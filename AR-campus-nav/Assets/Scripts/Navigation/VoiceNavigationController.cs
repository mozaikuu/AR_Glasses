using System;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;
using LocationInfoSystem;
#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN || UNITY_WSA
using UnityEngine.Windows.Speech;
#endif

/// <summary>
/// Listens for spoken destination requests and starts navigation automatically.
/// Example phrases: "go to math ta office", "take me to entrance".
/// </summary>
public class VoiceNavigationController : MonoBehaviour
{
  [Header("References")]
  [SerializeField] private NavigationManager navigationManager;
  [SerializeField] private VoiceGuide voiceGuide;

  [Header("Server Routing")]
  [SerializeField] private bool useServerCommandRouter = true;
  [SerializeField] private string serverBaseUrl = "http://localhost:8000";
  [SerializeField] private string commandRoutePath = "/unity/voice-command";
  [SerializeField] private string llmMode = "quick";
  [SerializeField] private float requestTimeoutSeconds = 8f;

  [Header("Listening")]
  [SerializeField] private bool autoStartListening = true;
  [SerializeField] private bool restartAfterPhrase = true;

  [Header("Command Parsing")]
  [SerializeField]
  private string[] commandPrefixes = new[]
  {
    "go to",
    "navigate to",
    "take me to",
    "guide me to",
    "i want to go to"
  };

  [Header("Debug")]
  [SerializeField] private bool debugLogs = true;

#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN || UNITY_WSA
  private DictationRecognizer dictationRecognizer;
#endif

  private void Awake()
  {
    if (navigationManager == null)
      navigationManager = FindObjectOfType<NavigationManager>();

    if (voiceGuide == null)
      voiceGuide = FindObjectOfType<VoiceGuide>();
  }

  private void Start()
  {
    if (autoStartListening)
      StartListening();
  }

  private void OnDestroy()
  {
    StopListening();
  }

  [ContextMenu("Voice: Start Listening")]
  public void StartListening()
  {
#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN || UNITY_WSA
    if (dictationRecognizer == null)
    {
      dictationRecognizer = new DictationRecognizer();
      dictationRecognizer.DictationResult += OnDictationResult;
      dictationRecognizer.DictationError += OnDictationError;
      dictationRecognizer.DictationComplete += OnDictationComplete;
      dictationRecognizer.DictationHypothesis += OnDictationHypothesis;
    }

    if (dictationRecognizer.Status == SpeechSystemStatus.Running)
      return;

    dictationRecognizer.Start();
    Log("Voice listening started.");
#else
    Log("Dictation is supported on Windows/HoloLens builds.");
#endif
  }

  [ContextMenu("Voice: Stop Listening")]
  public void StopListening()
  {
#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN || UNITY_WSA
    if (dictationRecognizer == null)
      return;

    if (dictationRecognizer.Status == SpeechSystemStatus.Running)
      dictationRecognizer.Stop();

    dictationRecognizer.DictationResult -= OnDictationResult;
    dictationRecognizer.DictationError -= OnDictationError;
    dictationRecognizer.DictationComplete -= OnDictationComplete;
    dictationRecognizer.DictationHypothesis -= OnDictationHypothesis;
    dictationRecognizer.Dispose();
    dictationRecognizer = null;
#endif
  }

#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN || UNITY_WSA
  private void OnDictationHypothesis(string text)
  {
    if (debugLogs && !string.IsNullOrWhiteSpace(text))
      Debug.Log($"[VoiceNav] Hearing: {text}");
  }

  private void OnDictationResult(string text, ConfidenceLevel confidence)
  {
    if (string.IsNullOrWhiteSpace(text))
      return;

    Log($"Heard: {text}");
    HandleSpokenCommand(text);
  }

  private void OnDictationComplete(DictationCompletionCause cause)
  {
    if (cause != DictationCompletionCause.Complete && cause != DictationCompletionCause.TimeoutExceeded)
      Log($"Dictation completed with cause: {cause}");

    if (restartAfterPhrase)
      StartListening();
  }

  private void OnDictationError(string error, int hresult)
  {
    Debug.LogWarning($"[VoiceNav] Dictation error: {error} (0x{hresult:X})");
    if (restartAfterPhrase)
      StartListening();
  }
#endif

