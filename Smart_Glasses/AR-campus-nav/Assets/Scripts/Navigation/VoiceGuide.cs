using System;
using UnityEngine;
using UnityEngine.AI;

/// <summary>
/// Provides voice guidance by computing turn instructions from NavMesh path corners.
/// Uses MRTK TextToSpeech or Windows Speech for audio output.
/// </summary>
public class VoiceGuide : MonoBehaviour
{
  [Header("Configuration")]
  [SerializeField] private bool enabled = true;
  [SerializeField] private float turnThresholdAngle = 30f; // Angle to trigger turn instruction
  [SerializeField] private float distanceToTriggerTurn = 2f; // Distance from corner to trigger

  [Header("Voice Settings")]
  [SerializeField] private bool useMrtkSpeech = true; // Use MRTK TextToSpeech if available
  [SerializeField] private float speechRate = 1.0f; // Speech rate (0.1 - 2.0)

  [Header("References")]
  [SerializeField] private NavMeshAgent navMeshAgent;

  // State
  private bool isEnabled = true;
  private int currentCornerIndex = 0;
  private Vector3[] currentCorners = new Vector3[0];
  private bool hasPlayedStartMessage = false;
  private bool hasPlayedArrivalMessage = false;

  // Track direction changes
  private Vector3 lastDirection;
  private bool directionTracked = false;

  // Events
  public event Action<string> OnInstructionPlay;

  private void Awake()
  {
    // Auto-find NavMeshAgent if not assigned
    if (navMeshAgent == null)
      navMeshAgent = GetComponent<NavMeshAgent>();
  }

  /// <summary>
  /// Enable or disable voice guidance.
  /// </summary>
  public void SetEnabled(bool enabled)
  {
    isEnabled = enabled;
  }

  /// <summary>
  /// Play a custom message.
  /// </summary>
  public void PlayMessage(string message)
  {
    if (!isEnabled || string.IsNullOrEmpty(message))
      return;

    Debug.Log($"[VoiceGuide] Playing: {message}");

    // Use MRTK TextToSpeech if available
    if (useMrtkSpeech)
    {
      PlayMrtkSpeech(message);
    }
    else
    {
      // Fallback to Windows Speech
      PlayWindowsSpeech(message);
    }

    OnInstructionPlay?.Invoke(message);
  }

  /// <summary>
  /// Play arrival message.
  /// </summary>
  public void PlayArrivalMessage(string destinationName)
  {
    if (hasPlayedArrivalMessage)
      return;

    hasPlayedArrivalMessage = true;

    string message = $"You have arrived at {FormatDestinationName(destinationName)}";
    PlayMessage(message);
  }

  /// <summary>
  /// Reset for new navigation.
  /// </summary>
  public void Reset()
  {
    currentCornerIndex = 0;
    directionTracked = false;
    hasPlayedStartMessage = false;
    hasPlayedArrivalMessage = false;
    lastDirection = Vector3.zero;
  }

  private void Update()
  {
    if (!isEnabled || !enabled || navMeshAgent == null)
      return;

    // Check if agent has a path
    if (!navMeshAgent.hasPath)
    {
      Reset();
      return;
    }

    Vector3[] corners = navMeshAgent.path.corners;

    // Check if path changed
    if (corners.Length != currentCorners.Length)
    {
      OnPathChanged(corners);
      return;
    }

    // Check distance to next corner
    CheckNextCorner(corners);
  }

  private void OnPathChanged(Vector3[] newCorners)
  {
    currentCorners = newCorners;
    currentCornerIndex = 0;
    directionTracked = false;
    hasPlayedStartMessage = false;
    hasPlayedArrivalMessage = false;

    if (newCorners.Length > 1 && !hasPlayedStartMessage)
    {
      // Get initial direction
      lastDirection = (newCorners[1] - newCorners[0]).normalized;
      directionTracked = true;
    }
  }

  private void CheckNextCorner(Vector3[] corners)
  {
    if (corners.Length < 2)
      return;

    // Check if we've reached the destination (last corner)
    if (navMeshAgent.remainingDistance <= navMeshAgent.stoppingDistance)
    {
      if (!hasPlayedArrivalMessage)
      {
        PlayArrivalMessage("your destination");
      }
      return;
    }

    // Get next corner index
    int nextCornerIndex = Math.Min(currentCornerIndex + 1, corners.Length - 1);

    if (nextCornerIndex <= currentCornerIndex)
      return;

    Vector3 currentPosition = navMeshAgent.transform.position;
    Vector3 nextCorner = corners[nextCornerIndex];
    float distanceToCorner = Vector3.Distance(currentPosition, nextCorner);

    // Check if approaching a corner
    if (distanceToCorner <= distanceToTriggerTurn && nextCornerIndex > currentCornerIndex)
    {
      // Calculate turn angle
      Vector3 currentDirection = (nextCorner - currentPosition).normalized;

      if (directionTracked)
      {
        float turnAngle = Vector3.SignedAngle(lastDirection, currentDirection, Vector3.up);

        // Check if significant turn
        if (Mathf.Abs(turnAngle) >= turnThresholdAngle)
        {
          string instruction = GetTurnInstruction(turnAngle);
          PlayMessage(instruction);
        }
      }

      // Update direction and corner index
      lastDirection = currentDirection;
      directionTracked = true;
      currentCornerIndex = nextCornerIndex;
    }
  }

  private string GetTurnInstruction(float angle)
  {
    if (angle > 45f)
      return "Turn right";
    else if (angle < -45f)
      return "Turn left";
    else if (angle > 15f)
      return "Slight right";
    else if (angle < -15f)
      return "Slight left";
    else
      return "Go straight";
  }

  private string FormatDestinationName(string name)
  {
    if (string.IsNullOrEmpty(name))
      return "destination";

    // Replace underscores with spaces
    return name.Replace("_", " ");
  }

  private void PlayMrtkSpeech(string text)
  {
    // Try to use MRTK TextToSpeech if available
    try
    {
      // MRTK 2.x uses TextToSpeechService
      // This is a placeholder - actual implementation depends on MRTK version
      Debug.Log($"[VoiceGuide] MRTK Speech: {text}");

      // For now, we'll use a simple approach
      // In production, integrate with MRTK's TextToSpeech
    }
    catch (Exception e)
    {
      Debug.LogWarning($"[VoiceGuide] MRTK not available: {e.Message}");
      PlayWindowsSpeech(text);
    }
  }

  private void PlayWindowsSpeech(string text)
  {
    // Windows Speech synthesis - requires System.Speech
    // This is a fallback for non-MRTK builds
    Debug.Log($"[VoiceGuide] Windows Speech: {text}");

    // In a full implementation, you would use:
    // using System.Speech.Synthesis;
    // var synth = new SpeechSynthesizer();
    // synth.Speak(text);
  }

  /// <summary>
  /// Test voice guidance with sample instructions.
  /// </summary>
  public void TestVoice()
  {
    PlayMessage("Navigation test. Turn right. Turn left. Go straight. You have arrived.");
  }
}
