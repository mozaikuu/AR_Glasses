import { useCallback, useEffect, useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Asset } from "expo-asset";
import type { ExpoWebGLRenderingContext } from "expo-gl";
import { GLView } from "expo-gl";
import { Renderer } from "expo-three";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

function disposeObject3D(root: THREE.Object3D) {
	root.traverse((child: THREE.Object3D) => {
		if (!(child instanceof THREE.Mesh)) {
			return;
		}
		child.geometry.dispose();
		const mat = child.material;
		if (!mat) {
			return;
		}
		const list = Array.isArray(mat) ? mat : [mat];
		for (const m of list) {
			const anyMat = m as THREE.MeshStandardMaterial;
			anyMat.map?.dispose?.();
			anyMat.normalMap?.dispose?.();
			anyMat.roughnessMap?.dispose?.();
			anyMat.metalnessMap?.dispose?.();
			anyMat.aoMap?.dispose?.();
			anyMat.emissiveMap?.dispose?.();
			m.dispose();
		}
	});
}

export type GlbViewerProps = {
	/** Result of `require("…/model.glb")` */
	assetModule: number;
	/** Y-axis spin per animation frame (radians). */
	autoRotateYPerFrame?: number;
};

/**
 * Minimal GLB preview on Expo GL + three.js (via `expo-three`).
 * Prefer testing on a physical device; simulators often struggle with GL + large meshes.
 */
export function GlbViewer({ assetModule, autoRotateYPerFrame = 0.004 }: GlbViewerProps) {
	const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
	const [errorText, setErrorText] = useState("");
	const disposeRef = useRef<(() => void) | null>(null);

	useEffect(
		() => () => {
			disposeRef.current?.();
			disposeRef.current = null;
		},
		[assetModule],
	);

	const onContextCreate = useCallback(
		async (gl: ExpoWebGLRenderingContext) => {
			disposeRef.current?.();
			disposeRef.current = null;
			setStatus("loading");
			setErrorText("");

			let raf = 0;

			try {
				const [{ localUri, uri }] = await Asset.loadAsync(assetModule);
				const modelUri = localUri ?? uri;
				if (!modelUri) {
					throw new Error("Could not resolve GLB asset URI.");
				}

				const renderer = new Renderer({ gl }) as THREE.WebGLRenderer;
				renderer.outputColorSpace = THREE.SRGBColorSpace;
				renderer.toneMapping = THREE.ACESFilmicToneMapping;
				renderer.setPixelRatio(1);
				renderer.setSize(gl.drawingBufferWidth, gl.drawingBufferHeight);

				const scene = new THREE.Scene();
				scene.background = new THREE.Color(0x0f172a);

				const aspect = gl.drawingBufferWidth / Math.max(1, gl.drawingBufferHeight);
				const camera = new THREE.PerspectiveCamera(45, aspect, 0.01, 5000);

				scene.add(new THREE.AmbientLight(0xffffff, 0.55));
				const key = new THREE.DirectionalLight(0xffffff, 0.9);
				key.position.set(6, 10, 8);
				scene.add(key);
				const fill = new THREE.DirectionalLight(0xb4c6fc, 0.35);
				fill.position.set(-4, 2, -6);
				scene.add(fill);

				const gltf = await new Promise<THREE.Group>((resolve, reject) => {
					const loader = new GLTFLoader();
					loader.load(modelUri, (g) => resolve(g.scene), undefined, reject);
				});

				scene.add(gltf);

				const box = new THREE.Box3().setFromObject(gltf);
				const center = box.getCenter(new THREE.Vector3());
				const size = box.getSize(new THREE.Vector3());
				const maxDim = Math.max(size.x, size.y, size.z, 0.01);
				const dist = maxDim * 1.85;
				camera.position.set(center.x + dist * 0.55, center.y + dist * 0.28, center.z + dist * 0.55);
				camera.near = maxDim / 200;
				camera.far = maxDim * 200;
				camera.updateProjectionMatrix();
				camera.lookAt(center);

				const render = () => {
					gltf.rotation.y += autoRotateYPerFrame;
					renderer.render(scene, camera);
					gl.endFrameEXP();
					raf = requestAnimationFrame(render);
				};
				raf = requestAnimationFrame(render);

				disposeRef.current = () => {
					cancelAnimationFrame(raf);
					disposeObject3D(gltf);
					scene.remove(gltf);
					renderer.dispose();
				};

				setStatus("ready");
			} catch (e) {
				const msg = e instanceof Error ? e.message : String(e);
				setErrorText(msg);
				setStatus("error");
			}
		},
		[assetModule, autoRotateYPerFrame],
	);

	return (
		<View style={styles.wrap}>
			<GLView key={String(assetModule)} style={styles.gl} onContextCreate={onContextCreate} />
			{status !== "ready" && (
				<View style={styles.overlay} pointerEvents="none">
					<Text style={styles.overlayText}>{status === "loading" ? "Loading 3D model…" : `3D error: ${errorText}`}</Text>
				</View>
			)}
		</View>
	);
}

const styles = StyleSheet.create({
	wrap: {
		flex: 1,
		minHeight: 280,
		borderRadius: 12,
		overflow: "hidden",
		backgroundColor: "#0f172a",
	},
	gl: { flex: 1 },
	overlay: {
		...StyleSheet.absoluteFillObject,
		justifyContent: "center",
		alignItems: "center",
		backgroundColor: "rgba(15,23,42,0.55)",
		padding: 16,
	},
	overlayText: {
		color: "#e2e8f0",
		textAlign: "center",
		fontSize: 14,
	},
});
