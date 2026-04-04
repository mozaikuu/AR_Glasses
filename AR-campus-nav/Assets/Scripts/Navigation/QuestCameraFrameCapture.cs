using System;
using UnityEngine;

/// <summary>
/// Captures a frame from the active camera and returns it as base64 JPEG for server upload.
/// </summary>
public static class QuestCameraFrameCapture
{
  public static bool TryCaptureMainCameraBase64(
    int targetWidth,
    int jpegQuality,
    out string imageBase64,
    out string error)
  {
    Camera source = Camera.main;
    if (source == null)
    {
      Camera[] all = UnityEngine.Object.FindObjectsOfType<Camera>();
      if (all != null && all.Length > 0)
        source = all[0];
    }

    return TryCaptureCameraBase64(source, targetWidth, jpegQuality, out imageBase64, out error);
  }

  private static bool TryCaptureCameraBase64(
    Camera sourceCamera,
    int targetWidth,
    int jpegQuality,
    out string imageBase64,
    out string error)
  {
    imageBase64 = string.Empty;
    error = string.Empty;

    if (sourceCamera == null)
    {
      error = "camera_missing";
      return false;
    }

    int width = Mathf.Clamp(targetWidth, 128, 1280);
    int quality = Mathf.Clamp(jpegQuality, 25, 95);
    float aspect = sourceCamera.aspect;
    if (aspect < 0.2f)
      aspect = 16f / 9f;
    int height = Mathf.Clamp(Mathf.RoundToInt(width / aspect), 128, 720);

    RenderTexture previousActive = RenderTexture.active;
    RenderTexture previousTarget = sourceCamera.targetTexture;
    RenderTexture rt = null;
    Texture2D frame = null;

    try
    {
      rt = RenderTexture.GetTemporary(width, height, 24, RenderTextureFormat.ARGB32);
      sourceCamera.targetTexture = rt;
      sourceCamera.Render();

      RenderTexture.active = rt;
      frame = new Texture2D(width, height, TextureFormat.RGB24, false, false);
      frame.ReadPixels(new Rect(0, 0, width, height), 0, 0);
      frame.Apply(false, false);

      byte[] jpeg = frame.EncodeToJPG(quality);
      if (jpeg == null || jpeg.Length == 0)
      {
        error = "jpg_encode_failed";
        return false;
      }

      imageBase64 = Convert.ToBase64String(jpeg);
      return true;
    }
    catch (Exception exc)
    {
      error = exc.Message;
      return false;
    }
    finally
    {
      sourceCamera.targetTexture = previousTarget;
      RenderTexture.active = previousActive;

      if (rt != null)
        RenderTexture.ReleaseTemporary(rt);
      if (frame != null)
        UnityEngine.Object.Destroy(frame);
    }
  }
}
