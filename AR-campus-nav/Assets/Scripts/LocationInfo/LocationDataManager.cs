using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;

namespace LocationInfoSystem
{
    /// <summary>
    /// Loads and serves location metadata for popup/navigation features.
    /// Uses StreamingAssets by default so the same flow works on Meta Quest.
    /// </summary>
    public class LocationDataManager : MonoBehaviour
    {
        [Header("Data Source")]
        [SerializeField] private TextAsset navigationJsonOverride;
        [SerializeField] private string streamingAssetsRelativePath = "Campus/navigation.json";
        [SerializeField] private bool loadOnAwake = true;

        [Header("Debug")]
        [SerializeField] private bool debugMode = false;

        private static LocationDataManager _instance;

        private readonly Dictionary<string, LocationData> locationDatabase = new Dictionary<string, LocationData>();
        private NavigationDataRoot navigationData;
        private Coroutine loadRoutine;
        private bool isLoaded;
        private bool isLoading;

        public static LocationDataManager Instance
        {
            get
            {
                if (_instance == null)
                {
                    _instance = FindFirstObjectByType<LocationDataManager>();
                    if (_instance == null)
                    {
                        Debug.LogError("[LocationDataManager] No instance found in scene.");
                    }
                }

                return _instance;
            }
        }

        public event Action OnDataLoaded;
        public event Action<string> OnDataLoadFailed;

        public bool IsLoaded => isLoaded;
        public bool IsLoading => isLoading;
        public bool DebugMode => debugMode;
        public int LocationCount => locationDatabase.Count;
        public BuildingInfo BuildingInfo => navigationData?.building;

