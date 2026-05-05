import * as THREE from "three";

/**
 * LiDAR / photogrammetry meshes often mix vertex colors, sRGB baseColor maps, and aggressive PBR
 * metalness that reads as grey on mobile GL. Normalize color spaces and readability.
 */
export function fixScanRendering(root: THREE.Object3D, renderer: THREE.WebGLRenderer) {
	root.updateMatrixWorld(true);
	const maxAniso = Math.min(8, renderer.capabilities.getMaxAnisotropy?.() ?? 4);

	root.traverse((obj) => {
		if (!(obj instanceof THREE.Mesh)) {
			return;
		}
		const geom = obj.geometry as THREE.BufferGeometry;
		const hasVertexColor = !!geom.getAttribute("color");
		const mats = Array.isArray(obj.material) ? obj.material : [obj.material];

		for (const mat of mats) {
			if (mat instanceof THREE.MeshStandardMaterial) {
				if (hasVertexColor) {
					mat.vertexColors = true;
				}
				const colorMap = (t: THREE.Texture | null | undefined) => {
					if (!t) {
						return;
					}
					t.colorSpace = THREE.SRGBColorSpace;
					t.anisotropy = maxAniso;
				};
				colorMap(mat.map);
				colorMap(mat.emissiveMap);
				mat.metalness = Math.min(mat.metalness, 0.35);
				mat.roughness = THREE.MathUtils.clamp(mat.roughness + 0.12, 0.2, 1);
				mat.envMapIntensity = Math.min(mat.envMapIntensity || 1, 1);
				mat.needsUpdate = true;
			} else if (mat instanceof THREE.MeshBasicMaterial) {
				if (hasVertexColor) {
					mat.vertexColors = true;
				}
				if (mat.map) {
					mat.map.colorSpace = THREE.SRGBColorSpace;
					mat.map.anisotropy = maxAniso;
				}
				mat.needsUpdate = true;
			}
		}
	});
}
