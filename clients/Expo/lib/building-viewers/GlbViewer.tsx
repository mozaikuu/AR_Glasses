import type { MutableRefObject } from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Asset } from "expo-asset";
import type { ExpoWebGLRenderingContext } from "expo-gl";
import { GLView } from "expo-gl";
import { Renderer } from "expo-three";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

import { fixScanRendering } from "./gltfMaterials";
import {
	embedGlbBufferViewTexturesAsCacheFiles,
	fetchGlbArrayBuffer,
	shouldRewriteGlbTexturesForPlatform,
} from "./prepareGlbForRnTextures";
import { createWalkInputState, GlbWalkHud, type WalkInputState } from "./GlbWalkHud";

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
	/** Y-axis spin per animation frame (radians); orbit mode only. */
	autoRotateYPerFrame?: number;
	/** Orbit camera outside the model, or first-person walk inside the scan bounds. */
	interactionMode?: "orbit" | "walk";
};

function placeWalkCamera(
	camera: THREE.PerspectiveCamera,
	box: THREE.Box3,
	target: { yaw: number; pitch: number },
) {
	const center = box.getCenter(new THREE.Vector3());
	const size = box.getSize(new THREE.Vector3());
	const floorY = box.min.y;
	const eye = THREE.MathUtils.clamp(size.y * 0.08, 1.35, 2.05);
	camera.position.set(center.x, floorY + eye, center.z);

	const look = new THREE.Vector3();
	if (size.x >= size.z) {
		look.set(0, 0, 1);
	} else {
		look.set(1, 0, 0);
	}
	const lookTarget = center.clone().add(look.multiplyScalar(Math.min(size.x, size.z) * 0.25));
	camera.lookAt(lookTarget);
	camera.rotation.order = "YXZ";
	target.yaw = camera.rotation.y;
	target.pitch = camera.rotation.x;
}

/**
 * GLB preview on Expo GL + three.js. Orbit mode rotates the model; walk mode keeps the scan fixed
 * and moves a first-person camera inside the bounding box (auto-placed / Recenter).
 */
export function GlbViewer({
	assetModule,
	autoRotateYPerFrame = 0.004,
	interactionMode = "orbit",
}: GlbViewerProps) {
	const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
	const [errorText, setErrorText] = useState("");
	const disposeRef = useRef<(() => void) | null>(null);
	const walkInputRef = useRef<WalkInputState>(createWalkInputState());
	const recenterRef = useRef<(() => void) | null>(null);

	useEffect(
		() => () => {
			disposeRef.current?.();
			disposeRef.current = null;
			recenterRef.current = null;
		},
		[assetModule, interactionMode],
	);

	const onContextCreate = useCallback(
		async (gl: ExpoWebGLRenderingContext) => {
			disposeRef.current?.();
			disposeRef.current = null;
			recenterRef.current = null;
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
				renderer.toneMappingExposure = interactionMode === "walk" ? 1.22 : 1.05;
				renderer.setPixelRatio(1);
				renderer.setSize(gl.drawingBufferWidth, gl.drawingBufferHeight);

				const scene = new THREE.Scene();
				scene.background = new THREE.Color(0x0f172a);

				const aspect = gl.drawingBufferWidth / Math.max(1, gl.drawingBufferHeight);
				const camera = new THREE.PerspectiveCamera(45, aspect, 0.01, 5000);

				scene.add(new THREE.AmbientLight(0xffffff, interactionMode === "walk" ? 0.72 : 0.55));
				const key = new THREE.DirectionalLight(0xffffff, interactionMode === "walk" ? 0.55 : 0.9);
				key.position.set(6, 10, 8);
				scene.add(key);
				const fill = new THREE.DirectionalLight(0xb4c6fc, interactionMode === "walk" ? 0.45 : 0.35);
				fill.position.set(-4, 2, -6);
				scene.add(fill);

				const loader = new GLTFLoader();
				const gltf = await new Promise<THREE.Group>((resolve, reject) => {
					const onParsed = (g: { scene: THREE.Group }) => resolve(g.scene);

					if (shouldRewriteGlbTexturesForPlatform()) {
						fetchGlbArrayBuffer(modelUri)
							.then(embedGlbBufferViewTexturesAsCacheFiles)
							.then((patched) => {
								const path = THREE.LoaderUtils.extractUrlBase(modelUri);
								loader.parse(patched, path, onParsed, reject);
							})
							.catch(reject);
					} else {
						loader.load(modelUri, onParsed, undefined, reject);
					}
				});

				scene.add(gltf);
				fixScanRendering(gltf, renderer);

				const box = new THREE.Box3().setFromObject(gltf);
				const size = box.getSize(new THREE.Vector3());
				const maxDim = Math.max(size.x, size.y, size.z, 0.01);
				camera.near = maxDim / 200;
				camera.far = maxDim * 200;

				const euler = { yaw: 0, pitch: 0 };
				if (interactionMode === "walk") {
					placeWalkCamera(camera, box, euler);
					recenterRef.current = () => {
						placeWalkCamera(camera, box, euler);
					};
				} else {
					const center = box.getCenter(new THREE.Vector3());
					const dist = maxDim * 1.85;
					camera.position.set(center.x + dist * 0.55, center.y + dist * 0.28, center.z + dist * 0.55);
					camera.updateProjectionMatrix();
					camera.lookAt(center);
				}

				const forward = new THREE.Vector3();
				const right = new THREE.Vector3();
				const tmp = new THREE.Vector3();
				let last = performance.now();

				const render = () => {
					const now = performance.now();
					const dt = Math.min(0.05, (now - last) / 1000);
					last = now;

					if (interactionMode === "orbit") {
						gltf.rotation.y += autoRotateYPerFrame;
					} else {
						const inp = walkInputRef.current;
						const lookSens = 0.0028;
						euler.yaw -= inp.lookDx * lookSens;
						euler.pitch -= inp.lookDy * lookSens;
						inp.lookDx = 0;
						inp.lookDy = 0;
						euler.pitch = THREE.MathUtils.clamp(euler.pitch, -Math.PI / 2 + 0.12, Math.PI / 2 - 0.12);
						camera.rotation.order = "YXZ";
						camera.rotation.y = euler.yaw;
						camera.rotation.x = euler.pitch;

						camera.getWorldDirection(forward);
						forward.y = 0;
						if (forward.lengthSq() < 1e-8) {
							forward.set(0, 0, -1).applyQuaternion(camera.quaternion);
							forward.y = 0;
						}
						forward.normalize();
						right.crossVectors(forward, tmp.set(0, 1, 0)).normalize();

						const speed = maxDim * 0.35;
						camera.position.addScaledVector(forward, inp.moveForward * speed * dt);
						camera.position.addScaledVector(right, inp.moveStrafe * speed * dt);

						const pad = maxDim * 0.02;
						camera.position.x = THREE.MathUtils.clamp(camera.position.x, box.min.x - pad, box.max.x + pad);
						camera.position.y = THREE.MathUtils.clamp(camera.position.y, box.min.y + 0.25, box.max.y + pad);
						camera.position.z = THREE.MathUtils.clamp(camera.position.z, box.min.z - pad, box.max.z + pad);
					}

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
		[assetModule, autoRotateYPerFrame, interactionMode],
	);

	return (
		<View style={styles.wrap}>
			<GLView key={`${assetModule}-${interactionMode}`} style={styles.gl} onContextCreate={onContextCreate} />
			{interactionMode === "walk" && status === "ready" && (
				<GlbWalkHud
					inputRef={walkInputRef as MutableRefObject<WalkInputState>}
					onRecenter={() => recenterRef.current?.()}
				/>
			)}
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
