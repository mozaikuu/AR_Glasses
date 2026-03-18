using UnityEngine;

/// <summary>
/// Renders the navigation path using Unity's LineRenderer and NavMeshAgent path corners.
/// </summary>
[RequireComponent(typeof(LineRenderer))]
public class PathRenderer : MonoBehaviour
{
  [Header("Configuration")]
  [SerializeField] private bool showPath = true;
  [SerializeField] private float pathHeightOffset = 0.1f; // Height above ground

  [Header("Line Settings")]
  [SerializeField] private Color pathColor = Color.green;
  [SerializeField] private Color pathColorPartial = Color.yellow;
  [SerializeField] private float lineWidth = 0.1f;
  [SerializeField] private float lineWidthEnd = 0.05f;

  [Header("References")]
  [SerializeField] private UnityEngine.AI.NavMeshAgent navMeshAgent;

  private LineRenderer lineRenderer;
  private bool isEnabled = true;
  private Vector3[] currentCorners = new Vector3[0];

  private void Awake()
  {
    // Get or add LineRenderer component
    lineRenderer = GetComponent<LineRenderer>();

    ConfigureLineRenderer();
  }

  private void Start()
  {
    // Auto-find NavMeshAgent if not assigned
    if (navMeshAgent == null)
      navMeshAgent = FindObjectOfType<UnityEngine.AI.NavMeshAgent>();
  }

  private void ConfigureLineRenderer()
  {
    lineRenderer.positionCount = 0;
    lineRenderer.startWidth = lineWidth;
    lineRenderer.endWidth = lineWidthEnd;
    lineRenderer.material = new Material(Shader.Find("Sprites/Default"));
    lineRenderer.startColor = pathColor;
    lineRenderer.endColor = pathColor;
    lineRenderer.useWorldSpace = true;
    lineRenderer.enabled = showPath;
  }

  /// <summary>
  /// Enable or disable path rendering.
  /// </summary>
  public void SetEnabled(bool enabled)
  {
    isEnabled = enabled;
    lineRenderer.enabled = enabled && showPath;
  }

  /// <summary>
  /// Update path visibility.
  /// </summary>
  public void SetShowPath(bool show)
  {
    showPath = show;
    lineRenderer.enabled = isEnabled && show;
  }

  private void Update()
  {
    if (!isEnabled || !showPath || navMeshAgent == null)
    {
      if (lineRenderer.positionCount > 0)
      {
        lineRenderer.positionCount = 0;
      }
      return;
    }

    // Check if agent has a path
    if (!navMeshAgent.hasPath)
    {
      if (lineRenderer.positionCount > 0)
      {
        lineRenderer.positionCount = 0;
      }
      return;
    }

    // Get path corners from NavMeshAgent
    Vector3[] corners = navMeshAgent.path.corners;

    // Check if corners changed
    if (CornersChanged(corners))
    {
      currentCorners = corners;
      DrawPath(corners);
    }
  }

  private bool CornersChanged(Vector3[] newCorners)
  {
    if (newCorners.Length != currentCorners.Length)
      return true;

    for (int i = 0; i < newCorners.Length; i++)
    {
      if (Vector3.SqrMagnitude(newCorners[i] - currentCorners[i]) > 0.001f)
        return true;
    }

    return false;
  }

  private void DrawPath(Vector3[] corners)
  {
    if (corners.Length < 2)
    {
      lineRenderer.positionCount = 0;
      return;
    }

    lineRenderer.positionCount = corners.Length;

    // Draw path with height offset to prevent z-fighting
    for (int i = 0; i < corners.Length; i++)
    {
      Vector3 point = corners[i];
      point.y += pathHeightOffset;
      lineRenderer.SetPosition(i, point);
    }

    // Gradient effect - destination is different color
    if (corners.Length >= 2)
    {
      lineRenderer.startColor = pathColor;
      lineRenderer.endColor = pathColorPartial;
    }
  }

  /// <summary>
  /// Draw a static path (for testing or preview).
  /// </summary>
  public void DrawStaticPath(Vector3[] positions)
  {
    if (positions.Length < 2)
    {
      lineRenderer.positionCount = 0;
      return;
    }

    lineRenderer.positionCount = positions.Length;

    for (int i = 0; i < positions.Length; i++)
    {
      Vector3 point = positions[i];
      point.y += pathHeightOffset;
      lineRenderer.SetPosition(i, point);
    }

    lineRenderer.startColor = pathColor;
    lineRenderer.endColor = pathColorPartial;
  }

  /// <summary>
  /// Clear the path visualization.
  /// </summary>
  public void ClearPath()
  {
    lineRenderer.positionCount = 0;
    currentCorners = new Vector3[0];
  }

  /// <summary>
  /// Set path colors.
  /// </summary>
  public void SetColors(Color start, Color end)
  {
    pathColor = start;
    pathColorPartial = end;
    lineRenderer.startColor = start;
    lineRenderer.endColor = end;
  }

  /// <summary>
  /// Set line width.
  /// </summary>
  public void SetWidth(float width)
  {
    lineWidth = width;
    lineRenderer.startWidth = width;
    lineRenderer.endWidth = width * 0.5f;
  }

  /// <summary>
  /// Get current path corners.
  /// </summary>
  public Vector3[] GetCurrentCorners()
  {
    return currentCorners;
  }

  /// <summary>
  /// Get the next corner position (for avatar guidance).
  /// </summary>
  public Vector3? GetNextCorner()
  {
    if (currentCorners.Length > 1)
      return currentCorners[1]; // Index 0 is current position

    return null;
  }

  /// <summary>
  /// Get remaining corners count.
  /// </summary>
  public int GetRemainingCornersCount()
  {
    // This is simplified - could track which corner we're at
    return currentCorners.Length;
  }
}
