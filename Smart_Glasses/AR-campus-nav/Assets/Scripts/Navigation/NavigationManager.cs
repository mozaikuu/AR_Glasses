using System;
using System.Collections;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.Networking;

/// <summary>
/// Main navigation controller that handles destination setting and server communication.
/// Uses Unity's built-in NavMesh for pathfinding.
/// </summary>
public class NavigationManager : MonoBehaviour
{
  [Header("Configuration")]
  [SerializeField] private string serverBaseUrl = "http://localhost:8000";
  [SerializeField] private float serverTimeout = 10f;
  [SerializeField] private bool warpGuideAgentToLocalizedStart = true;
  [SerializeField] private float localizedStartSampleDistance = 2.0f;

  [Header("References")]
  [SerializeField] public NavMeshAgent navMeshAgent;
  [SerializeField] private PathRenderer pathRenderer;
  [SerializeField] private VoiceGuide voiceGuide;
  [SerializeField] private LocalizationWrapper localization;

  // Navigation state
  private bool isNavigating = false;
  private string currentDestination = "";
  private Vector3? userStartPosition;

  // Events for UI and other systems
  public event Action<string> OnNavigationStarted;
  public event Action OnNavigationCompleted;
  public event Action<string> OnNavigationError;

  // Properties
  public bool IsNavigating => isNavigating;
  public string CurrentDestination => currentDestination;
  public Vector3? UserStartPosition => userStartPosition;

  private void Awake()
  {
    // Auto-find components if not assigned
    if (navMeshAgent == null)
      navMeshAgent = GetComponent<NavMeshAgent>();

    if (pathRenderer == null)
      pathRenderer = FindFirstObjectByType<PathRenderer>();

    if (voiceGuide == null)
      voiceGuide = FindFirstObjectByType<VoiceGuide>();

    if (localization == null)
      localization = FindFirstObjectByType<LocalizationWrapper>();
  }

  /// <summary>
  /// Test navigation in Editor - call from Inspector button
  /// </summary>
  [ContextMenu("Test: Navigate to TA_Office")]
  public void TestNavigateToTAOffice()
  {
    Debug.Log("[NavigationManager] Test: Navigating to TA_Office");
    NavigateTo("TA_Office");
  }

  [ContextMenu("Test: Navigate to Entrance")]
  public void TestNavigateToEntrance()
  {
    Debug.Log("[NavigationManager] Test: Navigating to Entrance");
    NavigateTo("Entrance");
  }

  [ContextMenu("Test: Navigate to Stairs_G")]
  public void TestNavigateToStairs()
  {
    Debug.Log("[NavigationManager] Test: Navigating to Stairs_G");
    NavigateTo("Stairs_G");
  }

  [ContextMenu("Stop Navigation")]
  public void TestStopNavigation()
  {
    Debug.Log("[NavigationManager] Test: Stopping navigation");
    CancelNavigation();
  }

  /// <summary>
  /// Navigate to a destination by name.
  /// Unity's NavMesh will automatically calculate the path.
  /// </summary>
  /// <param name="destinationName">Name of the destination GameObject</param>
  public void NavigateTo(string destinationName)
  {
    if (string.IsNullOrEmpty(destinationName))
    {
      OnNavigationError?.Invoke("Destination name is empty");
      return;
    }

    // Find the target GameObject
    GameObject target = GameObject.Find(destinationName);

    if (target == null)
    {
      // Try with underscores replaced
      target = GameObject.Find(destinationName.Replace(" ", "_"));

      if (target == null)
      {
        string error = $"Destination '{destinationName}' not found in scene";
        Debug.LogError($"[NavigationManager] {error}");
        OnNavigationError?.Invoke(error);
        return;
      }
    }

    StartNavigation(target.transform.position, destinationName);
  }

