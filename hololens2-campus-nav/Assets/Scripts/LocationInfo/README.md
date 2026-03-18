# LocationInfo System for Unity AR Navigation

## Overview

The LocationInfo system provides proximity-based popup menus that display information about locations in your university. When the user approaches a location (TA office, lecture hall, lab, etc.), a popup automatically appears showing relevant information.

## Features

- **Proximity Detection**: Automatic popup when user enters trigger area
- **Rich Location Data**: Staff info, office hours, lecture schedules
- **MRTK Compatible**: Designed for HoloLens with proper spatial UI
- **Dynamic Content**: Different layouts for different location types
- **Billboard Mode**: Popups always face the user
- **Configurable**: Per-location trigger radius and behavior

## Architecture

```
LocationInfoSystem/
├── LocationDataModels.cs      # Data structures (LocationData, StaffMember, Lecture)
├── LocationDataManager.cs     # Singleton - loads navigation.json
├── LocationTrigger.cs          # Proximity trigger component
├── LocationInfoPopup.cs        # UI controller for popup
└── LocationInfoSetup.cs        # Helper for scene setup
```

## Quick Start

### 1. Import navigation.json

1. Copy `navigation.json` from project root to `Assets/Resources/Data/`
2. In Unity: Right-click → Import New Asset → Select navigation.json
3. Set as TextAsset

### 2. Create LocationDataManager

1. Create empty GameObject: `GameObject` → `Create Empty`
2. Name it "LocationDataManager"
3. Add `LocationDataManager` component
4. Assign navigation.json to the "Navigation Json" field

### 3. Create Popup Prefab

1. Create Canvas: `UI` → `Canvas`
   - Render Mode: World Space
   - Scale: 0.001, 0.001, 0.001 (for meters)

2. Add UI elements:
   - Title (TextMeshPro)
   - Subtitle (TextMeshPro)
   - Content (TextMeshPro with ScrollRect)
   - Close button

3. Add `LocationInfoPopup` component
4. Assign UI references
5. Drag to Project window to create prefab

### 4. Create Location Trigger Prefab

1. Create empty GameObject
2. Add `SphereCollider`:
   - Is Trigger: ✓
   - Radius: 2
3. Add `LocationTrigger` component
4. Drag popup prefab to "Popup Prefab" field
5. Save as prefab

### 5. Setup Scene

1. Create empty GameObject "LocationInfoSetup"
2. Add `LocationInfoSetup` component
3. Assign:
   - Navigation JSON
   - Location Trigger Prefab
   - Popup Prefab
4. Right-click component → "Setup: Create Location Triggers"

## Location Types

### TA Office

**Displays:**
- Staff member cards
- Name, role, email
- Office days and hours

**Data from:** `staff` array in navigation.json

### Lecture Hall

**Displays:**
- Today's lectures
- Course name, code, instructor
- Start/end times
- Weekly schedule (if no lectures today)

**Data from:** `lectures` array in navigation.json

### Generic Location

**Displays:**
- Description
- Additional info

## Configuration

### LocationTrigger Options

| Option | Description |
|--------|-------------|
| `locationId` | ID from navigation.json |
| `overrideRadius` | Use custom radius instead of JSON value |
| `customRadius` | Trigger radius in meters |
| `popupOffset` | Where to show popup relative to trigger |
| `autoHideOnExit` | Hide popup when leaving area |
| `showDelay` | Delay before showing (seconds) |
| `requireFacing` | Only show if user faces location |

### LocationInfoPopup Options

| Option | Description |
|--------|-------------|
| `billboardMode` | Always face user camera |
| `followUser` | Popup follows user position |
| `followDistance` | Distance from user (if following) |
| `hideAfterSeconds` | Auto-hide timeout (0 = never) |

## MultiSet Integration

The system uses MultiSet SDK for localization:

1. Add `OnDeviceLocalizationManager` to scene (from MultiSet SDK)
2. Reference it in `LocalizationWrapper`
3. Set your map code
4. Call `RequestLocalization()` on start

The `LocalizationWrapper` provides user position to the navigation system.

## Testing in Editor

1. Set `simulateInEditor = true` in LocalizationWrapper
2. Set `simulatedPosition` to test different locations
3. Use WASD to move around in Scene view
4. Triggers will fire based on simulated position

## Debugging

Enable `debugMode` on components to see:
- Trigger radius gizmos (cyan spheres)
- Popup position gizmos (yellow)
- Console logs for trigger events

## Events

### LocationTrigger Events

```csharp
LocationTrigger trigger = GetComponent<LocationTrigger>();

trigger.OnPlayerEntered += (locationData) => {
    Debug.Log($"Entered: {locationData.name}");
};

trigger.OnPopupShown += (locationData) => {
    // Custom logic when popup shows
};
```

### LocationInfoPopup Events

```csharp
LocationInfoPopup popup = GetComponent<LocationInfoPopup>();

popup.OnShow += () => { /* Popup opened */ };
popup.OnHide += () => { /* Popup closed */ };
```

## Customization

### Custom Staff Card

1. Create UI prefab with TextMeshPro components:
   - Name
   - Role
   - Email
   - Hours

2. Assign to `LocationInfoPopup.staffCardPrefab`

### Custom Lecture Card

1. Create UI prefab with TextMeshPro components:
   - CourseName
   - CourseCode
   - Instructor
   - Time

2. Assign to `LocationInfoPopup.lectureCardPrefab`

## Troubleshooting

### Popup not showing

- Check trigger radius covers player
- Verify locationId matches navigation.json
- Ensure LocationDataManager loaded successfully
- Check console for errors

### Wrong location data

- Verify navigation.json is imported as TextAsset
- Check locationId matches exactly (case-sensitive)
- Enable debugMode to see loaded locations

### Popup position wrong

- Adjust `popupOffset` in LocationTrigger
- Check Canvas render mode is World Space
- Verify scale is appropriate for meters

## Migration from QR System

If migrating from QR-based popups:

1. Remove `HoloLensQrTracker` components
2. Remove `QrModalController` components
3. Add `LocationTrigger` to location GameObjects
4. Configure trigger radius
5. Test proximity detection

No changes needed to navigation.json - same data format.

## Future Enhancements

- [ ] Floor detection and filtering
- [ ] Multiple simultaneous popups
- [ ] Voice announcements
- [ ] Haptic feedback
- [ ] Accessibility options

---

*Part of Cerebro Smart Glasses Project*
