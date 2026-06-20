# CEREBRO Mobile

Android-first multimodal assistant with voice, camera analysis, and indoor navigation.

## Requirements

- Node.js 18+
- Android SDK (API 34) with a connected device or emulator
- Java 17+

## Install

```bash
npm install
```

## Run (Android)

```bash
npx react-native start
npx react-native run-android
```

## Type Check

```bash
npm run type-check
```

## Build APK

```bash
cd android
./gradlew assembleDebug
```

## Configuration

Open the Settings tab in the app to set the backend URL and optional API key.

Default backend URL: `http://127.0.0.1:8000`

---

Copyright © 2026 Ahmed Moussa

This software is provided to New Mansoura University solely for academic evaluation purposes.

No license, ownership rights, distribution rights, modification rights, or commercial rights are granted.

All intellectual property rights remain with the author.
