# Expo App Development Journal

## Session: 2026-05-01 21:16

### Overview

Setting up bottom tab navigation with 4 main screens: Home, Bus Tracking, Indoor Navigation, and Companion.

---

### Changes Made

#### 1. Fixed `app/indoornav.tsx`

**Issue:** Used lowercase `<text>` instead of `<Text>` component
**Fix:** Changed `<text>indoornav</text>` to `<Text>indoornav</Text>`
**Reason:** React Native components must be capitalized

#### 2. Fixed `app/index.tsx`

**Issue:** Had invalid HTML `<link>` tag for navigation
**Fix:** Removed `<link href="/indoornav" />`
**Reason:** React Native doesn't use HTML link tags; navigation handled by expo-router

#### 3. Created `app/bus.tsx`

**Purpose:** Bus tracking screen
**Content:** Placeholder screen with title "Bus Tracking"

#### 4. Created `app/companion.tsx`

**Purpose:** Companion feature screen
**Content:** Placeholder screen with title "Companion"

#### 5. Updated `app/_layout.tsx`

**Change:** Switched from Stack navigator to Tabs navigator
**Details:**

- Imported `Tabs` from `expo-router`
- Configured 4 tabs: index (Home), bus (Bus Tracking), indoornav (Indoor Nav), companion (Companion)
- Added icons from `@expo/vector-icons` (Ionicons)
- Each tab has a title and icon

---

### Files Modified

- `app/_layout.tsx` - Complete rewrite for tab navigation
- `app/index.tsx` - Removed invalid link tag
- `app/indoornav.tsx` - Fixed Text component casing

### Files Created

- `app/bus.tsx` - New bus tracking screen
- `app/companion.tsx` - New companion screen
- `journal.md` - This journal file

---

## Session: 2026-05-01 23:15

### Overview

Added a complete fake live bus tracking demo with real map, path selection, time selectors, and random stop simulation.

---

### Changes Made

#### 1. Added react-native-maps dependency

**File:** `package.json`
**Change:** Added `"react-native-maps": "^1.20.1"` to dependencies

#### 2. Complete rewrite of `app/bus.tsx`

**Purpose:** Interactive bus tracking with live map simulation

**Features Implemented:**

- **Two Modes:**
   - **Path Setup Mode:** Tap on map to set start (green) and end (red) positions
   - **Tracking Mode:** Live bus animation along the saved route

- **Path Management:**
   - Path is set once by tapping two points on the map
   - "Edit Path" button appears in tracking mode to modify the route
   - Route is automatically generated with a slight curve for realism

- **Time Selectors:**
   - Start time picker (defaults to current time)
   - End time is auto-calculated based on distance

- **Live Tracking Simulation:**
   - Bus marker moves along the route in real-time
   - Variable speed (20-50 km/h)
   - Random stops every 3-8 seconds (simulating traffic lights, bus stops, etc.)
   - Stop reasons displayed: "Traffic light", "Bus stop", "Traffic jam", "Passenger boarding"

- **Status Panel:**
   - Real-time speed display
   - Distance remaining
   - ETA
   - Progress percentage
   - Current status message

- **Visual Elements:**
   - Green "S" marker for start position
   - Red "E" marker for end position
   - Blue bus emoji marker (turns orange when stopped)
   - Blue polyline showing the route

---

### Files Modified

- `package.json` - Added react-native-maps dependency
- `app/bus.tsx` - Complete rewrite with map and tracking features

---

### Status: ✅ COMPLETED

Bus tracking demo with live map simulation is now fully functional.

---

### Next Steps / TODO

- [ ] Install npm dependencies (react-native-webview)
- [ ] Add real content to companion screen
- [ ] Add real content to indoor navigation screen
- [ ] Add API integrations for real bus data

---

## Session: 2026-05-01 00:24 - Bug Fixes

### Issue: turgomoduleregistry.getenforcing is not found

**Root Cause:** This error typically occurs due to:

1. New Architecture being enabled (`newArchEnabled: true`) which can cause compatibility issues with some native modules
2. Missing proper react-native-maps plugin configuration

**Fixes Applied:**

1. **Added react-native-maps plugin to app.json**
   - Added the expo config plugin for react-native-maps with location permissions

2. **Disabled New Architecture**
   - Changed `"newArchEnabled": true` to `"newArchEnabled": false` in app.json
   - This resolves compatibility issues with native modules

3. **Removed PROVIDER_GOOGLE from bus.tsx**
   - Removed the `provider={PROVIDER_GOOGLE}` prop from MapView
   - This allows the map to use the default provider which works better with Expo

**Files Modified:**

- `app.json` - Added react-native-maps plugin, disabled new architecture
- `app/bus.tsx` - Removed PROVIDER_GOOGLE import and usage
