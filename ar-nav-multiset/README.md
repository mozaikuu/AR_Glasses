# AR Nav MultiSet

An AR navigation sample project using the [MultiSet.ai](https://multiset.ai) framework.

This is part of a community project lead by [Joshua Drewlow](https://www.youtube.com/@joshuadrewlow), creating example projects with various AR frameworks.

Tutorial for this project on YouTube: https://youtu.be/NISY0aQjakE

## Getting started

Requirements:

- Unity 6000.x

1. Clone/fork this repo
2. Open the project with Unity
3. Open Scene: Assets/Multiset/Scenes/Localization.unity
4. Play ((note: the SDK has no simulator yet, so you won't be able to move around with the camera))
5. Select DemoController GameObject > AgentDemoWalk > isLocalized -> true (simulates as if SDK found position)
6. Enjoy the magic of Unitys [NavMesh](https://docs.unity3d.com/Packages/com.unity.ai.navigation@2.0/manual/NavInnerWorkings.html) system
7. If you want to see the mesh of the map (a special shader is attached for [occlusion](https://docs.multiset.ai/unity-sdk/occlusion)): disable the OcclusionHelper script on N317_bfh child TexturedMesh.obj before playing the scene

## Localise with your map

1. Rename the file MultiSet Configuration file (contains auth key for your developer account): Assets/MultiSet/Resources/MultiSetConfig_CHANGE_ME.asset to Assets/MultiSet/Resources/MultiSetConfig.asset
2. Select GameObject MultiSetSdkManager
3. In MultiSetSdkManager component click "Open MultiSet Configuration"
4. Enter Client Id and Client Secret from [Credentials](https://developer.multiset.ai/credentials) in your developer account
5. Create Map with [iOS App](https://apps.apple.com/us/app/multiset/id6737130008)
6. Download map
7. Add to Unity
8. Update map id from [Maps](https://developer.multiset.ai/maps): GameObject MultiSetSdkManager > MapLocalizationManager > MapOrMapSetId
9. Rebake NavMesh
10. Update obstacles, agent settings, occlusion etc.
11. Disable/remove my sample Map
12. Build & Test

## MultiSet Documentation

[docs.multiset.ai](https://docs.multiset.ai/)

## Changelog

| Version | Date       | Changes                                                        |
| ------- | ---------- | -------------------------------------------------------------- |
| 0.4     | 23.01.2025 | - replaced map with Medinf lab<br />- updated NavMesh and POIs |
| 0.3     | 21.01.2025 | - added navigation scripts<br />- added navigation UI          |
| 0.2     | 24.12.2024 | - added MapSet consisting of 3 Maps                            |
| 0.1     | 08.12.2024 | - basic navmesh example                                        |
