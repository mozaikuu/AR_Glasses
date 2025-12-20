using UnityEngine;

/// <summary>
/// Handles navigation logic: reacts to QR scans, spawns AR content,
/// and can orient arrows / paths towards the target room.
/// </summary>
public class NavigationManager : MonoBehaviour
{
    public static NavigationManager Instance { get; private set; }

    [Header("Database")]
    [Tooltip("ScriptableObject with all rooms and their QR IDs.")]
    public RoomDatabase roomDatabase;

    [Header("Navigation Target")]
    [Tooltip("ID of the destination room (must exist in the RoomDatabase).")]
    public string targetRoomID;

    [Tooltip("Reference to the user's head/camera (for path rendering, etc.).")]
    public Transform userHead;

    // Runtime state
    private RoomData _currentRoom;
    private GameObject _activeARObject;

    private void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this;
    }

    private void OnEnable()
    {
        QRScanner.OnQRDetected += OnRoomScanned;
    }

    private void OnDisable()
    {
        QRScanner.OnQRDetected -= OnRoomScanned;
    }

    /// <summary>
    /// Called whenever a QR is detected by <see cref="QRScanner"/>.
    /// </summary>
    private void OnRoomScanned(string roomID, Vector3 qrPos, Quaternion qrRot)
    {
        if (roomDatabase == null)
        {
            Debug.LogWarning("NavigationManager: RoomDatabase is not assigned.");
            return;
        }

        _currentRoom = roomDatabase.GetRoom(roomID);

        if (_currentRoom == null)
        {
            Debug.Log("NavigationManager: Unknown QR scanned: " + roomID);
            return;
        }

        SpawnRoomAR(qrPos, qrRot);

        if (!string.IsNullOrEmpty(targetRoomID) && roomID == targetRoomID)
        {
            DestinationReached();
        }
        else
        {
            GuideToTarget();
        }
    }

    /// <summary>
    /// Spawns the AR prefab associated with the current room at the QR position/rotation.
    /// </summary>
    private void SpawnRoomAR(Vector3 pos, Quaternion rot)
    {
        if (_currentRoom == null || _currentRoom.arPrefab == null)
            return;

        if (_activeARObject != null)
        {
            Destroy(_activeARObject);
        }

        _activeARObject = Instantiate(_currentRoom.arPrefab, pos, rot);

        // Optionally hook up arrow controller / line renderer targets automatically
        var arrow = _activeARObject.GetComponentInChildren<ArrowController>();
        if (arrow != null)
        {
            RoomData target = roomDatabase.GetRoom(targetRoomID);
            if (target != null)
            {
                arrow.target = target.roomTransform;
            }
        }

        var line = _activeARObject.GetComponentInChildren<LinePathRenderer>();
        if (line != null)
        {
            RoomData target = roomDatabase.GetRoom(targetRoomID);
            if (target != null)
            {
                line.user = userHead;
                line.target = target.roomTransform;
            }
        }
    }

    /// <summary>
    /// Basic guiding logic (logging for now, but you can expand with real pathfinding).
    /// </summary>
    private void GuideToTarget()
    {
        if (roomDatabase == null || string.IsNullOrEmpty(targetRoomID))
            return;

        RoomData target = roomDatabase.GetRoom(targetRoomID);
        if (target == null || _currentRoom == null)
            return;

        Debug.Log($"NavigationManager: Navigating from {_currentRoom.roomID} to {target.roomID}");
        // Here you could run real indoor navigation / graph search, etc.
    }

    private void DestinationReached()
    {
        Debug.Log("NavigationManager: Destination Reached!");
        // You can trigger animations, sounds, or UI feedback here.
    }
}



