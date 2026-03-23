using System;
using System.Reflection;
using MultiSet;
using UnityEngine;

/// <summary>
/// Quest-first bridge between the app and MultiSet localization managers.
/// It uses real MultiSet events when available and keeps the live user pose in sync with the tracked camera.
/// </summary>
public class LocalizationWrapper : MonoBehaviour
{
    [Header("MultiSet References")]
    [SerializeField] private MapLocalizationManager mapLocalizationManager;
    [SerializeField] private SingleFrameLocalizationManager singleFrameLocalizationManager;
    [SerializeField] private MonoBehaviour onDeviceLocalizationManager;
    [SerializeField] private Transform trackedPoseSource;

    [Header("Configuration")]
    [SerializeField] private string mapCode = "";
    [SerializeField] private bool autoLocalizeOnStart = true;
    [SerializeField] private bool keepPoseSyncedToTrackedSource = true;

    [Header("Pose Offset")]
    [SerializeField] private Vector3 positionOffset = Vector3.zero;
    [SerializeField] private Vector3 rotationOffsetEuler = Vector3.zero;

    [Header("Debug")]
    [SerializeField] private bool debugMode = false;
    [SerializeField] private bool simulateInEditor = true;
    [SerializeField] private Vector3 simulatedPosition = Vector3.zero;

    private static LocalizationWrapper _instance;

    private bool isLocalized;
    private Vector3 currentPosition;
    private Quaternion currentRotation = Quaternion.identity;
    private string currentLocationId = string.Empty;
    private float lastUpdateTime;

    public event Action<bool> OnLocalizationStateChanged;
    public event Action<string, Vector3> OnLocationChanged;
    public event Action OnLocalizationFailed;

    public bool IsLocalized => isLocalized;
    public Vector3 CurrentPosition => currentPosition;
    public Quaternion CurrentRotation => currentRotation;
    public string CurrentLocationId => currentLocationId;

