"""
glb_to_floorplan.py
====================
Convert a textured GLB / 3D mesh file into a clean 2D floor-plan image.

Key improvement over the naive approach:
  - Filters to NEAR-VERTICAL faces only (|face_normal_y| < 0.3)
    → removes stairs, floors, ceilings that would bleed into the wall slice.
  - Cross-sections the wall mesh at a user-defined height (default 1.0 m).
  - Rasterises at configurable resolution (default 5 cm / pixel).
  - Exports both a raw wall map and a styled parchment-style floor plan PNG.

Dependencies:
    pip install trimesh numpy opencv-python-headless matplotlib scipy

Usage:
    python glb_to_floorplan.py --input model.glb --height 1.0 --resolution 0.05
"""

import argparse
import numpy as np
import cv2
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# ─────────────────────────────────────────────────────────────
# 1. Load & combine meshes
# ─────────────────────────────────────────────────────────────
def load_mesh(path: str) -> trimesh.Trimesh:
    """Load any 3D file trimesh supports and return a single combined mesh."""
    scene = trimesh.load(path)
    if isinstance(scene, trimesh.Scene):
        meshes = list(scene.geometry.values())
        combined = trimesh.util.concatenate(meshes)
    else:
        combined = scene
    print(f"Loaded: {len(combined.vertices):,} verts, {len(combined.faces):,} faces")
    print(f"Bounds: {combined.bounds}")
    return combined


# ─────────────────────────────────────────────────────────────
# 2. Filter to walls only (remove stairs / floors / ceilings)
# ─────────────────────────────────────────────────────────────
def extract_walls(mesh: trimesh.Trimesh, normal_y_threshold: float = 0.3) -> trimesh.Trimesh:
    """
    Keep only faces whose Y-component of the face normal is below threshold.
    Y is assumed to be the vertical axis (standard in most GLB exports).

    A purely vertical wall has normal_y == 0.
    Stairs / floors / ceilings have |normal_y| ≈ 1.
    """
    y_abs = np.abs(mesh.face_normals[:, 1])
    wall_mask = y_abs < normal_y_threshold
    wall_faces = mesh.faces[wall_mask]
    wall_mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=wall_faces, process=False)
    print(f"Wall faces: {wall_mask.sum():,} / {len(mesh.faces):,} "
          f"({wall_mask.mean()*100:.1f}%)")
    return wall_mesh


# ─────────────────────────────────────────────────────────────
# 3. Cross-section at given height → 2-D path
# ─────────────────────────────────────────────────────────────
def slice_at_height(mesh: trimesh.Trimesh, height: float = 1.0) -> trimesh.path.path.Path2D:
    """Return a 2-D planar path by cutting the mesh horizontally."""
    section = mesh.section(
        plane_origin=[0, height, 0],
        plane_normal=[0, 1, 0]
    )
    if section is None:
        raise ValueError(f"No cross-section found at Y={height}. "
                         "Try a different height within the model bounds.")
    path2d, _ = section.to_2D()
    print(f"Section at Y={height}: {len(path2d.entities)} contours")
    return path2d


# ─────────────────────────────────────────────────────────────
# 4. Rasterise path → numpy grid
# ─────────────────────────────────────────────────────────────
def rasterise(path2d, resolution: float = 0.05, pad: int = 10) -> np.ndarray:
    """
    Convert a 2-D trimesh path into a binary occupancy image.

    Parameters
    ----------
    path2d     : trimesh Path2D object
    resolution : metres per pixel
    pad        : border padding in pixels

    Returns
    -------
    grid : uint8 ndarray (H x W), 255 = wall, 0 = empty
    """
    bounds  = path2d.bounds
    min_xy  = bounds[0]
    max_xy  = bounds[1]
    W = int((max_xy[0] - min_xy[0]) / resolution) + 2 * pad
    H = int((max_xy[1] - min_xy[1]) / resolution) + 2 * pad
    grid = np.zeros((H, W), dtype=np.uint8)

    def w2g(x, y):
        return (int((x - min_xy[0]) / resolution) + pad,
                int((y - min_xy[1]) / resolution) + pad)

    for entity in path2d.entities:
        pts = path2d.vertices[entity.points]
        for i in range(len(pts) - 1):
            cv2.line(grid, w2g(*pts[i]), w2g(*pts[i + 1]), 255, 2)
        if getattr(entity, 'closed', False):
            cv2.line(grid, w2g(*pts[-1]), w2g(*pts[0]), 255, 2)

    # Thicken walls slightly
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    grid = cv2.dilate(grid, kernel, iterations=1)

    print(f"Grid: {W}×{H} px  ({W*resolution:.1f}m × {H*resolution:.1f}m)")
    return grid


