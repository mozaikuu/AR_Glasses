using UnityEngine;
using LocationInfoSystem;

namespace LocationInfoSystem
{
    /// <summary>
    /// Triggers a popup when the user enters the proximity of a location.
    /// Attach this to a GameObject at the location's position.
    /// </summary>    [RequireComponent(typeof(SphereCollider))]
    public class LocationTrigger : MonoBehaviour
    {
        [Header("Location Data")]
        [Tooltip("Location ID from navigation.json")]
        [SerializeField] private string locationId;

        [Tooltip("Override the proximity radius from navigation.json")]
        [SerializeField] private bool overrideRadius = false;

        [Tooltip("Custom trigger radius (if overriding)")]
        [SerializeField] private float customRadius = 2.0f;

        [Header("UI")]
        [Tooltip("The popup prefab to instantiate")]
        [SerializeField] private LocationInfoPopup popupPrefab;

        [Tooltip("Parent transform for the popup (null = world space)")]
        [SerializeField] private Transform popupParent;

        [Tooltip("Offset from trigger center for popup position")]
        [SerializeField] private Vector3 popupOffset = new Vector3(0, 1.5f, 0);

        [Header("Behavior")]
        [Tooltip("Auto-hide popup when leaving trigger area")]
        [SerializeField] private bool autoHideOnExit = true;

        [Tooltip("Delay before showing popup (seconds)")]
        [SerializeField] private float showDelay = 0.5f;

        [Tooltip("Only show if user is facing the location")]
        [SerializeField] private bool requireFacing = false;

        [Tooltip("Facing angle threshold (degrees)")]
        [SerializeField] private float facingAngleThreshold = 60f;

        // Runtime
        private LocationData locationData;
        private SphereCollider triggerCollider;
        private LocationInfoPopup currentPopup;
        private float enterTime;
        private bool isPlayerInside = false;
        private Transform playerTransform;

        // Events
        public System.Action<LocationData> OnPlayerEntered;
        public System.Action<LocationData> OnPlayerExited;
        public System.Action<LocationData> OnPopupShown;
        public System.Action OnPopupHidden;

        private void Awake()
        {
            triggerCollider = GetComponent<SphereCollider>();
            triggerCollider.isTrigger = true;

            // Configure collider radius
            if (overrideRadius)
            {
                triggerCollider.radius = customRadius;
            }
        }

        private void Start()
        {
            // Load location data
            if (!string.IsNullOrEmpty(locationId) && LocationDataManager.Instance != null)
            {
                locationData = LocationDataManager.Instance.GetLocation(locationId);

                if (locationData != null && !overrideRadius)
                {
                    // Use radius from navigation.json
                    triggerCollider.radius = locationData.proximityRadius;
                }
            }

            if (locationData == null)
            {
                Debug.LogWarning($"[LocationTrigger] No location data found for ID: {locationId}");
            }

            // Validate popup prefab
            if (popupPrefab == null)
            {
                Debug.LogError($"[LocationTrigger] Popup prefab not assigned for {locationId}!");
            }
        }

        private void OnTriggerEnter(Collider other)
        {
            // Check if it's the player
            if (!other.CompareTag("Player") && !other.GetComponent<UnityEngine.AI.NavMeshAgent>())
                return;

            isPlayerInside = true;
            playerTransform = other.transform;
            enterTime = Time.time;

            OnPlayerEntered?.Invoke(locationData);

            // Check facing requirement
            if (requireFacing && !IsPlayerFacingLocation())
                return;

            // Show popup with delay
            Invoke(nameof(ShowPopup), showDelay);
        }

        private void OnTriggerExit(Collider other)
        {
            // Check if it's the player
            if (!other.CompareTag("Player") && !other.GetComponent<UnityEngine.AI.NavMeshAgent>())
                return;

            isPlayerInside = false;
            playerTransform = null;

            CancelInvoke(nameof(ShowPopup));

            OnPlayerExited?.Invoke(locationData);

            if (autoHideOnExit)
            {
                HidePopup();
            }
        }

        private void OnTriggerStay(Collider other)
        {
            // Check facing while inside
            if (requireFacing && isPlayerInside && currentPopup == null)
            {
                if (IsPlayerFacingLocation() && !IsInvoking(nameof(ShowPopup)))
                {
                    Invoke(nameof(ShowPopup), showDelay);
                }
            }
        }

        /// <summary>
        /// Check if the player is facing this location.
        /// </summary>
        private bool IsPlayerFacingLocation()
        {
            if (playerTransform == null)
                return true; // Default to true if no player

            Vector3 toLocation = (transform.position - playerTransform.position).normalized;
            float angle = Vector3.Angle(playerTransform.forward, toLocation);

            return angle <= facingAngleThreshold;
        }

        /// <summary>
        /// Show the location info popup.
        /// </summary>
        private void ShowPopup()
        {
            if (locationData == null || popupPrefab == null)
                return;

            // Don't show if already visible
            if (currentPopup != null)
                return;

            // Instantiate popup
            Transform parent = popupParent != null ? popupParent : null;
            Vector3 position = transform.position + popupOffset;

            var popupInstance = Instantiate(popupPrefab, position, Quaternion.identity, parent);
            currentPopup = popupInstance;

            // Initialize popup with location data
            currentPopup.Show(locationData);

            OnPopupShown?.Invoke(locationData);

            if (LocationDataManager.Instance != null && LocationDataManager.Instance.debugMode)
            {
                Debug.Log($"[LocationTrigger] Showing popup for: {locationData.name}");
            }
        }

        /// <summary>
        /// Hide the popup.
        /// </summary>
        private void HidePopup()
        {
            if (currentPopup != null)
            {
                currentPopup.Hide();
                currentPopup = null;

                OnPopupHidden?.Invoke();
            }
        }

        /// <summary>
        /// Manually trigger the popup (for testing or external calls).
        /// </summary>
        [ContextMenu("Test: Show Popup")]
        public void TestShowPopup()
        {
            if (locationData == null && LocationDataManager.Instance != null)
            {
                locationData = LocationDataManager.Instance.GetLocation(locationId);
            }

            ShowPopup();
        }

        /// <summary>
        /// Manually hide the popup.
        /// </summary>
        [ContextMenu("Test: Hide Popup")]
        public void TestHidePopup()
        {
            HidePopup();
        }

        /// <summary>
        /// Set the location ID at runtime.
        /// </summary>
        public void SetLocationId(string id)
        {
            locationId = id;
            if (LocationDataManager.Instance != null)
            {
                locationData = LocationDataManager.Instance.GetLocation(id);
            }
        }

        /// <summary>
        /// Get the current location data.
        /// </summary>
        public LocationData GetLocationData()
        {
            return locationData;
        }

        /// <summary>
        /// Check if player is currently inside trigger.
        /// </summary>
        public bool IsPlayerInside()
        {
            return isPlayerInside;
        }

        private void OnDrawGizmosSelected()
        {
            // Draw trigger radius in editor
            Gizmos.color = Color.cyan;
            Gizmos.DrawWireSphere(transform.position, triggerCollider != null ? triggerCollider.radius : customRadius);

            // Draw popup position
            Gizmos.color = Color.yellow;
            Gizmos.DrawSphere(transform.position + popupOffset, 0.1f);
            Gizmos.DrawLine(transform.position, transform.position + popupOffset);
        }
    }
}
