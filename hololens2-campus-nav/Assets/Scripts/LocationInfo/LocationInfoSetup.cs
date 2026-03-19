using System.Collections;
using UnityEngine;

namespace LocationInfoSystem
{
    /// <summary>
    /// Scene helper that creates the location info manager and optional trigger objects.
    /// </summary>
    public class LocationInfoSetup : MonoBehaviour
    {
        [Header("Data")]
        [Tooltip("Optional override. Leave empty to load from StreamingAssets/Campus/navigation.json")]
        [SerializeField] private TextAsset navigationJsonOverride;

        [SerializeField] private string streamingAssetsRelativePath = "Campus/navigation.json";

        [Header("Prefabs")]
        [Tooltip("Optional trigger prefab. If omitted, trigger objects are created in code.")]
        [SerializeField] private GameObject locationTriggerPrefab;

        [Tooltip("Location info popup prefab")]
        [SerializeField] private LocationInfoPopup popupPrefab;

        [Header("Scene References")]
        [SerializeField] private Transform triggersParent;
        [SerializeField] private Transform popupParent;

        [Header("Options")]
        [SerializeField] private bool createTriggersOnStart = true;
        [SerializeField] private bool useDistanceCheck = true;

        private IEnumerator Start()
        {
            LocationDataManager dataManager = EnsureDataManager();

            if (dataManager == null)
            {
                yield break;
            }

            if (!dataManager.IsLoaded && !dataManager.IsLoading)
            {
                dataManager.LoadData();
            }

            yield return new WaitUntil(() => dataManager != null && dataManager.IsLoaded);

            if (createTriggersOnStart)
            {
                CreateTriggersForAllLocations();
            }
        }

        private LocationDataManager EnsureDataManager()
        {
            LocationDataManager dataManager = FindFirstObjectByType<LocationDataManager>();
            if (dataManager == null)
            {
                GameObject managerObject = new GameObject("LocationDataManager");
                dataManager = managerObject.AddComponent<LocationDataManager>();
            }

            dataManager.SetNavigationJsonOverride(navigationJsonOverride);
            dataManager.SetStreamingAssetsRelativePath(streamingAssetsRelativePath);
            return dataManager;
        }

        [ContextMenu("Setup: Create Location Triggers")]
        public void CreateTriggersForAllLocations()
        {
            LocationDataManager dataManager = EnsureDataManager();
            if (dataManager == null)
            {
                Debug.LogError("[LocationInfoSetup] Could not create or find LocationDataManager.");
                return;
            }

            if (!dataManager.IsLoaded)
            {
                bool loaded = dataManager.LoadDataImmediate();
                if (!loaded)
                {
                    Debug.LogError("[LocationInfoSetup] Location data is not loaded yet.");
                    return;
                }
            }

            if (!dataManager.IsLoaded)
            {
                Debug.LogError("[LocationInfoSetup] Location data is not loaded yet.");
                return;
            }

            if (triggersParent == null)
            {
                GameObject parentObject = GameObject.Find("LocationTriggers") ?? new GameObject("LocationTriggers");
                triggersParent = parentObject.transform;
            }

            foreach (LocationData location in dataManager.GetAllLocations())
            {
                string triggerName = $"Trigger_{location.id}";
                Transform existingTrigger = triggersParent.Find(triggerName);
                GameObject triggerObject;

                if (existingTrigger != null)
                {
                    triggerObject = existingTrigger.gameObject;
                }
                else if (locationTriggerPrefab != null)
                {
                    triggerObject = Instantiate(locationTriggerPrefab, triggersParent);
                }
                else
                {
                    triggerObject = new GameObject(triggerName);
                    triggerObject.transform.SetParent(triggersParent);
                    triggerObject.AddComponent<SphereCollider>();
                    triggerObject.AddComponent<LocationTrigger>();
                }

                triggerObject.name = triggerName;
                triggerObject.transform.position = new Vector3(location.coordinates.x, location.floor * 3f, location.coordinates.y);

                LocationTrigger trigger = triggerObject.GetComponent<LocationTrigger>();
                if (trigger == null)
                {
                    trigger = triggerObject.AddComponent<LocationTrigger>();
                }

                trigger.SetLocationId(location.id);
                trigger.SetPopupPrefab(popupPrefab);
                trigger.SetPopupParent(popupParent);
                trigger.SetUseDistanceCheck(useDistanceCheck);

                if (existingTrigger != null)
                {
                    Debug.Log($"[LocationInfoSetup] Updated trigger for {location.name}");
                }
                else
                {
                    Debug.Log($"[LocationInfoSetup] Created trigger for {location.name}");
                }

#if UNITY_EDITOR
                UnityEditor.EditorUtility.SetDirty(triggerObject);
                UnityEditor.EditorUtility.SetDirty(trigger);
#endif
            }
        }

        [ContextMenu("Setup: Clear All Triggers")]
        public void ClearAllTriggers()
        {
            if (triggersParent == null)
            {
                GameObject existingParent = GameObject.Find("LocationTriggers");
                if (existingParent == null)
                {
                    return;
                }

                triggersParent = existingParent.transform;
            }

            while (triggersParent.childCount > 0)
            {
                DestroyImmediate(triggersParent.GetChild(0).gameObject);
            }
        }

        [ContextMenu("Setup: Validate")]
        public void ValidateSetup()
        {
            LocationDataManager dataManager = EnsureDataManager();

            if (popupPrefab == null)
            {
                Debug.LogWarning("[LocationInfoSetup] Popup prefab is not assigned yet.");
            }

            if (dataManager == null)
            {
                Debug.LogWarning("[LocationInfoSetup] LocationDataManager is not available.");
            }
            else if (!dataManager.IsLoaded)
            {
                Debug.Log("[LocationInfoSetup] LocationDataManager exists but data is not loaded yet. This is normal before Play Mode unless you run the setup command.");
            }

            Debug.Log("[LocationInfoSetup] Validation complete. Make sure Unity reimports the pasted scripts so .meta files are generated.");
        }
    }
}
