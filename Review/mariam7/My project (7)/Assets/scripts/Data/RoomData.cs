using UnityEngine;

/// <summary>
/// Data for a single room, tied to a QR code.
/// The QR text should match <see cref="roomID"/>.
/// </summary>
[System.Serializable]
public class RoomData
{
    [Tooltip("Unique ID for this room. This must match the QR code text.")]
    public string roomID;

    [Tooltip("Target location of this room in the scene (for navigation).")]
    public Transform roomTransform;

    [Tooltip("Prefab to spawn when this room's QR code is scanned (arrow, label, etc.).")]
    public GameObject arPrefab;
}



