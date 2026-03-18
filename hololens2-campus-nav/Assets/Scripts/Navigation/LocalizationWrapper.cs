using System;
using UnityEngine;

/// <summary>
/// Wrapper for MultiSet SDK localization.
/// Returns user position in Unity world coordinates.
///
/// Usage:
/// 1. Add OnDeviceLocalizationManager to scene (from MultiSet SDK)
/// 2. Reference it in this wrapper
/// 3. Call RequestLocalization() to get user position
/// 4. Use GetUserPosition() to get current position
///
/// NOTE: MultiSet HoloLens support requires proper SDK setup.
/// </summary>
public class LocalizationWrapper : MonoBehaviour
{
    [Header("MultiSet Configuration")]
    [Tooltip("Reference to MultiSet OnDeviceLocalizationManager")]
    [SerializeField] private MonoBehaviour onDeviceLocalizationManager;

    [Tooltip("Map or MapSet code for localization")]
    [SerializeField] private string mapCode = "";

    [Tooltip("Auto-start localization on enable")]
    [SerializeField] private bool autoLocalizeOnStart = true;

    [Header("Position Offset")]
    [Tooltip("Offset applied to MultiSet position")]
    [SerializeField] private Vector3 positionOffset = Vector3.zero;

    [Tooltip("Rotation offset applied to MultiSet rotation")]
    [SerializeField] private Vector3 rotationOffsetEuler = Vector3.zero;

    [Header("Debug")]
    [SerializeField] private bool debugMode = false;
    [SerializeField] private bool simulateInEditor = true;
    [SerializeField] private Vector3 simulatedPosition = new Vector3(0, 0, 0);

    // Current localization state
    private bool isLocalized = false;
    private Vector3 currentPosition;
    private Quaternion currentRotation;
    private string currentLocationId = "";
    private float lastUpdateTime = 0f;

    // Events
    public event Action<bool> OnLocalizationStateChanged;
    public event Action<string, Vector3> OnLocationChanged;
    public event Action OnLocalizationFailed;

    // Properties
    public bool IsLocalized => isLocalized;
    public Vector3 CurrentPosition => currentPosition;
    public Quaternion CurrentRotation => currentRotation;
    public string CurrentLocationId => currentLocationId;

    // Singleton
    private static LocalizationWrapper _instance;
    public static LocalizationWrapper Instance
    {
        get
        {
            if (_instance == null)
                _instance = FindFirstObjectByType<LocalizationWrapper>();
            return _instance;
        }
    }

    private void Awake()
    {
        if (_instance != null && _instance != this)
        {
            Destroy(gameObject);
            return;
        }
        _instance = this;

        // Initialize position
        currentPosition = transform.position;
        currentRotation = transform.rotation;
    }

    private void Start()
    {
        if (autoLocalizeOnStart)
        {
            RequestLocalization();
        }
    }

    /// <summary>
    /// Get user position in Unity world coordinates.
    /// </summary>
    public Vector3? GetUserPosition()
    {
        if (isLocalized)
        {
            return currentPosition;
        }

#if UNITY_EDITOR
        if (simulateInEditor)
        {
            return simulatedPosition;
        }
#endif

        return null;
    }

    /// <summary>
    /// Get user rotation in Unity world coordinates.
    /// </summary>
    public Quaternion? GetUserRotation()
    {
        if (isLocalized)
        {
            return currentRotation;
        }
        return null;
    }