# ─────────────────────────────────────────────────────────────
# 5. Style and save
# ─────────────────────────────────────────────────────────────
def save_floorplan(grid: np.ndarray, output_path: str, resolution: float = 0.05) -> None:
    """Render a styled parchment floor-plan PNG."""
    H, W = grid.shape
    styled = np.full((H, W, 3), [245, 240, 225], dtype=np.uint8)   # parchment bg
    styled[grid > 0] = [40, 35, 30]                                  # dark walls

    fig, axes = plt.subplots(1, 2, figsize=(18, 9), facecolor='#1a1a2e')
    for ax in axes:
        ax.set_facecolor('#0f0f1a')

    axes[0].imshow(np.flipud(grid), cmap='gray', interpolation='nearest')
    axes[0].set_title('Wall Cross-Section (walls only)', color='white', fontsize=12)
    axes[0].axis('off')

    axes[1].imshow(np.flipud(styled), interpolation='nearest')

    # Scale bar (5 m)
    scale_px = int(5.0 / resolution)
    bx, by = 20, H - 15
    axes[1].plot([bx, bx + scale_px], [by, by], color='#e74c3c', linewidth=3)
    axes[1].text(bx + scale_px // 2, by - 8, '5 m',
                 color='#e74c3c', ha='center', fontsize=9)
    axes[1].set_title('Styled Floor Plan', color='white', fontsize=12)
    axes[1].axis('off')

    plt.suptitle('2D Floor Plan from GLB Mesh', color='white', fontsize=14, y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"Saved → {output_path}")

    # Also save clean PNG for use in annotator
    clean_path = output_path.replace('.png', '_clean.png')
    cv2.imwrite(clean_path,
                cv2.cvtColor(np.flipud(styled), cv2.COLOR_RGB2BGR))
    print(f"Clean PNG → {clean_path}")


# ─────────────────────────────────────────────────────────────
# 6. Main
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="GLB → 2D Floor Plan")
    parser.add_argument('--input',      default='model.glb',
                        help='Path to .glb / .gltf / .obj / .ply file')
    parser.add_argument('--output',     default='floorplan.png',
                        help='Output PNG path')
    parser.add_argument('--height',     type=float, default=1.0,
                        help='Horizontal slice height in metres (default 1.0)')
    parser.add_argument('--resolution', type=float, default=0.05,
                        help='Metres per pixel (default 0.05 = 5 cm)')
    parser.add_argument('--normal_threshold', type=float, default=0.3,
                        help='Max |normal_y| to keep a face as a wall (default 0.3)')
    parser.add_argument('--try_heights', action='store_true',
                        help='Try multiple heights and save each slice')
    args = parser.parse_args()

    mesh = load_mesh(args.input)

    if args.try_heights:
        # Sweep heights to find the best slice
        y_min, y_max = mesh.bounds[0][1], mesh.bounds[1][1]
        for h in np.arange(y_min + 0.5, y_max - 0.5, 0.5):
            try:
                walls   = extract_walls(mesh, args.normal_threshold)
                path2d  = slice_at_height(walls, height=h)
                grid    = rasterise(path2d, args.resolution)
                out     = args.output.replace('.png', f'_h{h:.1f}.png')
                save_floorplan(grid, out, args.resolution)
            except Exception as e:
                print(f"  Skip h={h:.1f}: {e}")
        return

    walls  = extract_walls(mesh, args.normal_threshold)
    path2d = slice_at_height(walls, args.height)
    grid   = rasterise(path2d, args.resolution)
    save_floorplan(grid, args.output, args.resolution)


if __name__ == '__main__':
    main()