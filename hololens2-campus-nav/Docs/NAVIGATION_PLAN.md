# Campus Navigation Implementation Plan (Ultra-Simplified)

## Key Insight

**Let Unity handle pathfinding!**

Instead of computing paths on the server, the server just returns the **destination name**. Unity's built-in NavMesh calculates the optimal path automatically.

## The Simplest Pipeline

```
User Command (e.g., "Take me to TA Office")
        ↓
Server returns: { "destination": "TA_Office" }
        ↓
NavigationManager finds GameObject.Find("TA_Office")
        ↓
NavMeshAgent.SetDestination(targetPosition)
        ↓
Unity calculates path automatically (NavMesh)
        ↓
LineRenderer draws path.corners
        ↓
VoiceGuide reads corners for instructions
```

## What We Delete

- ❌ Server pathfinding logic
- ❌ Navigation graph on server
- ❌ Node → coordinate mapping
- ❌ Waypoint system
- ❌ CampusGraphLoader

## What We Keep

- ✅ Unity NavMesh (already set up)
- ✅ Unity NavMeshAgent (already added)
- ✅ Server as simple command relay
- ✅ MultiSet for localization

## Minimal Scripts (3-4 total)

| Script                                                                    | Purpose                                          |
| ------------------------------------------------------------------------- | ------------------------------------------------ |
| [`NavigationManager`](Assets/Scripts/Navigation/NavigationManager.cs)     | Main controller - calls server, sets destination |
| [`PathRenderer`](Assets/Scripts/Navigation/PathRenderer.cs)               | Draws path using LineRenderer + path.corners     |
| [`VoiceGuide`](Assets/Scripts/Navigation/VoiceGuide.cs)                   | Computes turn instructions from corners          |
| [`LocalizationWrapper`](Assets/Scripts/Navigation/LocalizationWrapper.cs) | Wraps MultiSet - returns user position           |

## Server Simplification

### Request

```http
POST /navigate
{
  "destination": "TA_Office"
}
```

### Response

```json
{
	"destination": "TA_Office"
}
```

That's it! Unity already knows where "TA_Office" is (GameObject in scene).

## Unity Scene Setup

```
Hierarchy:
├── CampusModel (with NavMesh baked)
├── NavigationTargets (folder)
│   ├── Entrance (empty GameObject)
│   ├── TA_Office
│   ├── Stairs_G
│   ├── Elevator
│   └── ...
├── NavigationAgent (GameObject with NavMeshAgent)
└── NavigationManager (script)
```

## Step-by-Step Implementation

### Step 1: Create Navigation Target GameObjects

Create empty GameObjects in scene at each location:

- Name them: `Entrance`, `TA_Office`, `Stairs_G`, etc.
- These are the destinations

### Step 2: Create NavigationManager

```csharp
public class NavigationManager : MonoBehaviour {
    public NavMeshAgent agent;
    public string serverUrl = "http://localhost:8000";

    public void NavigateTo(string destinationName) {
        // Find the target GameObject
        GameObject target = GameObject.Find(destinationName);
        if (target != null) {
            agent.SetDestination(target.transform.position);
        }
    }

    // OR call server to get destination
    public IEnumerator NavigateToAsync(string destinationName) {
        // Server just confirms: { "destination": destinationName }
        yield return StartCoroutine(CallServer(destinationName));
    }
}
```

### Step 3: Create PathRenderer

```csharp
public class PathRenderer : MonoBehaviour {
    public LineRenderer lineRenderer;
    public NavMeshAgent agent;

    void Update() {
        if (agent.hasPath) {
            Vector3[] corners = agent.path.corners;
            lineRenderer.positionCount = corners.Length;
            lineRenderer.SetPositions(corners);
        }
    }
}
```

### Step 4: Create VoiceGuide

```csharp
public class VoiceGuide : MonoBehaviour {
    public NavMeshAgent agent;

    void Update() {
        if (agent.hasPath && agent.remainingDistance < 1f) {
            // Arrived!
            PlayAudio("You have arrived at your destination");
        }
    }

    // Simple turn detection from corners
    void CheckForTurns() {
        Vector3[] corners = agent.path.corners;
        if (corners.Length >= 2) {
            Vector3 direction = (corners[1] - corners[0]).normalized;
            float angle = Vector3.SignedAngle(transform.forward, direction, Vector3.up);

            if (angle > 30) PlayAudio("Turn right");
            else if (angle < -30) PlayAudio("Turn left");
        }
    }
}
```

## Path Corners - The Magic

Unity's NavMeshAgent automatically generates path corners:

```
Corner 0: Start position
Corner 1: First turning point
Corner 2: Second turning point
...
Corner N: Destination
```

These are perfect for:

- ✅ Drawing path line (LineRenderer)
- ✅ Triggering voice instructions
- ✅ Avatar animation triggers

## Voice Instruction Logic

Instead of server-generated text, compute from corners:

```csharp
float GetTurnAngle(Vector3 from, Vector3 to) {
    Vector3 dirFrom = (from - previousCorner).normalized;
    Vector3 dirTo = (to - from).normalized;
    return Vector3.SignedAngle(dirFrom, dirTo, Vector3.up);
}

// If angle > 45° → "Turn right"
// If angle < -45° → "Turn left"
// Otherwise → "Go straight"
```

## Testing Order

1. Create 2 navigation targets in scene
2. Test NavMeshAgent.SetDestination() works
3. Test LineRenderer draws path.corners
4. Add voice instructions
5. Connect to server (optional for MVP)

## Benefits

1. **No coordinate mapping** - Unity uses world positions directly
2. **No server path logic** - NavMesh handles everything
3. **Automatic obstacle avoidance** - Built into Unity
4. **Stairs work automatically** - If NavMesh is baked correctly
5. **Path updates** - NavMesh recalculates if blocked

## The Hard Part

The only genuinely hard part is **localization**:

- MultiSet position → Unity world position
- May need offset/rotation correction

Everything else Unity handles.

## Summary

This approach reduces:

- Server code by ~80%
- Unity scripts from 8 to 4
- Complexity by removing entire pathfinding layer

Focus your energy on the localization wrapper - that's the real challenge.