        private void Awake()
        {
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

        public void SetNavigationJsonOverride(TextAsset textAsset)
        {
            navigationJsonOverride = textAsset;
        }

        public void SetStreamingAssetsRelativePath(string relativePath)
        {
            if (!string.IsNullOrWhiteSpace(relativePath))
            {
                streamingAssetsRelativePath = relativePath;
            }
        }

        public void LoadData()
        {
            if (isLoading)
            {
                return;
            }

            if (loadRoutine != null)
            {
                StopCoroutine(loadRoutine);
            }

            loadRoutine = StartCoroutine(LoadDataRoutine());
        }

        public bool LoadDataImmediate()
        {
            if (isLoading)
            {
                return false;
            }

            isLoading = true;
            isLoaded = false;

            string json = null;
            string sourceLabel = string.Empty;

            if (navigationJsonOverride != null)
            {
                json = navigationJsonOverride.text;
                sourceLabel = "TextAsset override";
            }
            else
            {
                string streamingPath = Path.Combine(Application.streamingAssetsPath, streamingAssetsRelativePath).Replace("\\", "/");
                sourceLabel = streamingPath;

                if (!File.Exists(streamingPath))
                {
                    FailLoad($"navigation.json not found at {streamingPath}");
                    return false;
                }

                json = File.ReadAllText(streamingPath);
            }

            if (string.IsNullOrWhiteSpace(json))
            {
                FailLoad("navigation.json was empty.");
                return false;
            }

            ParseJson(json, sourceLabel);
            return isLoaded;
        }

        private IEnumerator LoadDataRoutine()
        {
            isLoading = true;
            isLoaded = false;

            string json = null;
            string sourceLabel = string.Empty;

            if (navigationJsonOverride != null)
            {
                json = navigationJsonOverride.text;
                sourceLabel = "TextAsset override";
            }
            else
            {
                string streamingPath = Path.Combine(Application.streamingAssetsPath, streamingAssetsRelativePath).Replace("\\", "/");
                sourceLabel = streamingPath;

                if (streamingPath.StartsWith("jar:", StringComparison.OrdinalIgnoreCase) ||
                    streamingPath.StartsWith("http", StringComparison.OrdinalIgnoreCase))
                {
                    using (UnityWebRequest request = UnityWebRequest.Get(streamingPath))
                    {
                        yield return request.SendWebRequest();

                        if (request.result != UnityWebRequest.Result.Success)
                        {
                            FailLoad($"Failed to load navigation data from {streamingPath}: {request.error}");
                            yield break;
                        }

                        json = request.downloadHandler.text;
                    }
                }
                else
                {
                    if (!File.Exists(streamingPath))
                    {
                        FailLoad($"navigation.json not found at {streamingPath}");
                        yield break;
                    }

                    json = File.ReadAllText(streamingPath);
                }
            }

            if (string.IsNullOrWhiteSpace(json))
            {
                FailLoad("navigation.json was empty.");
                yield break;
            }

            ParseJson(json, sourceLabel);
        }

        private void ParseJson(string json, string sourceLabel)
        {
            try
            {
                navigationData = JsonUtility.FromJson<NavigationDataRoot>(FixJsonPlaceType(json));

                if (navigationData == null || navigationData.locations == null)
                {
                    FailLoad($"Failed to parse navigation data from {sourceLabel}");
                    return;
                }

                locationDatabase.Clear();
                foreach (LocationData location in navigationData.locations)
                {
                    if (string.IsNullOrWhiteSpace(location?.id))
                    {
                        continue;
                    }

                    locationDatabase[location.id] = location;

                    if (debugMode)
                    {
                        Debug.Log($"[LocationDataManager] Loaded {location.id} -> {location.name}");
                    }
                }

                isLoaded = true;
                isLoading = false;
                loadRoutine = null;

                Debug.Log($"[LocationDataManager] Loaded {locationDatabase.Count} locations from {sourceLabel}");
                OnDataLoaded?.Invoke();
            }
            catch (Exception exception)
            {
                FailLoad($"Error parsing navigation data: {exception.Message}");
            }
        }

        private void FailLoad(string message)
        {
            isLoading = false;
            isLoaded = false;
            loadRoutine = null;

            Debug.LogError($"[LocationDataManager] {message}");
            OnDataLoadFailed?.Invoke(message);
        }

        public LocationData GetLocation(string locationId)
        {
            if (!isLoaded)
            {
                Debug.LogWarning("[LocationDataManager] Data not loaded yet.");
                return null;
            }

            if (locationDatabase.TryGetValue(locationId, out LocationData data))
            {
                return data;
            }

            Debug.LogWarning($"[LocationDataManager] Location not found: {locationId}");
            return null;
        }

        public LocationData GetLocationByName(string name)
        {
            if (!isLoaded || string.IsNullOrWhiteSpace(name))
            {
                return null;
            }

            foreach (KeyValuePair<string, LocationData> entry in locationDatabase)
            {
                if (entry.Value.name.Equals(name, StringComparison.OrdinalIgnoreCase))
                {
                    return entry.Value;
                }
            }

            return null;
        }

        public LocationData[] GetAllLocations()
        {
            if (!isLoaded)
            {
                return Array.Empty<LocationData>();
            }

            LocationData[] array = new LocationData[locationDatabase.Count];
            locationDatabase.Values.CopyTo(array, 0);
            return array;
        }

        public LocationData[] GetLocationsByFloor(int floor)
        {
            if (!isLoaded)
            {
                return Array.Empty<LocationData>();
            }

            List<LocationData> result = new List<LocationData>();
            foreach (LocationData location in locationDatabase.Values)
            {
                if (location.floor == floor)
                {
                    result.Add(location);
                }
            }

            return result.ToArray();
        }

        public LocationData[] GetLocationsByType(PlaceType type)
        {
            if (!isLoaded)
            {
                return Array.Empty<LocationData>();
            }

            List<LocationData> result = new List<LocationData>();
            foreach (LocationData location in locationDatabase.Values)
            {
                if (location.placeType == type)
                {
                    result.Add(location);
                }
            }

            return result.ToArray();
        }

        public LocationData[] GetLocationsNear(Vector2 position, float radius)
        {
            if (!isLoaded)
            {
                return Array.Empty<LocationData>();
            }

            List<LocationData> result = new List<LocationData>();
            float radiusSquared = radius * radius;

            foreach (LocationData location in locationDatabase.Values)
            {
                float distanceSquared = (location.coordinates - position).sqrMagnitude;
                if (distanceSquared <= radiusSquared)
                {
                    result.Add(location);
                }
            }

            return result.ToArray();
        }

        public bool HasLocation(string locationId)
        {
            return isLoaded && locationDatabase.ContainsKey(locationId);
        }

        public string GetBuildingName()
        {
            return navigationData?.building?.name ?? "Unknown Building";
        }

        public string GetBuildingAddress()
        {
            return navigationData?.building?.address ?? string.Empty;
        }

        private string FixJsonPlaceType(string json)
        {
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