  /// <summary>
  /// Navigate to a specific position.
  /// </summary>
  /// <param name="position">Target position in world space</param>
  /// <param name="destinationName">Name for logging purposes</param>
  public void NavigateToPosition(Vector3 position, string destinationName = "Unknown")
  {
    StartNavigation(position, destinationName);
  }

  /// <summary>
  /// Start navigation to a position.
  /// </summary>
  private void StartNavigation(Vector3 targetPosition, string destinationName)
  {
    if (navMeshAgent == null)
    {
      OnNavigationError?.Invoke("NavMeshAgent not found");
      return;
    }

    // Stop any existing navigation
    navMeshAgent.ResetPath();

    // Get user position from localization if available
    if (localization != null)
    {
      Vector3? localizedPos = localization.GetUserPosition();
      if (localizedPos.HasValue)
      {
        userStartPosition = localizedPos.Value;
      }
    }

    // Keep the guide capsule aligned with where localization says the user currently is.
    if (warpGuideAgentToLocalizedStart)
    {
      TryWarpAgentToLocalizedStart();
    }

    // Set destination - Unity's NavMesh calculates path automatically
    navMeshAgent.isStopped = false;
    bool setDestinationOk = navMeshAgent.SetDestination(targetPosition);
    if (!setDestinationOk)
    {
      string error = $"Could not set destination '{destinationName}' on NavMesh.";
      Debug.LogError($"[NavigationManager] {error}");
      OnNavigationError?.Invoke(error);
      return;
    }

    currentDestination = destinationName;
    isNavigating = true;

    Debug.Log($"[NavigationManager] Started navigation to '{destinationName}' at {targetPosition}");

    // Notify components
    OnNavigationStarted?.Invoke(destinationName);

    // Enable path rendering
    if (pathRenderer != null)
    {
      pathRenderer.SetEnabled(true);
    }

    // Enable voice guidance
    if (voiceGuide != null)
    {
      voiceGuide.SetEnabled(true);
    }
  }

  /// <summary>
  /// Navigate to destination via server (for voice command integration).
  /// Server just returns destination name, Unity calculates path.
  /// </summary>
  /// <param name="destination">Destination from server response</param>
  public void NavigateFromServer(string destination)
  {
    NavigateTo(destination);
  }

  /// <summary>
  /// Ask server to resolve a natural language destination, then navigate locally on NavMesh.
  /// </summary>
  public void NavigateFromPrompt(string destinationPrompt)
  {
    if (string.IsNullOrWhiteSpace(destinationPrompt))
    {
      OnNavigationError?.Invoke("Destination prompt is empty");
      return;
    }

    string startLocation = localization != null ? localization.GetCurrentLocationName() : string.Empty;
    StartCoroutine(RequestNavigationFromServer(startLocation, destinationPrompt));
  }

  /// <summary>
  /// Call server to get navigation (if voice command was used).
  /// For now, server just returns the destination - we handle pathfinding locally.
  /// </summary>
  public IEnumerator RequestNavigationFromServer(string startLocation, string destination)
  {
    string url = $"{serverBaseUrl}/navigate";

    string jsonBody = JsonUtility.ToJson(new NavigateRequest
    {
      destination = destination,
      start = startLocation
    });

    using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
    {
      byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(jsonBody);
      request.uploadHandler = new UploadHandlerRaw(bodyRaw);
      request.downloadHandler = new DownloadHandlerBuffer();
      request.timeout = Mathf.CeilToInt(serverTimeout);
      request.SetRequestHeader("Content-Type", "application/json");

      yield return request.SendWebRequest();

      if (request.result == UnityWebRequest.Result.Success)
      {
        string responseText = request.downloadHandler.text;
        Debug.Log($"[NavigationManager] Server response: {responseText}");

        // Parse response - server just echoes the destination
        var response = JsonUtility.FromJson<NavigateResponse>(responseText);

        if (response != null && !string.IsNullOrEmpty(response.destination))
        {
          NavigateTo(response.destination);
        }
        else
        {
          OnNavigationError?.Invoke("Invalid server response");
        }
      }
      else
      {
        string error = $"Server request failed: {request.error}";
        Debug.LogError($"[NavigationManager] {error}");
        OnNavigationError?.Invoke(error);
      }
    }
  }