  private void HandleSpokenCommand(string rawText)
  {
    if (useServerCommandRouter)
    {
      StartCoroutine(ProcessWithServerRouter(rawText));
      return;
    }

    if (navigationManager == null)
    {
      Debug.LogWarning("[VoiceNav] NavigationManager reference is missing.");
      return;
    }

    string destinationQuery = ExtractDestination(rawText);
    if (string.IsNullOrWhiteSpace(destinationQuery))
      return;

    if (TryResolveDestination(destinationQuery, out DestinationMatch match))
    {
      if (match.usePosition)
      {
        navigationManager.NavigateToPosition(match.position, match.displayName);
      }
      else
      {
        navigationManager.NavigateTo(match.sceneTargetName);
      }

      voiceGuide?.PlayMessage($"Navigating to {match.displayName}");
      Log($"Matched '{destinationQuery}' -> {match.displayName}");
      return;
    }

    voiceGuide?.PlayMessage("I could not find that destination. Please try again.");
    Log($"No destination match for: {destinationQuery}");
  }

  private System.Collections.IEnumerator ProcessWithServerRouter(string rawText)
  {
    if (navigationManager == null)
    {
      Debug.LogWarning("[VoiceNav] NavigationManager reference is missing.");
      yield break;
    }

    string url = $"{serverBaseUrl.TrimEnd('/')}{commandRoutePath}";
    VoiceCommandRouterRequest payload = new VoiceCommandRouterRequest
    {
      command = rawText,
      mode = llmMode
    };
    string json = JsonUtility.ToJson(payload);

    using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
    {
      byte[] bodyRaw = Encoding.UTF8.GetBytes(json);
      request.uploadHandler = new UploadHandlerRaw(bodyRaw);
      request.downloadHandler = new DownloadHandlerBuffer();
      request.timeout = Mathf.CeilToInt(requestTimeoutSeconds);
      request.SetRequestHeader("Content-Type", "application/json");

      yield return request.SendWebRequest();

      if (request.result != UnityWebRequest.Result.Success)
      {
        Debug.LogWarning($"[VoiceNav] Server router failed: {request.error}. Falling back to local matching.");
        HandleSpokenCommandLocally(rawText);
        yield break;
      }

      VoiceCommandRouterResponse response = JsonUtility.FromJson<VoiceCommandRouterResponse>(request.downloadHandler.text);
      if (response == null)
      {
        Debug.LogWarning("[VoiceNav] Server router returned invalid JSON. Falling back to local matching.");
        HandleSpokenCommandLocally(rawText);
        yield break;
      }

      if (debugLogs)
      {
        Debug.Log($"[VoiceNav] Router intent={response.intent}, action={response.action}, destination={response.destination}, confidence={response.confidence}");
      }

      string action = (response.action ?? string.Empty).Trim().ToLowerInvariant();
      if (action == "navigate" && !string.IsNullOrWhiteSpace(response.destination))
      {
        navigationManager.NavigateTo(response.destination);
      }
      else if (action == "cancel_navigation")
      {
        navigationManager.CancelNavigation();
      }
      else if (action == "error")
      {
        Debug.LogWarning($"[VoiceNav] Router error: {response.response_text}");
      }

      if (!string.IsNullOrWhiteSpace(response.response_text))
      {
        voiceGuide?.PlayMessage(response.response_text);
      }
    }
  }

  private void HandleSpokenCommandLocally(string rawText)
  {
    if (navigationManager == null)
      return;

    string destinationQuery = ExtractDestination(rawText);
    if (string.IsNullOrWhiteSpace(destinationQuery))
      return;

    if (TryResolveDestination(destinationQuery, out DestinationMatch match))
    {
      if (match.usePosition)
        navigationManager.NavigateToPosition(match.position, match.displayName);
      else
        navigationManager.NavigateTo(match.sceneTargetName);

      voiceGuide?.PlayMessage($"Navigating to {match.displayName}");
      return;
    }

    voiceGuide?.PlayMessage("I could not find that destination. Please try again.");
  }

  private string ExtractDestination(string rawText)
  {
    string lowered = Normalize(rawText);
    if (string.IsNullOrWhiteSpace(lowered))
      return string.Empty;

    foreach (string prefix in commandPrefixes)
    {
      string normalizedPrefix = Normalize(prefix);
      if (lowered.StartsWith(normalizedPrefix + " ", StringComparison.Ordinal))
      {
        return lowered.Substring(normalizedPrefix.Length).Trim();
      }
    }

    return lowered;
  }

