using UnityEngine;

namespace LocationInfoSystem
{
    /// <summary>
    /// Shows a popup when the user is close to a location.
    /// Supports a distance-check mode that fits headset-based AR better than physics-only triggers.
    /// </summary>
    [RequireComponent(typeof(SphereCollider))]
    public class LocationTrigger : MonoBehaviour
    {
        [Header("Location Data")]
        [Tooltip("Location ID from navigation.json")]
        [SerializeField] private string locationId;

        [Tooltip("Override the proximity radius from navigation.json")]
        [SerializeField] private bool overrideRadius = false;

        [Tooltip("Custom trigger radius (if overriding)")]
        [SerializeField] private float customRadius = 2.0f;

        [Header("Detection")]
        [Tooltip("Use distance checks against the localized user/camera pose instead of waiting for collider hits.")]
        [SerializeField] private bool useDistanceCheck = true;

        [Tooltip("Optional explicit transform to track. If empty, LocalizationWrapper and then Camera.main are used.")]
        [SerializeField] private Transform trackedUserTransform;

        [Tooltip("How often to evaluate distance checks.")]
        [SerializeField] private float distanceCheckInterval = 0.1f;

        [Header("UI")]
        [Tooltip("The popup prefab to instantiate")]
        [SerializeField] private LocationInfoPopup popupPrefab;

        [Tooltip("Parent transform for the popup (null = world space)")]
        [SerializeField] private Transform popupParent;

        [Tooltip("Offset from trigger center for popup position")]
        [SerializeField] private Vector3 popupOffset = new Vector3(0f, 1.5f, 0f);

        [Header("Behavior")]
        [Tooltip("Auto-hide popup when leaving trigger area")]
        [SerializeField] private bool autoHideOnExit = true;

        [Tooltip("Delay before showing popup (seconds)")]
        [SerializeField] private float showDelay = 0.5f;

        [Tooltip("Only show if user is facing the location")]
        [SerializeField] private bool requireFacing = false;

        [Tooltip("Facing angle threshold (degrees)")]
        [SerializeField] private float facingAngleThreshold = 60f;

        private LocationData locationData;
        private SphereCollider triggerCollider;
        private LocationInfoPopup currentPopup;
        private LocalizationWrapper localizationWrapper;
        private Transform runtimeUserTransform;
        private bool isUserInside;
        private float nextDistanceCheckTime;

        public System.Action<LocationData> OnPlayerEntered;
        public System.Action<LocationData> OnPlayerExited;
        public System.Action<LocationData> OnPopupShown;
        public System.Action OnPopupHidden;

        private void Awake()
        {
            EnsureTriggerCollider();
        }

        private void Start()
        {
            EnsureTriggerCollider();
            localizationWrapper = LocalizationWrapper.Instance;
            ResolveTrackedUserTransform();
            TryLoadLocationData();

            if (locationData == null)
            {
                if (LocationDataManager.Instance != null)
                {
                    LocationDataManager.Instance.OnDataLoaded += TryLoadLocationData;
                }
            }

            if (popupPrefab == null)
            {
                Debug.LogWarning($"[LocationTrigger] Popup prefab is not assigned for {locationId}.");
            }
        }

        private void Update()
        {
            if (locationData == null)
            {
                TryLoadLocationData();
                return;
            }

            if (!useDistanceCheck)
            {
                return;
            }

            if (Time.time < nextDistanceCheckTime)
            {
                return;
            }

            nextDistanceCheckTime = Time.time + Mathf.Max(0.02f, distanceCheckInterval);
            EvaluateDistanceState();
        }

        private void ResolveTrackedUserTransform()
        {
            runtimeUserTransform = trackedUserTransform;

            if (runtimeUserTransform == null && Camera.main != null)
            {
                runtimeUserTransform = Camera.main.transform;
            }
        }

        private void TryLoadLocationData()
        {
            EnsureTriggerCollider();

            if (string.IsNullOrWhiteSpace(locationId) || LocationDataManager.Instance == null || !LocationDataManager.Instance.IsLoaded)
            {
                return;
            }

            locationData = LocationDataManager.Instance.GetLocation(locationId);
            if (locationData != null && !overrideRadius)
            {
                triggerCollider.radius = locationData.proximityRadius;
            }

            if (locationData == null)
            {
                Debug.LogWarning($"[LocationTrigger] No location data found for ID: {locationId}");
            }
        }

        private void EvaluateDistanceState()
        {
            Vector3? userPosition = GetTrackedUserPosition();
            if (!userPosition.HasValue)
            {
                return;
            }

            bool isInRange = Vector3.Distance(transform.position, userPosition.Value) <= triggerCollider.radius;

            if (isInRange && !isUserInside)
            {
                HandleUserEntered(userPosition.Value);
            }
            else if (!isInRange && isUserInside)
            {
                HandleUserExited();
            }
            else if (isInRange && requireFacing && currentPopup == null && !IsInvoking(nameof(ShowPopup)) && IsUserFacingLocation(userPosition.Value))
            {
                Invoke(nameof(ShowPopup), showDelay);
            }
        }

