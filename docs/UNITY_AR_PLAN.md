# Unity AR Navigation - Proximity Popup System Plan

**Date:** March 17, 2026
**Branch:** Everything-refixed
**Goal:** Replace QR-based location info with proximity-based popup menus using MultiSet localization

---

## Current State Analysis

### Existing Unity Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `NavigationManager.cs` | Main navigation controller, NavMesh pathfinding | ✅ Working |
| `PathRenderer.cs` | LineRenderer path visualization | ✅ Working |
| `VoiceGuide.cs` | Turn-by-turn voice instructions | ✅ Working |
| `LocalizationWrapper.cs` | MultiSet SDK wrapper (placeholder) | ⚠️ Needs implementation |
| `QrModalController.cs` | QR-triggered popup modal | ❌ Will be replaced |
| `HoloLensQrTracker.cs` | QR code tracking (commented out) | ❌ Will be removed |
| `BackendApiClient.cs` | API client for QR endpoints | ❌ Will be refactored |

### Data Source: `navigation.json`

The navigation.json contains rich location data:
- **TA Offices**: Staff info (name, role, email, office days, hours)
- **Lecture Halls**: Scheduled lectures (course name, code, instructor, day, time)
- **Labs**: Equipment info, access requirements
- **General locations**: Description, floor, coordinates

### MultiSet SDK Integration

- MultiSet SDK is in `Assets/MultiSet/`
- Sample scenes available in `Assets/Samples/MultiSet-SDK/1.11.2/`
- `OnDeviceLocalization` sample is the reference implementation
- `LocalizationWrapper.cs` is a placeholder that needs actual MultiSet integration

---

## Plan: Proximity-Based Popup System

### Phase 1: Cleanup & Deprecation (Day 1)

#### 1.1 Move to Depricated/
```
Depricated/
├── ar_pipeline/              # Old AR pipeline (replaced by Unity)
├── audio_recorder_component/ # Replaced by WebRTC
├── old/                      # Old Python server/client
├── Smart_Gllasses/           # Empty/tools folder
├── web_app/                  # Replaced by Streamlit
├── mobile/                   # Flutter (if not using)
├── qr_code_system/           # QR-related code (moved from tools/)
└── hololens_qr_scripts/      # HoloLens QR scripts
```

#### 1.2 Remove QR Code System
- Move `tools/qr_generator.py` to Depricated/
- Comment out/remove QR-related code in `LocalizationWrapper.cs`
- Remove/deprecate `HoloLensQrTracker.cs`
- Refactor `QrModalController.cs` → `LocationInfoPopup.cs`
- Update `BackendApiClient.cs` to fetch location data instead of QR data

### Phase 2: MultiSet Localization Integration (Day 1-2)

#### 2.1 Study MultiSet SDK
- Review `OnDeviceRuntimeDemo.cs` sample
- Understand coordinate system mapping
- Learn how to get user position from MultiSet

#### 2.2 Implement LocalizationWrapper
```csharp
public class LocalizationWrapper : MonoBehaviour
{
    // Integrate with MultiSet SDK
    // Remove QR fallback
    // Provide: GetUserPosition(), IsLocalized events
}
```

#### 2.3 Map MultiSet Coordinates to Unity World
- Create coordinate mapping system
- Align MultiSet's coordinate system with Unity NavMesh
- Test localization accuracy

### Phase 3: Proximity Detection System (Day 2-3)

#### 3.1 Create LocationTrigger System

```csharp
// LocationTrigger.cs - Attach to each location GameObject
public class LocationTrigger : MonoBehaviour
{
    [Header("Location Data")]
    public string locationId;  // Matches navigation.json ID
    public float triggerRadius = 2.0f;
    public PlaceType placeType;

    [Header("UI")]
    public LocationInfoPopup popupPrefab;

    // Sphere trigger for proximity detection
    // OnTriggerEnter: Show popup
    // OnTriggerExit: Hide popup
}
```

#### 3.2 Create LocationInfoPopup UI

