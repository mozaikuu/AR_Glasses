using System;
using UnityEngine;

/// <summary>
/// Resolves backend base URL from runtime overrides with sensible fallbacks.
/// Priority: PlayerPrefs -> env var (Editor/Desktop) -> serialized fallback.
/// </summary>
public static class ApiEndpointResolver
{
  public const string PlayerPrefsKey = "SmartGlasses.ApiBaseUrl";
  public const string EnvironmentVariable = "SMART_GLASSES_API_BASE_URL";

  public static string Resolve(string fallbackBaseUrl)
  {
    string fromPrefs = PlayerPrefs.GetString(PlayerPrefsKey, string.Empty).Trim();
    if (!string.IsNullOrWhiteSpace(fromPrefs))
      return TrimTrailingSlash(fromPrefs);

    string fromEnv = Environment.GetEnvironmentVariable(EnvironmentVariable)?.Trim() ?? string.Empty;
    if (!string.IsNullOrWhiteSpace(fromEnv))
      return TrimTrailingSlash(fromEnv);

    return TrimTrailingSlash(fallbackBaseUrl);
  }

  public static void SetOverride(string baseUrl)
  {
    string normalized = TrimTrailingSlash(baseUrl);
    PlayerPrefs.SetString(PlayerPrefsKey, normalized);
    PlayerPrefs.Save();
  }

  public static void ClearOverride()
  {
    PlayerPrefs.DeleteKey(PlayerPrefsKey);
    PlayerPrefs.Save();
  }

  private static string TrimTrailingSlash(string value)
  {
    return (value ?? string.Empty).Trim().TrimEnd('/');
  }
}
