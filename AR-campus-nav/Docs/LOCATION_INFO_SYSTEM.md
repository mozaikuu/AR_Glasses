# Location Info Popup System

**Created:** March 17, 2026
**Purpose:** Proximity-based popup system for displaying location information in AR
**Replaces:** QR code-based location info system

---

## Overview

This system displays information about locations (TA offices, lecture halls, labs, etc.) when the user gets close to them. It uses Unity trigger colliders for proximity detection and MRTK-based UI for the popup display.

## Architecture

```
User approaches location
        ↓
LocationTrigger (SphereCollider)
        ↓
OnTriggerEnter detected
        ↓
LocationDataManager provides data
        ↓
LocationInfoPopup instantiated
        ↓
Dynamic UI populated based on type
```

## Components

### 1. LocationDataManager (Singleton)
- Loads `navigation.json` at startup
- Provides fast lookup by location ID
- Caches all location data in memory

### 2. LocationTrigger
- SphereCollider trigger for proximity
- Configurable radius per location
- Events: OnPlayerEntered, OnPlayerExited
- Optional: require facing location

### 3. LocationInfoPopup
- MRTK-compatible UI
- Dynamic content based on PlaceType
- Billboard mode (always face user)
- Auto-hide options

### 4. LocationDataModels
- Serializable classes matching JSON
- StaffMember, Lecture, LocationData
- Helper methods for data access

## Setup Instructions

### Step 1: Import navigation.json

1. Copy `navigation.json` to `Assets/Resources/Data/`
2. In Unity, select the file
3. In Inspector, verify it's a TextAsset

### Step 2: Create LocationDataManager

1. Create empty GameObject: `LocationDataManager`
2. Add `LocationDataManager` component
3. Assign `navigation.json` to the field
4. Check "Load On Awake"

### Step 3: Create Popup Prefab

1. Create Canvas (World Space)
2. Add MRTK components:
   - `NearInteractionGrabbable` (optional)
   - `CanvasUtility`
   - `GraphicRaycaster`
3. Add UI elements:
   - Title (TextMeshPro)
   - Subtitle (TextMeshPro)
   - Content (TextMeshPro)
   - StaffContainer (for cards)
   - LecturesContainer (for cards)
4. Add `LocationInfoPopup` script
5. Assign UI references
6. Create prefab: `Prefabs/UI/LocationInfoPopup.prefab`

### Step 4: Create Trigger Prefab

1. Create empty GameObject: `LocationTrigger`
2. Add SphereCollider (isTrigger = true)
3. Add `LocationTrigger` script
4. Configure:
   - Assign popup prefab
   - Set popup offset (e.g., 0, 1.5, 0)
5. Create prefab: `Prefabs/LocationTrigger.prefab`

### Step 5: Setup Scene

Option A: Manual Setup
```
1. Create empty GameObject: "LocationTriggers"
2. For each location in navigation.json:
   - Instantiate trigger prefab
   - Set position from coordinates
   - Set locationId from JSON
   - Parent to "LocationTriggers"
```

Option B: Use LocationInfoSetup
```
1. Create empty GameObject: "LocationInfoSetup"
2. Add `LocationInfoSetup` component
3. Assign navigation.json
4. Assign trigger prefab
5. Assign popup prefab
6. Right-click → "Setup: Create Location Triggers"
```

### Step 6: Configure MultiSet (Optional)

1. Add `LocalizationWrapper` to scene
2. Reference `OnDeviceLocalizationManager` (from MultiSet SDK)
3. Set map code
4. Configure offsets if needed

## Data Format

The system reads from `navigation.json`:

```json
{
  "building": {
    "name": "Smart Building",
    "address": "123 Tech Street"
  },
  "locations": [
    {
      "id": "ta_office_1",
      "name": "CS Department TA Office",
      "floor": 2,
      "coordinates": { "x": 3, "y": 5 },
      "description": "Computer Science TA Office",
      "placeType": "Office",
      "proximityRadius": 2.0,
      "staff": [
        {
          "name": "Ahmed Hassan",
          "role": "Teaching Assistant",
          "email": "ahmed@university.edu",
          "officeDays": ["Sunday", "Monday", "Tuesday", "Wednesday"],
          "officeHours": "9:00 AM - 2:00 PM"
        }
      ]
    },
    {
      "id": "lecture_hall_a",
      "name": "Lecture Hall A",
      "floor": 1,
      "coordinates": { "x": 10, "y": 0 },
      "description": "Main lecture hall",
      "placeType": "LectureRoom",
      "proximityRadius": 3.0,
      "lectures": [
        {
          "courseName": "Data Structures",
          "courseCode": "CS201",
          "instructor": "Dr. Mahmoud",
          "day": "Sunday",
          "startTime": "9:00 AM",
          "endTime": "10:30 AM"
        }
      ]
    }
  ]
}
```

## Popup Types

### TA Office Popup
- Shows staff list
- Each staff card displays:
  - Name
  - Role
  - Email
  - Office days
  - Office hours

### Lecture Hall Popup
- Shows today's lectures
- Each lecture card displays:
  - Course name
  - Course code
  - Instructor
  - Time slot
- If no lectures today, shows weekly schedule

### Generic Location Popup
- Shows description
- Shows additional info

## Customization

### Change Trigger Radius
```csharp
// In LocationTrigger or navigation.json
proximityRadius = 3.0f; // meters
```

### Change Popup Position
```csharp
// In LocationTrigger
popupOffset = new Vector3(0, 2.0f, 0); // 2 meters up
```

### Require Facing Location
```csharp
// In LocationTrigger
requireFacing = true;
facingAngleThreshold = 60f; // degrees
```

### Auto-hide Popup
```csharp
// In LocationInfoPopup
hideAfterSeconds = 10f; // auto-hide after 10 seconds
```

## Integration with Navigation

The LocationInfo system works independently of the Navigation system:

- `NavigationManager` - Pathfinding and movement
- `LocationTrigger` - Proximity detection
- `LocationInfoPopup` - Information display

They can be used together:
```csharp
// When user arrives at destination
navigationManager.OnNavigationCompleted += () => {
    // Show location info
    locationTrigger.TestShowPopup();
};
```

## Testing

### In Editor
1. Set `simulateInEditor = true` in LocalizationWrapper
2. Set simulated position near a location
3. Enter Play mode
4. Walk towards trigger (use scene view)

### On Device
1. Build and deploy to HoloLens
2. Ensure MultiSet localization is working
3. Walk near locations
4. Popups should appear automatically

## Debugging

Enable debug mode in components:
- `LocationDataManager.debugMode` - Log loaded locations
- `LocationTrigger` - Gizmos show trigger radius
- `LocalizationWrapper.debugMode` - Draw position rays

## Migration from QR System

| Old (QR) | New (Proximity) |
|----------|-----------------|
| User scans QR code | User walks near location |
| HoloLensQrTracker | LocationTrigger |
| QrModalController | LocationInfoPopup |
| Backend API call | Local JSON data |
| QR code placement | Trigger collider placement |

## Future Enhancements

- [ ] Voice commands to show/hide popups
- [ ] Persistent popups (pin to world)
- [ ] Multiple popups (compare locations)
- [ ] Floor filtering (only show current floor)
- [ ] Search functionality
- [ ] Favorite locations

---

*Document version: 1.0*