```csharp
// LocationInfoPopup.cs - MRTK-based popup
public class LocationInfoPopup : MonoBehaviour
{
    // MRTK UI components:
    // - Title (location name)
    // - Scrollable content area
    // - Close button
    // - Follow user gaze or world-locked

    public void Show(LocationData data);
    public void Hide();
    public void PopulateTAOffice(TAOfficeData data);
    public void PopulateLectureHall(LectureHallData data);
    public void PopulateLab(LabData data);
}
```

#### 3.3 Data Models

```csharp
// LocationData.cs
[System.Serializable]
public class LocationData
{
    public string id;
    public string name;
    public string description;
    public int floor;
    public PlaceType placeType;
    public StaffMember[] staff;        // For TA offices
    public Lecture[] lectures;         // For lecture halls
    public string additionalInfo;
}

[System.Serializable]
public class StaffMember
{
    public string name;
    public string role;
    public string email;
    public string[] officeDays;
    public string officeHours;
}

[System.Serializable]
public class Lecture
{
    public string courseName;
    public string courseCode;
    public string instructor;
    public string day;
    public string startTime;
    public string endTime;
}
```

### Phase 4: Data Loading & Management (Day 3)

#### 4.1 Create LocationDataManager

```csharp
// LocationDataManager.cs - Singleton
public class LocationDataManager : MonoBehaviour
{
    [SerializeField] private TextAsset navigationJson;
    private Dictionary<string, LocationData> locationDatabase;

    void Awake()
    {
        // Load navigation.json
        // Parse into LocationData objects
        // Index by ID for fast lookup
    }

    public LocationData GetLocation(string id);
    public LocationData[] GetAllLocations();
    public LocationData[] GetLocationsByFloor(int floor);
}
```

#### 4.2 JSON Parsing
- Import `navigation.json` into Unity as TextAsset
- Use JsonUtility or Newtonsoft.Json for parsing
- Handle type conversions (PlaceType enum)

### Phase 5: UI Implementation (Day 3-4)

#### 5.1 MRTK UI Setup
- Create popup prefab with MRTK components
- NearInteractionGrabbable for moving popup
- Scrollable content for long lists
- Backplate for visual separation

#### 5.2 Dynamic Content Layout

**TA Office Popup:**
```
┌─────────────────────────────┐
│  CS Department TA Office    │  ← Title
│  Floor 2                    │  ← Subtitle
├─────────────────────────────┤
│  Staff:                     │
│  ┌─────────────────────┐   │
│  │ Ahmed Hassan        │   │
│  │ Teaching Assistant  │   │
│  │ 📧 ahmed.hassan@... │   │
│  │ 📅 Sun-Wed          │   │
│  │ 🕐 9:00 AM - 2:00 PM│   │
│  └─────────────────────┘   │
│  ┌─────────────────────┐   │
│  │ Sara Mohamed        │   │
│  │ ...                 │   │
│  └─────────────────────┘   │
│                             │
│  [Additional Info]          │
│  For CS101, CS102 courses   │
└─────────────────────────────┘
```

**Lecture Hall Popup:**
```
┌─────────────────────────────┐
│  Lecture Hall A             │
│  Floor 1 • 200 seats        │
├─────────────────────────────┤
│  Today's Lectures:          │
│  ┌─────────────────────┐   │
│  │ Data Structures     │   │
│  │ CS201 - Dr. Mahmoud │   │
│  │ 🕐 9:00 AM - 10:30  │   │
│  └─────────────────────┘   │
│  ┌─────────────────────┐   │
│  │ Algorithms          │   │
│  │ CS202 - Dr. Fatima  │   │
│  │ 🕐 11:00 AM - 12:30 │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
```

#### 5.3 Popup Behavior
- Billboard mode (always face user)
- Smooth appear/disappear animations
- Auto-hide after timeout (optional)
- Manual close button
- Pin to world option

### Phase 6: Integration & Testing (Day 4-5)

#### 6.1 Scene Setup
1. Create "LocationTriggers" parent GameObject
2. Add LocationTrigger components to each location
3. Set trigger radius per location type
4. Assign location IDs matching navigation.json
5. Configure popup prefab

