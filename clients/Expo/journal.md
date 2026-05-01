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

### Status: ✅ COMPLETED

All tasks completed successfully. The app now has a fully functional bottom tab navigation with 4 screens.

---

### Next Steps / TODO

- [ ] Add real content to bus tracking screen
- [ ] Add real content to companion screen
- [ ] Add real content to indoor navigation screen
- [ ] Style the tab bar further (colors, badges, etc.)
- [ ] Add API integrations
