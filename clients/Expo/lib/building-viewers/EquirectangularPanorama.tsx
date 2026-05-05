import { useCallback, useEffect, useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import type { ExpoWebGLRenderingContext } from "expo-gl";
import { GLView } from "expo-gl";
import { Renderer } from "expo-three";
import * as THREE from "three";

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
			const anyMat = m as THREE.MeshBasicMaterial;
			anyMat.map?.dispose?.();
			m.dispose();
		}
	});
}

export type EquirectangularPanoramaProps = {
	/** File URI from a picker or `Asset.localUri`. */
	imageUri: string;
};

/**
 * Simple interior sphere with an equirectangular texture (360° photo).
 */
export function EquirectangularPanorama({ imageUri }: EquirectangularPanoramaProps) {
	const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
	const [errorText, setErrorText] = useState("");
	const disposeRef = useRef<(() => void) | null>(null);

	useEffect(
		() => () => {
			disposeRef.current?.();
			disposeRef.current = null;
		},
		[imageUri],
	);

	const onContextCreate = useCallback(
		async (gl: ExpoWebGLRenderingContext) => {
			disposeRef.current?.();
			disposeRef.current = null;
			setStatus("loading");
			setErrorText("");

			let raf = 0;

			try {
				const renderer = new Renderer({ gl }) as THREE.WebGLRenderer;
				renderer.outputColorSpace = THREE.SRGBColorSpace;
				renderer.setPixelRatio(1);
				renderer.setSize(gl.drawingBufferWidth, gl.drawingBufferHeight);

				const scene = new THREE.Scene();
				const aspect = gl.drawingBufferWidth / Math.max(1, gl.drawingBufferHeight);
				const camera = new THREE.PerspectiveCamera(70, aspect, 0.1, 2000);
				camera.position.set(0, 0, 0);

				const texture = await new Promise<THREE.Texture>((resolve, reject) => {
					const loader = new THREE.TextureLoader();
					loader.load(
						imageUri,
						(t: THREE.Texture) => {
							t.colorSpace = THREE.SRGBColorSpace;
							t.anisotropy = 4;
							resolve(t);
						},
						undefined,
						reject,
					);
				});

				const geo = new THREE.SphereGeometry(500, 48, 32);
				geo.scale(-1, 1, 1);
				const mat = new THREE.MeshBasicMaterial({ map: texture });
				const mesh = new THREE.Mesh(geo, mat);
				scene.add(mesh);

				let yaw = 0;
				const render = () => {
					yaw += 0.0015;
					mesh.rotation.y = yaw;
					renderer.render(scene, camera);
					gl.endFrameEXP();
					raf = requestAnimationFrame(render);
				};
				raf = requestAnimationFrame(render);

				disposeRef.current = () => {
					cancelAnimationFrame(raf);
					disposeObject3D(mesh);
					scene.remove(mesh);
					texture.dispose();
					renderer.dispose();
				};

				setStatus("ready");
			} catch (e) {
				const msg = e instanceof Error ? e.message : String(e);
				setErrorText(msg);
				setStatus("error");
			}
		},
		[imageUri],
	);

	return (
		<View style={styles.wrap}>
			<GLView key={imageUri} style={styles.gl} onContextCreate={onContextCreate} />
			{status !== "ready" && (
				<View style={styles.overlay} pointerEvents="none">
					<Text style={styles.overlayText}>
						{status === "loading" ? "Loading panorama…" : `Panorama error: ${errorText}`}
					</Text>
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
		backgroundColor: "#020617",
	},
	gl: { flex: 1 },
	overlay: {
		...StyleSheet.absoluteFillObject,
		justifyContent: "center",
		alignItems: "center",
		backgroundColor: "rgba(2,6,23,0.55)",
		padding: 16,
	},
	overlayText: {
		color: "#e2e8f0",
		textAlign: "center",
		fontSize: 14,
	},
});
