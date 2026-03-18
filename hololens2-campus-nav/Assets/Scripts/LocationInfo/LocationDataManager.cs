using System.Collections.Generic;
using UnityEngine;
using LocationInfoSystem;

namespace LocationInfoSystem
{
    /// <summary>
    /// Singleton manager that loads and provides access to location data from navigation.json.
    /// Attach this to a GameObject in the scene.
    /// </summary>
    public class LocationDataManager : MonoBehaviour
    {
        [Header("Data Source")]
        [SerializeField] private TextAsset navigationJson;
        [SerializeField] private bool loadOnAwake = true;

        [Header("Debug")]
        [SerializeField] private bool debugMode = false;

        // Singleton instance
        private static LocationDataManager _instance;
        public static LocationDataManager Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = FindFirstObjectByType<LocationDataManager>();
                    if (_instance == null)
                    {
                        Debug.LogError("[LocationDataManager] No instance found in scene!");
                    }
                }
                return _instance;
            }
        }

        // Data storage
        private Dictionary<string, LocationData> locationDatabase = new Dictionary<string, LocationData>();
        private NavigationDataRoot navigationData;
        private bool isLoaded = false;

        // Properties
        public bool IsLoaded => isLoaded;
        public int LocationCount => locationDatabase.Count;
        public BuildingInfo BuildingInfo => navigationData?.building;

        private void Awake()
        {
            // Singleton setup
            if (_instance != null && _instance != this)
            {
                Destroy(gameObject);
                return;
            }
            _instance = this;

            if (loadOnAwake)
            {
                LoadData();
            }
        }

        /// <summary>
        /// Load and parse the navigation.json data.
        /// </summary>
        public void LoadData()
        {
            if (navigationJson == null)
            {
                Debug.LogError("[LocationDataManager] navigationJson TextAsset is not assigned!");
                return;
            }

            try
            {
                string json = navigationJson.text;

                // Handle mixed string/integer placeType in JSON
                json = FixJsonPlaceType(json);

                navigationData = JsonUtility.FromJson<NavigationDataRoot>(json);

                if (navigationData == null || navigationData.locations == null)
                {
                    Debug.LogError("[LocationDataManager] Failed to parse navigation.json!");
                    return;
                }

                // Build lookup dictionary
                locationDatabase.Clear();
                foreach (var location in navigationData.locations)
                {
                    if (!string.IsNullOrEmpty(location.id))
                    {
                        locationDatabase[location.id] = location;

                        if (debugMode)
                        {
                            Debug.Log($"[LocationDataManager] Loaded: {location.name} (ID: {location.id})");
                        }
                    }
                }

                isLoaded = true;
                Debug.Log($"[LocationDataManager] Loaded {locationDatabase.Count} locations from navigation.json");
            }
            catch (System.Exception e)
            {
                Debug.LogError($"[LocationDataManager] Error loading data: {e.Message}");
            }
        }

        /// <summary>
        /// Get location data by ID.
        /// </summary>
        public LocationData GetLocation(string locationId)
        {
            if (!isLoaded)
            {
                Debug.LogWarning("[LocationDataManager] Data not loaded yet!");
                return null;
            }

            if (locationDatabase.TryGetValue(locationId, out LocationData data))
            {
                return data;
            }

            Debug.LogWarning($"[LocationDataManager] Location not found: {locationId}");
            return null;
        }

        /// <summary>
        /// Get location data by name (case-insensitive).
        /// </summary>
        public LocationData GetLocationByName(string name)
        {
            if (!isLoaded) return null;

            foreach (var kvp in locationDatabase)
            {
                if (kvp.Value.name.Equals(name, System.StringComparison.OrdinalIgnoreCase))
                {
                    return kvp.Value;
                }
            }

            return null;
        }

        /// <summary>
        /// Get all locations.
        /// </summary>
        public LocationData[] GetAllLocations()
        {
            if (!isLoaded) return new LocationData[0];

            LocationData[] array = new LocationData[locationDatabase.Count];
            locationDatabase.Values.CopyTo(array, 0);
            return array;
        }

        /// <summary>
        /// Get locations filtered by floor.
        /// </summary>
        public LocationData[] GetLocationsByFloor(int floor)
        {
            if (!isLoaded) return new LocationData[0];

            var result = new List<LocationData>();
            foreach (var location in locationDatabase.Values)
            {
                if (location.floor == floor)
                {
                    result.Add(location);
                }
            }
            return result.ToArray();
        }

        /// <summary>
        /// Get locations filtered by type.
        /// </summary>
        public LocationData[] GetLocationsByType(PlaceType type)
        {
            if (!isLoaded) return new LocationData[0];

            var result = new List<LocationData>();
            foreach (var location in locationDatabase.Values)
            {
                if (location.placeType == type)
                {
                    result.Add(location);
                }
            }
            return result.ToArray();
        }

        /// <summary>
        /// Get locations near a position (within radius).
        /// </summary>
        public LocationData[] GetLocationsNear(Vector2 position, float radius)
        {
            if (!isLoaded) return new LocationData[0];

            var result = new List<LocationData>();
            float radiusSqr = radius * radius;

            foreach (var location in locationDatabase.Values)
            {
                float distSqr = (location.coordinates - position).sqrMagnitude;
                if (distSqr <= radiusSqr)
                {
                    result.Add(location);
                }
            }
            return result.ToArray();
        }

        /// <summary>
        /// Check if a location ID exists.
        /// </summary>
        public bool HasLocation(string locationId)
        {
            return locationDatabase.ContainsKey(locationId);
        }

        /// <summary>
        /// Get the building name.
        /// </summary>
        public string GetBuildingName()
        {
            return navigationData?.building?.name ?? "Unknown Building";
        }

        /// <summary>
        /// Get the building address.
        /// </summary>
        public string GetBuildingAddress()
        {
            return navigationData?.building?.address ?? "";
        }

        /// <summary>
        /// Fix JSON to handle string placeType values (convert to integers).
        /// </summary>
        private string FixJsonPlaceType(string json)
        {
            // Replace string placeType values with enum integers
            json = json.Replace("\"placeType\": \"Office\"", "\"placeType\": 1");
            json = json.Replace("\"placeType\": \"LectureRoom\"", "\"placeType\": 2");
            json = json.Replace("\"placeType\": \"Lab\"", "\"placeType\": 3");
            json = json.Replace("\"placeType\": \"Cafeteria\"", "\"placeType\": 4");
            json = json.Replace("\"placeType\": \"Library\"", "\"placeType\": 5");
            json = json.Replace("\"placeType\": \"EmergencyExit\"", "\"placeType\": 6");
            json = json.Replace("\"placeType\": \"General\"", "\"placeType\": 0");
            return json;
        }

        private void OnDestroy()
        {
            if (_instance == this)
            {
                _instance = null;
            }
        }
    }
}