  private void TryWarpAgentToLocalizedStart()
  {
    if (navMeshAgent == null || localization == null)
      return;

    Vector3? localizedPos = localization.GetUserPosition();
    if (!localizedPos.HasValue)
      return;

    if (NavMesh.SamplePosition(localizedPos.Value, out NavMeshHit hit, localizedStartSampleDistance, NavMesh.AllAreas))
    {
      navMeshAgent.Warp(hit.position);
    }
  }

  /// <summary>
  /// Cancel current navigation.
  /// </summary>
  public void CancelNavigation()
  {
    if (navMeshAgent != null && isNavigating)
    {
      navMeshAgent.ResetPath();
    }

    isNavigating = false;
    currentDestination = "";
    userStartPosition = null;

    // Disable components
    if (pathRenderer != null)
      pathRenderer.SetEnabled(false);

    if (voiceGuide != null)
      voiceGuide.SetEnabled(false);

    Debug.Log("[NavigationManager] Navigation cancelled");
  }

  /// <summary>
  /// Get all available navigation targets in the scene.
  /// </summary>
  public string[] GetAvailableDestinations()
  {
    // Find all objects tagged as "NavigationTarget" or in "NavigationTargets" folder
    GameObject[] allObjects = FindObjectsOfType<GameObject>();
    var destinations = new System.Collections.Generic.List<string>();

    foreach (GameObject obj in allObjects)
    {
      if (obj.transform.parent != null && obj.transform.parent.name == "NavigationTargets")
      {
        destinations.Add(obj.name);
      }
      else if (obj.CompareTag("NavigationTarget"))
      {
        destinations.Add(obj.name);
      }
    }

    return destinations.ToArray();
  }

  /// <summary>
  /// Get current navigation progress (0-1).
  /// </summary>
  public float GetProgress()
  {
    if (navMeshAgent == null || !navMeshAgent.hasPath)
      return 0f;

    float pathLength = GetPathLength();
    float remainingDistance = navMeshAgent.remainingDistance;

    if (pathLength <= 0)
      return 0f;

    return 1f - (remainingDistance / pathLength);
  }

  /// <summary>
  /// Get total path length.
  /// </summary>
  public float GetPathLength()
  {
    if (navMeshAgent == null || !navMeshAgent.hasPath)
      return 0f;

    // Calculate path length from corners
    Vector3[] corners = navMeshAgent.path.corners;
    if (corners.Length < 2)
      return 0f;

    float totalDistance = 0f;
    for (int i = 0; i < corners.Length - 1; i++)
    {
      totalDistance += Vector3.Distance(corners[i], corners[i + 1]);
    }

    return totalDistance;
  }

  private void Update()
  {
    if (isNavigating && navMeshAgent != null)
    {
      // Check if arrived
      if (navMeshAgent.remainingDistance <= navMeshAgent.stoppingDistance && navMeshAgent.pathStatus == NavMeshPathStatus.PathComplete)
      {
        OnArrived();
      }
    }
  }

  private void OnArrived()
  {
    isNavigating = false;

    Debug.Log($"[NavigationManager] Arrived at '{currentDestination}'");

    // Disable components
    if (pathRenderer != null)
      pathRenderer.SetEnabled(false);

    // Play arrival message
    if (voiceGuide != null)
    {
      voiceGuide.PlayArrivalMessage(currentDestination);
      voiceGuide.SetEnabled(false);
    }

    OnNavigationCompleted?.Invoke();
  }

  // Request/Response classes for server communication
  [Serializable]
  private class NavigateRequest
  {
    public string destination;
    public string start;
  }

  [Serializable]
  private class NavigateResponse
  {
    public string destination;
  }
}
