using System;
using System.Collections;
using System.Collections.Concurrent;
using System.Collections.Generic;
using UnityEngine;

#if WINDOWS_UWP
using Microsoft.MixedReality.QR;
#endif

[DisallowMultipleComponent]
public class HoloLensQrTracker : MonoBehaviour
{
    [Header("Dependencies")]
    [SerializeField] private BackendApiClient backendClient;
    [SerializeField] private QrModalController modalController;

    [Header("Telemetry")]
    [SerializeField] private bool sendTelemetry = true;
    [SerializeField] private float telemetryEverySeconds = 2f;

    private readonly ConcurrentQueue<Action> _mainThreadActions = new ConcurrentQueue<Action>();
    private readonly Dictionary<string, string> _qrMap = new Dictionary<string, string>();

    private string _activeTrackingId;
    private string _activeQrId;
    private float _nextTelemetryAt;

#if WINDOWS_UWP
    private QRCodeWatcher _watcher;
#endif

    private void Awake()
    {
        if (backendClient == null)
        {
            backendClient = FindObjectOfType<BackendApiClient>();
        }

        if (modalController == null)
        {
            modalController = FindObjectOfType<QrModalController>();
        }
    }

    private void OnEnable()
    {
#if WINDOWS_UWP
        StartWatcherAsync();
#else
        Debug.Log("HoloLens QR watcher runs only on UWP device. Use SimulateVisible/SimulateHidden in Editor.");
#endif
    }

    private void OnDisable()
    {
#if WINDOWS_UWP
        if (_watcher != null)
        {
            _watcher.Added -= OnQrAdded;
            _watcher.Updated -= OnQrUpdated;
            _watcher.Removed -= OnQrRemoved;
            _watcher.Stop();
            _watcher = null;
        }
#endif
    }

    private void Update()
    {
        while (_mainThreadActions.TryDequeue(out var action))
        {
            action?.Invoke();
        }

        if (backendClient == null || !sendTelemetry || string.IsNullOrEmpty(_activeTrackingId) || modalController == null || !modalController.IsVisible)
        {
            return;
        }

        if (Time.time >= _nextTelemetryAt)
        {
            _nextTelemetryAt = Time.time + Mathf.Max(0.5f, telemetryEverySeconds);
            StartCoroutine(backendClient.SendQrTelemetry(
                _activeTrackingId,
                _activeQrId,
                "displayed",
                true,
                null,
                error => Debug.LogWarning("QR telemetry failed: " + error)));
        }
    }

#if WINDOWS_UWP
    private async void StartWatcherAsync()
    {
        var accessStatus = await QRCodeWatcher.RequestAccessAsync();
        if (accessStatus != QRCodeWatcherAccessStatus.Allowed)
        {
            Debug.LogError("QR access denied: " + accessStatus);
            return;
        }

        _watcher = new QRCodeWatcher();
        _watcher.Added += OnQrAdded;
        _watcher.Updated += OnQrUpdated;
        _watcher.Removed += OnQrRemoved;
        _watcher.Start();
    }

    private void OnQrAdded(object sender, QRCodeAddedEventArgs args)
    {
        HandleQrVisibleEvent(args.Code);
    }

    private void OnQrUpdated(object sender, QRCodeUpdatedEventArgs args)
    {
        HandleQrVisibleEvent(args.Code);
    }

    private void HandleQrVisibleEvent(QRCode qr)
    {
        if (qr == null || string.IsNullOrWhiteSpace(qr.Data))
        {
            return;
        }

        string watcherId = qr.Id.ToString();
        _mainThreadActions.Enqueue(() =>
        {
            _qrMap[watcherId] = qr.Data;
            StartCoroutine(backendClient.SendQrVisible(
                qr.Data,
                watcherId,
                response =>
                {
                    _activeTrackingId = response.tracking_id;
                    _activeQrId = response.display != null ? response.display.id : null;
                    _nextTelemetryAt = Time.time + Mathf.Max(0.5f, telemetryEverySeconds);
                    if (modalController != null)
                    {
                        modalController.Show(response.display);
                    }
                },
                error => Debug.LogWarning("QR visible post failed: " + error)));
        });
    }

    private void OnQrRemoved(object sender, QRCodeRemovedEventArgs args)
    {
        string watcherId = args.Code.Id.ToString();
        _mainThreadActions.Enqueue(() =>
        {
            string qrId = _activeQrId;
            StartCoroutine(backendClient.SendQrHidden(
                watcherId,
                qrId,
                _ => { },
                error => Debug.LogWarning("QR hidden post failed: " + error)));

            if (_activeTrackingId == watcherId && modalController != null)
            {
                modalController.Hide();
                _activeTrackingId = null;
                _activeQrId = null;
            }

            _qrMap.Remove(watcherId);
        });
    }
#endif

    public void SimulateVisible(string qrData, string trackingId = "editor-qr-1")
    {
        if (backendClient == null || string.IsNullOrWhiteSpace(qrData))
        {
            return;
        }

        StartCoroutine(backendClient.SendQrVisible(
            qrData,
            trackingId,
            response =>
            {
                _activeTrackingId = response.tracking_id;
                _activeQrId = response.display != null ? response.display.id : null;
                if (modalController != null)
                {
                    modalController.Show(response.display);
                }
            },
            error => Debug.LogWarning("Simulate visible failed: " + error)));
    }

    public void SimulateHidden(string trackingId = "editor-qr-1")
    {
        if (backendClient == null)
        {
            return;
        }

        StartCoroutine(backendClient.SendQrHidden(
            trackingId,
            _activeQrId,
            _ => { },
            error => Debug.LogWarning("Simulate hidden failed: " + error)));

        _activeTrackingId = null;
        _activeQrId = null;
        if (modalController != null)
        {
            modalController.Hide();
        }
    }
}
