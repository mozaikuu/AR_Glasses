using System;
using UnityEngine;

/// <summary>
/// Central place to raise QR-detected events.
/// Later you can hook this up to your actual QR plugin / MRTK QR tracker.
/// </summary>
public class QRScanner : MonoBehaviour
{
    /// <summary>
    /// roomID (decoded QR text), world position, world rotation.
    /// </summary>
    public static event Action<string, Vector3, Quaternion> OnQRDetected;

    /// <summary>
    /// Call this from your actual QR detection code when a QR is read.
    /// For now you can also call it from the Inspector using a debug button.
    /// </summary>
    public static void RaiseQRDetected(string qrText, Vector3 position, Quaternion rotation)
    {
        OnQRDetected?.Invoke(qrText, position, rotation);
    }

    // Example manual trigger for testing in the editor.
    // You can call this from other scripts, or add your own UI/debug hook.
    public void SimulateQRDetection(string qrText)
    {
        Vector3 pos = transform.position;
        Quaternion rot = transform.rotation;
        RaiseQRDetected(qrText, pos, rot);
    }
}