    public static LocalizationWrapper Instance
    {
        get
        {
            if (_instance == null)
            {
                _instance = FindFirstObjectByType<LocalizationWrapper>();
            }

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
        ResolveReferences();

        currentPosition = trackedPoseSource != null ? trackedPoseSource.position : transform.position;
        currentRotation = trackedPoseSource != null ? trackedPoseSource.rotation : transform.rotation;
    }

    private void OnEnable()
    {
        ResolveReferences();
        SubscribeToMultiSetEvents();
    }

    private void Start()
    {
        if (autoLocalizeOnStart)
        {
            RequestLocalization();
        }
    }

    private void Update()
    {
        if (isLocalized && keepPoseSyncedToTrackedSource && trackedPoseSource != null)
        {
            ApplyTrackedSourcePose(currentLocationId);
        }

        if (debugMode && isLocalized)
        {
            Debug.DrawRay(currentPosition, Vector3.up * 0.5f, Color.green);
            Debug.DrawRay(currentPosition, currentRotation * Vector3.forward * 0.3f, Color.blue);
        }
    }

    private void OnDisable()
    {
        UnsubscribeFromMultiSetEvents();
    }

    public Vector3? GetUserPosition()
    {
#if UNITY_EDITOR
        if (!isLocalized && simulateInEditor)
        {
            return simulatedPosition;
        }
#endif

        if (isLocalized)
        {
            return currentPosition;
        }

        if (trackedPoseSource != null)
        {
            return trackedPoseSource.position;
        }

        return null;
    }

    public Quaternion? GetUserRotation()
    {
        if (isLocalized)
        {
            return currentRotation;
        }

        if (trackedPoseSource != null)
        {
            return trackedPoseSource.rotation;
        }

        return null;
    }

    public void RequestLocalization()
    {
#if UNITY_EDITOR
        if (simulateInEditor)
        {
            SetPosition(simulatedPosition, Quaternion.identity, "EditorSimulation");
            return;
        }
#endif

        ResolveReferences();

        bool configuredAnyManager = false;

        if (mapLocalizationManager != null)
        {
            ConfigureManagerMapCode(mapLocalizationManager, mapCode);
            configuredAnyManager = TryInvokeMethod(mapLocalizationManager, "ValidateMapOrMapSetCode", mapCode) || configuredAnyManager;
            configuredAnyManager = TryInvokeMethod(mapLocalizationManager, "LocalizeFrame") || configuredAnyManager;
        }

        if (singleFrameLocalizationManager != null)
        {
            ConfigureManagerMapCode(singleFrameLocalizationManager, mapCode);
            configuredAnyManager = TryInvokeMethod(singleFrameLocalizationManager, "ValidateMapOrMapSetCode", mapCode) || configuredAnyManager;
            configuredAnyManager = TryInvokeMethod(singleFrameLocalizationManager, "LocalizeFrame") || configuredAnyManager;
        }

        if (onDeviceLocalizationManager != null)
        {
            ConfigureManagerMapCode(onDeviceLocalizationManager, mapCode);
            configuredAnyManager = TryInvokeMethod(onDeviceLocalizationManager, "ValidateMapOrMapSetCode", mapCode) || configuredAnyManager;
            configuredAnyManager = TryInvokeMethod(onDeviceLocalizationManager, "LocalizeFrame") || configuredAnyManager;
        }

        if (!configuredAnyManager)
        {
            Debug.LogWarning("[LocalizationWrapper] No MultiSet localization manager was configured.");
            OnLocalizationFailed?.Invoke();
        }
    }

    public void SetMapCode(string code)
    {
        mapCode = code;
    }

    public void UpdateFromMultiSet(Vector3 multisetPosition, Quaternion multisetRotation, string locationId = "")
    {
        Vector3 offsetPosition = multisetPosition + positionOffset;
        Quaternion offsetRotation = Quaternion.Euler(rotationOffsetEuler) * multisetRotation;
        SetPosition(offsetPosition, offsetRotation, locationId);
    }

    public void SetPosition(Vector3 position, Quaternion rotation, string locationId = "")
    {
        currentPosition = position;
        currentRotation = rotation;
        currentLocationId = locationId;
        lastUpdateTime = Time.time;

        if (!isLocalized)
        {
            isLocalized = true;
            OnLocalizationStateChanged?.Invoke(true);
        }

        OnLocationChanged?.Invoke(currentLocationId, currentPosition);

        if (debugMode)
        {
            Debug.Log($"[LocalizationWrapper] Pose updated at {currentPosition}");
        }
    }

    public void ResetLocalization()
    {
        isLocalized = false;
        currentLocationId = string.Empty;
        OnLocalizationStateChanged?.Invoke(false);
    }

    public bool IsLocalizationRecent(float timeoutSeconds = 10f)
    {
        return (Time.time - lastUpdateTime) < timeoutSeconds;
    }

    public string GetCurrentLocationName()
    {
        return currentLocationId;
    }

    [ContextMenu("Test: Request Localization")]
    public void TestRequestLocalization()
    {
        RequestLocalization();
    }

    [ContextMenu("Test: Set Simulated Position")]
    public void SetTestPosition()
    {
        SetPosition(simulatedPosition, Quaternion.identity, "Test");
    }

    private void ResolveReferences()
    {
        if (mapLocalizationManager == null)
        {
            mapLocalizationManager = FindFirstObjectByType<MapLocalizationManager>();
        }

        if (singleFrameLocalizationManager == null)
        {
            singleFrameLocalizationManager = FindFirstObjectByType<SingleFrameLocalizationManager>();
        }

        if (trackedPoseSource == null && Camera.main != null)
        {
            trackedPoseSource = Camera.main.transform;
        }
    }

    private void SubscribeToMultiSetEvents()
    {
        if (mapLocalizationManager != null)
        {
            mapLocalizationManager.OnLocalizationWithResponse -= HandleMultiFrameLocalization;
            mapLocalizationManager.OnLocalizationWithResponse += HandleMultiFrameLocalization;
        }

        if (singleFrameLocalizationManager != null)
        {
            singleFrameLocalizationManager.OnLocalizationWithResponse -= HandleSingleFrameLocalization;
            singleFrameLocalizationManager.OnLocalizationWithResponse += HandleSingleFrameLocalization;
        }
    }

    private void UnsubscribeFromMultiSetEvents()
    {
        if (mapLocalizationManager != null)
        {
            mapLocalizationManager.OnLocalizationWithResponse -= HandleMultiFrameLocalization;
        }

        if (singleFrameLocalizationManager != null)
        {
            singleFrameLocalizationManager.OnLocalizationWithResponse -= HandleSingleFrameLocalization;
        }
    }

    private void HandleSingleFrameLocalization(LocalizationSuccessResponse response)
    {
        if (TryExtractPose(response, out Vector3 position, out Quaternion rotation))
        {
            UpdateFromMultiSet(position, rotation, ExtractLocationId(response));
            return;
        }

        MarkLocalizedFromTrackedSource("SingleFrame");
    }

    private void HandleMultiFrameLocalization(LocalizationResponseMultiFrame response)
    {
        if (TryExtractPose(response, out Vector3 position, out Quaternion rotation))
        {
            UpdateFromMultiSet(position, rotation, ExtractLocationId(response));
            return;
        }

        MarkLocalizedFromTrackedSource("MultiFrame");
    }

    private void MarkLocalizedFromTrackedSource(string locationId)
    {
        if (trackedPoseSource == null)
        {
            OnLocalizationFailed?.Invoke();
            return;
        }

        ApplyTrackedSourcePose(locationId);
    }

    private void ApplyTrackedSourcePose(string locationId)
    {
        Vector3 position = trackedPoseSource.position + positionOffset;
        Quaternion rotation = Quaternion.Euler(rotationOffsetEuler) * trackedPoseSource.rotation;
        SetPosition(position, rotation, locationId);
    }

    private bool TryExtractPose(object source, out Vector3 position, out Quaternion rotation)
    {
        position = Vector3.zero;
        rotation = Quaternion.identity;

        if (TryGetPoseMembers(source, out position, out rotation))
        {
            return true;
        }

        foreach (string nestedMember in new[] { "estimatedPose", "trackingPose", "pose" })
        {
            object nestedValue = GetMemberValue(source, nestedMember);
            if (nestedValue != null && TryGetPoseMembers(nestedValue, out position, out rotation))
            {
                return true;
            }
        }

        return false;
    }

    private bool TryGetPoseMembers(object source, out Vector3 position, out Quaternion rotation)
    {
        position = Vector3.zero;
        rotation = Quaternion.identity;

        object rawPosition = GetMemberValue(source, "position");
        object rawRotation = GetMemberValue(source, "rotation");

        if (TryConvertVector3(rawPosition, out position) && TryConvertQuaternion(rawRotation, out rotation))
        {
            return true;
        }

        return false;
    }

    private string ExtractLocationId(object source)
    {
        object mapCodes = GetMemberValue(source, "mapCodes");
        if (mapCodes is System.Collections.IEnumerable sequence)
        {
            foreach (object item in sequence)
            {
                if (item != null)
                {
                    return item.ToString();
                }
            }
        }

        return string.Empty;
    }

    private object GetMemberValue(object source, string memberName)
    {
        if (source == null)
        {
            return null;
        }

        Type type = source.GetType();
        PropertyInfo property = type.GetProperty(memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (property != null)
        {
            return property.GetValue(source);
        }

        FieldInfo field = type.GetField(memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        return field?.GetValue(source);
    }

    private bool TryConvertVector3(object rawValue, out Vector3 vector)
    {
        vector = Vector3.zero;

        if (rawValue == null)
        {
            return false;
        }

        if (rawValue is Vector3 unityVector)
        {
            vector = unityVector;
            return true;
        }

        if (rawValue is float[] floatArray && floatArray.Length >= 3)
        {
            vector = new Vector3(floatArray[0], floatArray[1], floatArray[2]);
            return true;
        }

        if (rawValue is double[] doubleArray && doubleArray.Length >= 3)
        {
            vector = new Vector3((float)doubleArray[0], (float)doubleArray[1], (float)doubleArray[2]);
            return true;
        }

        Type valueType = rawValue.GetType();
        object x = GetMemberValue(rawValue, "x");
        object y = GetMemberValue(rawValue, "y");
        object z = GetMemberValue(rawValue, "z");

        if (x != null && y != null && z != null)
        {
            vector = new Vector3(Convert.ToSingle(x), Convert.ToSingle(y), Convert.ToSingle(z));
            return true;
        }

        if (debugMode)
        {
            Debug.Log($"[LocalizationWrapper] Could not parse Vector3 from {valueType.Name}");
        }

        return false;
    }

    private bool TryConvertQuaternion(object rawValue, out Quaternion quaternion)
    {
        quaternion = Quaternion.identity;

        if (rawValue == null)
        {
            return false;
        }

        if (rawValue is Quaternion unityQuaternion)
        {
            quaternion = unityQuaternion;
            return true;
        }

        if (rawValue is float[] floatArray && floatArray.Length >= 4)
        {
            quaternion = new Quaternion(floatArray[0], floatArray[1], floatArray[2], floatArray[3]);
            return true;
        }

        if (rawValue is double[] doubleArray && doubleArray.Length >= 4)
        {
            quaternion = new Quaternion((float)doubleArray[0], (float)doubleArray[1], (float)doubleArray[2], (float)doubleArray[3]);
            return true;
        }

        object x = GetMemberValue(rawValue, "x") ?? GetMemberValue(rawValue, "qx");
        object y = GetMemberValue(rawValue, "y") ?? GetMemberValue(rawValue, "qy");
        object z = GetMemberValue(rawValue, "z") ?? GetMemberValue(rawValue, "qz");
        object w = GetMemberValue(rawValue, "w") ?? GetMemberValue(rawValue, "qw");

        if (x != null && y != null && z != null && w != null)
        {
            quaternion = new Quaternion(Convert.ToSingle(x), Convert.ToSingle(y), Convert.ToSingle(z), Convert.ToSingle(w));
            return true;
        }

        return false;
    }

    private void ConfigureManagerMapCode(object manager, string code)
    {
        if (manager == null || string.IsNullOrWhiteSpace(code))
        {
            return;
        }

        SetMemberIfExists(manager, "mapOrMapsetCode", code);
        SetMemberIfExists(manager, "mapCode", code);
    }

    private void SetMemberIfExists(object target, string memberName, object value)
    {
        Type type = target.GetType();

        PropertyInfo property = type.GetProperty(memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (property != null && property.CanWrite)
        {
            property.SetValue(target, value);
            return;
        }

        FieldInfo field = type.GetField(memberName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        field?.SetValue(target, value);
    }

    private bool TryInvokeMethod(object target, string methodName, params object[] args)
    {
        if (target == null)
        {
            return false;
        }

        MethodInfo method = target.GetType().GetMethod(methodName, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
        if (method == null)
        {
            return false;
        }

        method.Invoke(target, args);
        return true;
    }

    private void OnDestroy()
    {
        UnsubscribeFromMultiSetEvents();

        if (_instance == this)
        {
            _instance = null;
        }
    }
}
