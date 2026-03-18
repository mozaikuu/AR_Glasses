using UnityEngine;
using UnityEngine.AI;

/// <summary>
/// Helper script to set up navigation targets in the scene.
/// Attach to an empty GameObject and configure in Inspector.
/// </summary>
public class NavigationSetup : MonoBehaviour
{
  [Header("Navigation Agent")]
  [SerializeField] private GameObject agentObject;
  [SerializeField] private float agentSpeed = 3.5f;
  [SerializeField] private float agentAngularSpeed = 120f;

  [Header("Path Rendering")]
  [SerializeField] private bool enablePathRendering = true;
  [SerializeField] private Color pathColor = Color.green;
  [SerializeField] private float pathWidth = 0.1f;

  [Header("Voice Guidance")]
  [SerializeField] private bool enableVoiceGuidance = true;
  [SerializeField] private float turnThreshold = 30f;

  [Header("Navigation Targets")]
  [SerializeField]
  private string[] targetNames = new string[]
  {
        "Entrance",
        "TA_Office",
        "Stairs_G",
        "Floor_1",
        "Elevator"
  };

  [Header("References (Auto-Find)")]
  [SerializeField] private NavigationManager navigationManager;
  [SerializeField] private PathRenderer pathRenderer;
  [SerializeField] private VoiceGuide voiceGuide;
  [SerializeField] private LocalizationWrapper localization;

  /// <summary>
  /// Set up the navigation system automatically.
  /// </summary>
  [ContextMenu("Setup Navigation")]
  public void SetupNavigation()
  {
    SetupAgent();
    SetupPathRenderer();
    SetupVoiceGuide();
    SetupLocalization();
    CreateNavigationTargets();

    Debug.Log("[NavigationSetup] Navigation system set up complete!");
  }

  private void SetupAgent()
  {
    if (agentObject == null)
    {
      // Try to find existing agent
      NavMeshAgent existingAgent = FindObjectOfType<NavMeshAgent>();

      if (existingAgent != null)
      {
        agentObject = existingAgent.gameObject;
      }
      else
      {
        // Create new agent
        agentObject = new GameObject("NavigationAgent");
        agentObject.transform.SetParent(transform);

        NavMeshAgent newAgent = agentObject.AddComponent<NavMeshAgent>();
        newAgent.speed = agentSpeed;
        newAgent.angularSpeed = agentAngularSpeed;

        // Add capsule for visual representation
        GameObject capsule = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        capsule.transform.SetParent(agentObject.transform);
        capsule.transform.localPosition = new Vector3(0, 1, 0);
      }
    }

    // Get or add NavigationManager
    navigationManager = agentObject.GetComponent<NavigationManager>();
    if (navigationManager == null)
    {
      navigationManager = agentObject.AddComponent<NavigationManager>();
    }

    // Configure NavigationManager
    navigationManager.navMeshAgent = agentObject.GetComponent<NavMeshAgent>();

    Debug.Log("[NavigationSetup] Agent configured");
  }

  private void SetupPathRenderer()
  {
    if (!enablePathRendering) return;

    // Try to find existing PathRenderer
    pathRenderer = FindObjectOfType<PathRenderer>();

    if (pathRenderer == null && agentObject != null)
    {
      // Add PathRenderer to agent
      pathRenderer = agentObject.AddComponent<PathRenderer>();
    }

    if (pathRenderer != null)
    {
      pathRenderer.SetShowPath(true);
      pathRenderer.SetColors(pathColor, Color.yellow);
      pathRenderer.SetWidth(pathWidth);
    }

    // Link to NavigationManager
    if (navigationManager != null)
    {
      // reflection or direct reference
    }

    Debug.Log("[NavigationSetup] PathRenderer configured");
  }

  private void SetupVoiceGuide()
  {
    if (!enableVoiceGuidance) return;

    // Try to find existing VoiceGuide
    voiceGuide = FindObjectOfType<VoiceGuide>();

    if (voiceGuide == null && agentObject != null)
    {
      // Add VoiceGuide to agent
      voiceGuide = agentObject.AddComponent<VoiceGuide>();
    }

    if (voiceGuide != null)
    {
      voiceGuide.SetEnabled(true);
      // Set turn threshold via reflection or public property
    }

    Debug.Log("[NavigationSetup] VoiceGuide configured");
  }

  private void SetupLocalization()
  {
    // Try to find existing LocalizationWrapper
    localization = FindObjectOfType<LocalizationWrapper>();

    if (localization == null)
    {
      // Add to main camera or create new
      GameObject locObj = new GameObject("LocalizationWrapper");
      localization = locObj.AddComponent<LocalizationWrapper>();
    }

    Debug.Log("[NavigationSetup] Localization configured");
  }

  private void CreateNavigationTargets()
  {
    // Create or verify NavigationTargets folder
    GameObject targetsFolder = GameObject.Find("NavigationTargets");

    if (targetsFolder == null)
    {
      targetsFolder = new GameObject("NavigationTargets");
    }

    foreach (string targetName in targetNames)
    {
      GameObject existingTarget = GameObject.Find(targetName);

      if (existingTarget == null)
      {
        GameObject target = new GameObject(targetName);
        target.transform.SetParent(targetsFolder.transform);

        // Add NavigationTarget tag if needed
        // target.tag = "NavigationTarget";

        Debug.Log($"[NavigationSetup] Created target: {targetName}");
      }
      else
      {
        Debug.Log($"[NavigationSetup] Found existing target: {targetName}");
      }
    }

    Debug.Log($"[NavigationSetup] Created {targetNames.Length} navigation targets");
  }

  /// <summary>
  /// Quick test - navigate to first target.
  /// </summary>
  [ContextMenu("Test Navigation")]
  public void TestNavigation()
  {
    if (navigationManager != null && targetNames.Length > 0)
    {
      navigationManager.NavigateTo(targetNames[0]);
      Debug.Log($"[NavigationSetup] Testing navigation to: {targetNames[0]}");
    }
  }

  /// <summary>
  /// Get all available destinations.
  /// </summary>
  public string[] GetDestinations()
  {
    return targetNames;
  }
}