#### 6.2 Testing Checklist
- [ ] MultiSet localization works
- [ ] Proximity triggers fire correctly
- [ ] Popups show correct data
- [ ] UI is readable on HoloLens
- [ ] Multiple locations don't overlap
- [ ] Navigation still works
- [ ] Voice guidance still works

#### 6.3 Edge Cases
- User stands between two locations (show closest)
- User on different floor (filter by floor)
- Missing data in JSON (graceful fallback)
- Localization lost (pause proximity detection)

---

## Implementation Details

### File Structure

```
Assets/
├── Scripts/
│   ├── Navigation/
│   │   ├── NavigationManager.cs      (existing)
│   │   ├── PathRenderer.cs           (existing)
│   │   ├── VoiceGuide.cs             (existing)
│   │   └── NavigationSetup.cs        (existing)
│   ├── Localization/
│   │   ├── LocalizationWrapper.cs    (update)
│   │   └── MultiSetBridge.cs         (new)
│   ├── LocationInfo/
│   │   ├── LocationDataManager.cs    (new)
│   │   ├── LocationTrigger.cs        (new)
│   │   ├── LocationInfoPopup.cs      (new)
│   │   └── LocationDataModels.cs     (new)
│   └── Deprecated/                   (move here)
│       ├── HoloLensQrTracker.cs
│       ├── QrModalController.cs
│       └── BackendApiClient.cs
├── Resources/
│   └── Data/
│       └── navigation.json           (imported)
├── Prefabs/
│   └── UI/
│       └── LocationInfoPopup.prefab  (new)
└── Scenes/
    └── NavigationScene.unity         (updated)
```

### Key Technical Decisions

1. **Trigger System**: Use Unity's SphereCollider with isTrigger=true
   - More efficient than distance checks every frame
   - Built-in physics optimization

2. **Data Loading**: Load JSON at startup, cache in memory
   - Avoid file I/O during gameplay
   - Fast lookups by ID

3. **UI Framework**: Use MRTK v3 (or v2 if already set up)
   - Native HoloLens support
   - Proper spatial UI interactions

4. **Localization**: MultiSet SDK only
   - Remove QR complexity
   - More seamless user experience

5. **Popup Positioning**: World-locked near the location
   - Not billboard (can look around it)
   - Slightly offset so it doesn't block the view

### Questions for User

1. **MultiSet SDK Version**: Which version is being used? (1.11.2 based on samples)

2. **Coordinate Mapping**: How does MultiSet's coordinate system map to Unity world coordinates? Is there a calibration step?

3. **MRTK Version**: Is the project using MRTK 2.x or 3.x?

4. **Popup Style**: Should popups be:
   - World-locked (stay at location)
   - Billboard (always face user)
   - Tag-along (follow user but lag behind)

5. **Auto-hide**: Should popups auto-hide after X seconds, or stay until user closes them?

6. **Multiple Locations**: If user is near multiple locations, show all or just closest?

7. **Floor Detection**: How is floor/height handled in MultiSet? Do we need to filter by floor?

---

## Migration from QR to Proximity

### Before (QR-based)
```
User sees QR → Scans with HoloLens →
Backend API called → Returns location data →
Modal shows info
```

### After (Proximity-based)
```
MultiSet localizes user → User walks near location →
Trigger collider detects user →
LocationDataManager provides data →
Popup shows info
```

### Benefits
1. **No manual scanning** - Automatic when approaching
2. **No QR codes needed** - Cleaner environment
3. **Faster interaction** - No stopping to scan
4. **More intuitive** - Info appears when relevant

---

## Next Steps

1. ✅ **Approve this plan**
2. **Execute Phase 1** - Cleanup and deprecation
3. **Execute Phase 2** - MultiSet integration
4. **Execute Phase 3** - Proximity detection
5. **Execute Phase 4** - Data loading
6. **Execute Phase 5** - UI implementation
7. **Execute Phase 6** - Integration testing

---

## Notes

- Keep `NavigationManager`, `PathRenderer`, `VoiceGuide` unchanged
- They work independently of the popup system
- Popup system is additive feature
- Can disable popups without affecting navigation

---

*Document created by Claude Code - March 17, 2026*
