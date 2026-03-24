# Navigation System Setup Guide

## Created Scripts

The following Unity scripts have been created in `Assets/Scripts/Navigation/`:

| Script                                                                       | Purpose                                                         |
| ---------------------------------------------------------------------------- | --------------------------------------------------------------- |
| [`NavigationManager.cs`](Assets/Scripts/Navigation/NavigationManager.cs)     | Main controller - handles server communication and NavMeshAgent |
| [`PathRenderer.cs`](Assets/Scripts/Navigation/PathRenderer.cs)               | Renders path using LineRenderer                                 |
| [`VoiceGuide.cs`](Assets/Scripts/Navigation/VoiceGuide.cs)                   | Provides turn-by-turn voice instructions                        |
| [`LocalizationWrapper.cs`](Assets/Scripts/Navigation/LocalizationWrapper.cs) | Wraps MultiSet SDK for localization                             |
| [`NavigationSetup.cs`](Assets/Scripts/Navigation/NavigationSetup.cs)         | Helper to set up navigation automatically                       |

## Quick Setup in Unity Editor

### Step 1: Create Navigation Targets

1. Create an empty GameObject named "NavigationTargets"
2. Create child GameObjects for each location:
   - `Entrance` - at main gate position
   - `TA_Office` - at TA office position
   - `Stairs_G` - at ground floor stairs
   - `Floor_1` - at first floor
   - etc.

### Step 2: Set Up Agent

1. Select your agent GameObject (with NavMeshAgent)
2. Add `NavigationManager` component
3. Add `PathRenderer` component (adds LineRenderer automatically)
4. Add `VoiceGuide` component

### Step 3: Link Components

In NavigationManager inspector:

- Drag NavMeshAgent to `Nav Mesh Agent` field
- Drag PathRenderer to `Path Renderer` field
- Drag VoiceGuide to `Voice Guide` field

### Step 4: Test

1. Press Play
2. In console or via button, call:
   ```csharp
   navigationManager.NavigateTo("TA_Office");
   ```

## Using NavigationSetup Helper

1. Create empty GameObject "NavigationSetup"
2. Add `NavigationSetup` component
3. Configure target names in Inspector
4. Right-click → "Setup Navigation"

## How It Works

### Flow

```
User selects destination
        ↓
NavigationManager.NavigateTo("TA_Office")
        ↓
GameObject.Find("TA_Office") → gets position
        ↓
navMeshAgent.SetDestination(position)
        ↓
Unity NavMesh calculates path automatically
        ↓
PathRenderer draws path.corners
        ↓
VoiceGuide announces turns at corners
```

### Path Finding

- Unity's built-in NavMesh handles all pathfinding
- No server-side path calculation needed
- Server just confirms destination name

### Voice Instructions

- Calculated from path corner angles
- If turn angle > 30° → "Turn right"
- If turn angle < -30° → "Turn left"
- Otherwise → "Go straight"

## Integration with Server

The server endpoint `/navigation/start` should return:

```json
{
	"destination": "TA_Office"
}
```

Unity will:

1. Parse the destination name
2. Find the GameObject
3. Set NavMeshAgent destination
4. NavMesh calculates the path

## Testing Checklist

- [ ] Create navigation target GameObjects in scene
- [ ] Add NavMeshAgent to agent
- [ ] Add NavigationManager, PathRenderer, VoiceGuide
- [ ] Link components in Inspector
- [ ] Build and test on PC
- [ ] Test on Android
- [ ] Test path visualization
- [ ] Test voice instructions (if TTS available)
- [ ] Test on HoloLens 2 (when ready)

## Common Issues

### Path not drawing

- Ensure LineRenderer is enabled
- Check path has at least 2 corners
- Verify NavMesh is baked

### Agent not moving

- Check NavMeshAgent is enabled
- Verify destination is on NavMesh
- Check for obstacles

### Voice not playing

- Check MRTK TextToSpeech or Windows Speech available
- Verify voice guide is enabled

### Localization not working

- MultiSet SDK integration needed
- Or use QR fallback
