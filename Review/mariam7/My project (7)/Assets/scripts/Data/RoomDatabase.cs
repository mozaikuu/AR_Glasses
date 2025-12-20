using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// ScriptableObject database that holds all rooms reachable in the building.
/// Create an instance via: Assets -> Create -> SmartNavigator -> Room Database.
/// </summary>
[CreateAssetMenu(menuName = "SmartNavigator/Room Database")]
public class RoomDatabase : ScriptableObject
{
    [Tooltip("List of all rooms that can be navigated to or recognized from QR.")]
    public List<RoomData> rooms = new List<RoomData>();

    /// <summary>
    /// Lookup a room by its ID (the decoded QR text).
    /// </summary>
    public RoomData GetRoom(string id)
    {
        if (string.IsNullOrEmpty(id) || rooms == null)
            return null;

        return rooms.Find(r => r != null && r.roomID == id);
    }

    /// <summary>
    /// Fills the database with imaginary test rooms (IDs only).
    /// Use the context menu in the Inspector to generate them.
    /// </summary>
    [ContextMenu("Fill With Test Rooms")]
    private void FillWithTestRooms()
    {
        rooms = new List<RoomData>
        {
            new RoomData { roomID = "Room101" },   // Entrance
            new RoomData { roomID = "Room102" },   // Reception
            new RoomData { roomID = "Room201" },   // Meeting Room A
            new RoomData { roomID = "Room202" },   // Meeting Room B
            new RoomData { roomID = "LabA"   },    // Lab A
            new RoomData { roomID = "LabB"   },    // Lab B
            new RoomData { roomID = "Office1"},    // Office 1
            new RoomData { roomID = "Office2"},  // Cafeteria
            new RoomData { roomID = "Exit"}        // Building Exit
        };

        // NOTE: roomTransform and arPrefab are left null on purpose so you can
        // assign real scene locations and prefabs later in the Inspector.
    }
}
