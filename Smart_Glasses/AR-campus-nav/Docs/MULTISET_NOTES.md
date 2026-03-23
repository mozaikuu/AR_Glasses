# MultiSet Feasibility Notes

## Current evidence from local package files
- MultiSet package README lists iOS/Android setup and requirements.
- Package dependencies focus on ARCore/ARKit and AR Foundation mobile flow.
- `Runtime/Plugins/MultiSetSDK.dll.meta` has Windows Store Apps importer disabled in this installed package.

## Implication
- MultiSet may not be ready for UWP/HoloLens in your current installed version (`1.11.2`).
- Treat MultiSet on HoloLens as unconfirmed until vendor support explicitly confirms it.

## Action
- Contact MultiSet support with your exact target:
  - Device: HoloLens 2
  - Build target: UWP ARM64
  - Unity: 2022.3.62f1 or 6000.0.49f1
  - Need: campus localization + navigation SDK support on device