        private Vector3? GetTrackedUserPosition()
        {
            localizationWrapper = LocalizationWrapper.Instance;
            if (localizationWrapper != null)
            {
                Vector3? localizedPosition = localizationWrapper.GetUserPosition();
                if (localizedPosition.HasValue)
                {
                    ResolveTrackedUserTransform();
                    return localizedPosition.Value;
                }
            }

            ResolveTrackedUserTransform();
            if (runtimeUserTransform != null)
            {
                return runtimeUserTransform.position;
            }

            return null;
        }

        private void HandleUserEntered(Vector3 userPosition)
        {
            isUserInside = true;
            ResolveTrackedUserTransform();
            OnPlayerEntered?.Invoke(locationData);

            if (requireFacing && !IsUserFacingLocation(userPosition))
            {
                return;
            }

            Invoke(nameof(ShowPopup), showDelay);
        }

        private void HandleUserExited()
        {
            isUserInside = false;
            CancelInvoke(nameof(ShowPopup));
            OnPlayerExited?.Invoke(locationData);

            if (autoHideOnExit)
            {
                HidePopup();
            }
        }

        private bool IsUserFacingLocation(Vector3 userPosition)
        {
            ResolveTrackedUserTransform();
            if (runtimeUserTransform == null)
            {
                return true;
            }

            Vector3 toLocation = (transform.position - userPosition).normalized;
            float angle = Vector3.Angle(runtimeUserTransform.forward, toLocation);
            return angle <= facingAngleThreshold;
        }

        private void OnTriggerEnter(Collider other)
        {
            if (useDistanceCheck)
            {
                return;
            }

            if (!other.CompareTag("Player") && other.GetComponent<UnityEngine.AI.NavMeshAgent>() == null)
            {
                return;
            }

            runtimeUserTransform = other.transform;
            HandleUserEntered(other.transform.position);
        }

        private void OnTriggerExit(Collider other)
        {
            if (useDistanceCheck)
            {
                return;
            }

            if (!other.CompareTag("Player") && other.GetComponent<UnityEngine.AI.NavMeshAgent>() == null)
            {
                return;
            }

            HandleUserExited();
        }

        private void OnTriggerStay(Collider other)
        {
            if (useDistanceCheck)
            {
                return;
            }

            if (!requireFacing || !isUserInside || currentPopup != null)
            {
                return;
            }

            runtimeUserTransform = other.transform;
            if (IsUserFacingLocation(other.transform.position) && !IsInvoking(nameof(ShowPopup)))
            {
                Invoke(nameof(ShowPopup), showDelay);
            }
        }

        private void ShowPopup()
        {
            if (locationData == null || popupPrefab == null || currentPopup != null)
            {
                return;
            }

            Vector3 popupPosition = transform.position + popupOffset;
            currentPopup = Instantiate(popupPrefab, popupPosition, Quaternion.identity, popupParent);
            currentPopup.Show(locationData);
            OnPopupShown?.Invoke(locationData);

            if (LocationDataManager.Instance != null && LocationDataManager.Instance.DebugMode)
            {
                Debug.Log($"[LocationTrigger] Showing popup for {locationData.name}");
            }
        }

        private void HidePopup()
        {
            if (currentPopup == null)
            {
                return;
            }

            currentPopup.Hide();
            currentPopup = null;
            OnPopupHidden?.Invoke();
        }

        [ContextMenu("Test: Show Popup")]
        public void TestShowPopup()
        {
            TryLoadLocationData();
            ShowPopup();
        }

        [ContextMenu("Test: Hide Popup")]
        public void TestHidePopup()
        {
            HidePopup();
        }

        public void SetLocationId(string id)
        {
            EnsureTriggerCollider();
            locationId = id;
            locationData = null;
            TryLoadLocationData();
        }

        public void SetPopupPrefab(LocationInfoPopup prefab)
        {
            popupPrefab = prefab;
        }

        public void SetPopupParent(Transform parent)
        {
            popupParent = parent;
        }

        public void SetUseDistanceCheck(bool enabled)
        {
            useDistanceCheck = enabled;
        }

        public LocationData GetLocationData()
        {
            return locationData;
        }

        public bool IsPlayerInside()
        {
            return isUserInside;
        }

        private void EnsureTriggerCollider()
        {
            if (triggerCollider == null)
            {
                triggerCollider = GetComponent<SphereCollider>();
            }

            if (triggerCollider == null)
            {
                triggerCollider = gameObject.AddComponent<SphereCollider>();
            }

            triggerCollider.isTrigger = true;

            if (overrideRadius)
            {
                triggerCollider.radius = customRadius;
            }
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = Color.cyan;
            Gizmos.DrawWireSphere(transform.position, triggerCollider != null ? triggerCollider.radius : customRadius);

            Gizmos.color = Color.yellow;
            Gizmos.DrawSphere(transform.position + popupOffset, 0.1f);
            Gizmos.DrawLine(transform.position, transform.position + popupOffset);
        }

        private void OnDestroy()
        {
            if (LocationDataManager.Instance != null)
            {
                LocationDataManager.Instance.OnDataLoaded -= TryLoadLocationData;
            }
        }
    }
}