  private bool TryResolveDestination(string query, out DestinationMatch match)
  {
    List<DestinationMatch> candidates = BuildCandidates();
    if (candidates.Count == 0)
    {
      match = default(DestinationMatch);
      return false;
    }

    int bestScore = -1;
    DestinationMatch best = default(DestinationMatch);

    foreach (DestinationMatch candidate in candidates)
    {
      int score = Score(query, candidate.searchText);
      if (score > bestScore)
      {
        bestScore = score;
        best = candidate;
      }
    }

    if (bestScore < 45)
    {
      match = default(DestinationMatch);
      return false;
    }

    match = best;
    return true;
  }

  private List<DestinationMatch> BuildCandidates()
  {
    var candidates = new List<DestinationMatch>();
    var seen = new HashSet<string>(StringComparer.Ordinal);

    string[] sceneDestinations = navigationManager != null ? navigationManager.GetAvailableDestinations() : Array.Empty<string>();
    foreach (string destination in sceneDestinations)
    {
      if (string.IsNullOrWhiteSpace(destination))
        continue;

      string key = Normalize(destination);
      if (!seen.Add("scene:" + key))
        continue;

      candidates.Add(new DestinationMatch
      {
        displayName = destination.Replace("_", " "),
        sceneTargetName = destination,
        searchText = key,
        usePosition = false
      });
    }

    LocationDataManager dataManager = LocationDataManager.Instance;
    if (dataManager != null && dataManager.IsLoaded)
    {
      foreach (LocationData location in dataManager.GetAllLocations())
      {
        if (location == null || string.IsNullOrWhiteSpace(location.id))
          continue;

        string locationName = string.IsNullOrWhiteSpace(location.name) ? location.id : location.name;
        string search = Normalize(location.id + " " + locationName);

        GameObject directTarget =
          GameObject.Find(location.id) ??
          GameObject.Find(locationName) ??
          GameObject.Find(location.id.Replace(" ", "_"));

        if (directTarget != null)
        {
          string key = "obj:" + directTarget.name;
          if (seen.Add(key))
          {
            candidates.Add(new DestinationMatch
            {
              displayName = locationName,
              sceneTargetName = directTarget.name,
              searchText = search,
              usePosition = false
            });
          }

          continue;
        }

        GameObject trigger = GameObject.Find($"Trigger_{location.id}");
        if (trigger != null)
        {
          string key = "trigger:" + location.id;
          if (seen.Add(key))
          {
            candidates.Add(new DestinationMatch
            {
              displayName = locationName,
              sceneTargetName = location.id,
              searchText = search,
              usePosition = true,
              position = trigger.transform.position
            });
          }
        }
      }
    }

    return candidates;
  }

  private int Score(string query, string candidate)
  {
    if (string.IsNullOrWhiteSpace(query) || string.IsNullOrWhiteSpace(candidate))
      return 0;

    if (candidate == query)
      return 100;

    if (candidate.StartsWith(query, StringComparison.Ordinal))
      return 90;

    if (candidate.IndexOf(query, StringComparison.Ordinal) >= 0)
      return 80;

    string[] queryTokens = query.Split(' ', StringSplitOptions.RemoveEmptyEntries);
    if (queryTokens.Length == 0)
      return 0;

    int tokenMatches = 0;
    foreach (string token in queryTokens)
    {
      if (candidate.IndexOf(token, StringComparison.Ordinal) >= 0)
        tokenMatches++;
    }

    return Mathf.RoundToInt((tokenMatches / (float)queryTokens.Length) * 70f);
  }

  private static string Normalize(string input)
  {
    if (string.IsNullOrWhiteSpace(input))
      return string.Empty;

    string trimmed = input.Trim().ToLowerInvariant().Replace("_", " ");
    var sb = new StringBuilder(trimmed.Length);
    foreach (char c in trimmed)
    {
      if (char.IsLetterOrDigit(c) || char.IsWhiteSpace(c))
        sb.Append(c);
    }

    return sb.ToString().Trim();
  }

  private void Log(string message)
  {
    if (debugLogs)
      Debug.Log($"[VoiceNav] {message}");
  }

  private struct DestinationMatch
  {
    public string displayName;
    public string sceneTargetName;
    public string searchText;
    public bool usePosition;
    public Vector3 position;
  }

  [Serializable]
  private class VoiceCommandRouterRequest
  {
    public string command;
    public string mode;
  }

  [Serializable]
  private class VoiceCommandRouterResponse
  {
    public string action;
    public string intent;
    public string response_text;
    public string destination;
    public float confidence;
  }
}