    /// <summary>
    /// Request localization from MultiSet.
    /// Call this to start or refresh localization.
    /// </summary>
    public void RequestLocalization()
    {
        if (string.IsNullOrEmpty(mapCode))
        {
            Debug.LogWarning("[LocalizationWrapper] Map code not set!");
            OnLocalizationFailed?.Invoke();
            return;
        }

#if UNITY_EDITOR
        if (simulateInEditor)
        {
            // Simulate successful localization in editor
            SetPosition(simulatedPosition, Quaternion.identity, "Simulated");
            Debug.Log("[LocalizationWrapper] Using simulated position in editor");
            return;
        }
#endif

        // TODO: Integrate with MultiSet SDK
        // This requires the actual MultiSet SDK implementation
        // Example:
        // if (onDeviceLocalizationManager != null)
        // {
        //     // Validate map code first
        //     onDeviceLocalizationManager.ValidateMapOrMapSetCode(mapCode);
        //     // Then localize
        //     onDeviceLocalizationManager.LocalizeFrame();
        // }

        Debug.Log("[LocalizationWrapper] Requesting MultiSet localization...");

        // For now, simulate success after a delay
        // Remove this when MultiSet is properly integrated
        Invoke(nameof(SimulateLocalizationSuccess), 2.0f);
    }

    /// <summary>
    /// Set the map code at runtime.
    /// </summary>
    public void SetMapCode(string code)
    {
        mapCode = code;
    }

    /// <summary>
    /// Update position from MultiSet SDK callback.
    /// Call this from MultiSet event handlers.
    /// </summary>
    public void UpdateFromMultiSet(Vector3 multisetPosition, Quaternion multisetRotation, string locationId = "")
    {
        // Apply offsets
        Vector3 offsetPosition = multisetPosition + positionOffset;
        Quaternion offsetRotation = Quaternion.Euler(rotationOffsetEuler) * multisetRotation;

        SetPosition(offsetPosition, offsetRotation, locationId);

        if (debugMode)
        {
            Debug.Log($"[LocalizationWrapper] MultiSet position: {multisetPosition}, offset: {offsetPosition}");
        }
    }

    /// <summary>
    /// Set position directly (for testing or external systems).
    /// </summary>
    public void SetPosition(Vector3 position, Quaternion rotation, string locationId = "")
    {
        currentPosition = position;
        currentRotation = rotation;
        currentLocationId = locationId;

        if (!isLocalized)
        {
            isLocalized = true;
            OnLocalizationStateChanged?.Invoke(true);
        }

        OnLocationChanged?.Invoke(locationId, currentPosition);
        lastUpdateTime = Time.time;

        if (debugMode)
        {
            Debug.Log($"[LocalizationWrapper] Position set: {position}, Location: {locationId}");
        }
    }

    /// <summary>
    /// Reset localization state.
    /// </summary>
    public void ResetLocalization()
    {
        isLocalized = false;
        currentLocationId = "";
        OnLocalizationStateChanged?.Invoke(false);
    }

    /// <summary>
    /// Check if localization is recent (within timeout).
    /// </summary>
    public bool IsLocalizationRecent(float timeoutSeconds = 10f)
    {
        return (Time.time - lastUpdateTime) < timeoutSeconds;
    }

    /// <summary>
    /// Get the current location name.
    /// </summary>
    public string GetCurrentLocationName()
    {
        return currentLocationId;
    }

    /// <summary>
    /// Force a position update (for testing).
    /// </summary>
    [ContextMenu("Test: Set Simulated Position")]
    public void SetTestPosition()
    {
        SetPosition(simulatedPosition, Quaternion.identity, "Test");
    }

    /// <summary>
    /// Request re-localization.
    /// </summary>
    [ContextMenu("Test: Request Localization")]
    public void TestRequestLocalization()
    {
        RequestLocalization();
    }

    private void SimulateLocalizationSuccess()
    {
        // This is temporary until MultiSet is properly integrated
        if (!isLocalized)
        {
            SetPosition(simulatedPosition, Quaternion.identity, "Simulated");
        }
    }

    private void Update()
    {
        if (debugMode && isLocalized)
        {
            Debug.DrawRay(currentPosition, Vector3.up * 0.5f, Color.green);
            Debug.DrawRay(currentPosition, currentRotation * Vector3.forward * 0.3f, Color.blue);
        }
    }

    private void OnDestroy()
    {
        if (_instance == this)
        {
            _instance = null;
        }
    }
}
