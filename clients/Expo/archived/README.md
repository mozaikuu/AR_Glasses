# Archived Expo experiments

These folders preserve **temporary / non-production** features that were removed from the main tab bar to make room for the **Indoor Navigation MVP**.

They are **not** registered in Expo Router, so they do not appear as routes. To restore a feature:

1. Copy the screen file back under `app/main/` (e.g. `lidar.tsx`).
2. Re-add a `Tabs.Screen` entry in `app/main/_layout.tsx`.
3. Run `npx tsc --noEmit` in `clients/Expo`.

## Contents

| Folder             | Description                                                  |
| ------------------ | ------------------------------------------------------------ |
| `lidar-scan/`      | GLB LiDAR walk-through viewer (uses `lib/building-viewers`). |
| `3d-viewer/`       | Same GLB in orbit-style preview.                             |
| `panorama-viewer/` | Equirectangular panorama picker + GL viewer.                 |

Shared implementation remains in `clients/Expo/lib/building-viewers/` and related assets under `clients/Expo/assets/lidar/`.

---

Copyright © 2026 Ahmed Moussa

This software is provided to New Mansoura University solely for academic evaluation purposes.

No license, ownership rights, distribution rights, modification rights, or commercial rights are granted.

All intellectual property rights remain with the author.
