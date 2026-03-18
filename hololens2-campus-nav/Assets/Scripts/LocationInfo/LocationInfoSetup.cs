using UnityEngine;
using LocationInfoSystem;

namespace LocationInfoSystem
{
    /// <summary>
    /// Helper script to set up the LocationInfo system in a scene.
    /// Attach to an empty GameObject and configure in inspector.
    /// </summary>
    public class LocationInfoSetup : MonoBehaviour
    {
        [Header("Data")]
        [Tooltip("Navigation JSON file (drag from Resources/Data)")]
        [SerializeField] private TextAsset navigationJson;

        [Header("Prefabs")]
        [Tooltip("Location trigger prefab (with SphereCollider + LocationTrigger)")]
        [SerializeField] private GameObject locationTriggerPrefab;

        [Tooltip("Location info popup prefab")]
        [SerializeField] private LocationInfoPopup popupPrefab;

        [Header("Scene References")]
        [Tooltip("Parent for all location triggers")]
        [SerializeField] private Transform triggersParent;

        [Tooltip("Parent for popups (null = world space)")]
        [SerializeField] private Transform popupParent;

        [Header("Options")]
        [SerializeField] private bool createTriggersOnStart = false;
        [SerializeField] private bool showDebugGizmos = true;

        private void Awake()
        {
            // Ensure LocationDataManager exists
            var dataManager = FindFirstObjectByType<LocationDataManager>();
            if (dataManager == null)
            {
                GameObject managerGO = new GameObject("LocationDataManager");
                dataManager = managerGO.AddComponent<LocationDataManager>();
                dataManager.GetType().GetField("navigationJson",
                    System.Reflection.BindingFlags.NonPublic |
                    System.Reflection.BindingFlags.Instance)?.SetValue(dataManager, navigationJson);
            }

            if (createTriggersOnStart)
            {
                CreateTriggersForAllLocations();
            }
        }

        /// <summary>
        /// Create LocationTrigger objects for all locations in navigation.json.
        /// </summary>
        [ContextMenu("Setup: Create Location Triggers")]
        public void CreateTriggersForAllLocations()
        {
            if (LocationDataManager.Instance == null)
            {
                Debug.LogError("[LocationInfoSetup] LocationDataManager not found!");
                return;
            }

            if (locationTriggerPrefab == null)
            {
                Debug.LogError("[LocationInfoSetup] Location trigger prefab not assigned!");
                return;
            }

            // Create parent if needed
            if (triggersParent == null)
            {
                GameObject parentGO = new GameObject("LocationTriggers");
                triggersParent = parentGO.transform;
            }

            // Get all locations
            var locations = LocationDataManager.Instance.GetAllLocations();

            foreach (var location in locations)
            {
                // Check if trigger already exists
                string triggerName = $"Trigger_{location.id}";
                if (triggersParent.Find(triggerName) != null)
                {
                    Debug.Log($"[LocationInfoSetup] Trigger already exists for: {location.name}");
                    continue;
                }

                // Create trigger
                GameObject triggerGO = Instantiate(locationTriggerPrefab, triggersParent);
                triggerGO.name = triggerName;

                // Set position from coordinates (x, y in JSON = x, z in Unity)
                triggerGO.transform.position = new Vector3(
                    location.coordinates.x,
                    location.floor * 3f, // Approximate floor height
                    location.coordinates.y
                );

                // Configure LocationTrigger
                var trigger = triggerGO.GetComponent<LocationTrigger>();
                if (trigger != null)
                {
                    trigger.SetLocationId(location.id);

                    // Set popup prefab
                    if (popupPrefab != null)
                    {
                        var popupField = trigger.GetType().GetField("popupPrefab",
                            System.Reflection.BindingFlags.NonPublic |
                            System.Reflection.BindingFlags.Instance);
                        popupField?.SetValue(trigger, popupPrefab);
                    }

                    // Set popup parent
                    if (popupParent != null)
                    {
                        var parentField = trigger.GetType().GetField("popupParent",
                            System.Reflection.BindingFlags.NonPublic |
                            System.Reflection.BindingFlags.Instance);
                        parentField?.SetValue(trigger, popupParent);
                    }
                }

                Debug.Log($"[LocationInfoSetup] Created trigger for: {location.name} at {triggerGO.transform.position}");
            }

            Debug.Log($"[LocationInfoSetup] Created {locations.Length} location triggers");
        }

        /// <summary>
        /// Clear all existing location triggers.
        /// </summary>
        [ContextMenu("Setup: Clear All Triggers")]
        public void ClearAllTriggers()
        {
            if (triggersParent == null)
            {
                // Find existing triggers parent
                var existingParent = GameObject.Find("LocationTriggers");
                if (existingParent != null)
                {
                    triggersParent = existingParent.transform;
                }
                else
                {
                    return;
                }
            }

            // Destroy all children
            while (triggersParent.childCount > 0)
            {
                DestroyImmediate(triggersParent.GetChild(0).gameObject);
            }

            Debug.Log("[LocationInfoSetup] Cleared all location triggers");
        }

        /// <summary>
        /// Validate the setup.
        /// </summary>
        [ContextMenu("Setup: Validate")]
        public void ValidateSetup()
        {
            bool isValid = true;

            if (navigationJson == null)
            {
                Debug.LogError("[LocationInfoSetup] Navigation JSON not assigned!");
                isValid = false;
            }

            if (locationTriggerPrefab == null)
            {
                Debug.LogError("[LocationInfoSetup] Location trigger prefab not assigned!");
                isValid = false;
            }

            if (popupPrefab == null)
            {
                Debug.LogWarning("[LocationInfoSetup] Popup prefab not assigned - will use fallback");
            }

            if (isValid)
            {
                Debug.Log("[LocationInfoSetup] Setup is valid!");
            }
        }
    }
}
