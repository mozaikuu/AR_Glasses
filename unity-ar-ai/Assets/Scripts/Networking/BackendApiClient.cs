using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

[DisallowMultipleComponent]
public class BackendApiClient : MonoBehaviour
{
    [Header("Backend")]
    [SerializeField] private string baseUrl = "http://127.0.0.1:8000";
    [SerializeField] private float timeoutSeconds = 8f;

    [Serializable]
    public class QrDisplay
    {
        public string id;
        public string name;
        public string building;
        public int floor;
        public string description;
        public string additional_info;
    }

    [Serializable]
    public class QrVisibleResponse
    {
        public bool success;
        public string tracking_id;
        public bool visible;
        public QrDisplay display;
        public int active_count;
        public string error;
    }

    [Serializable]
    public class QrHiddenResponse
    {
        public bool success;
        public bool visible;
        public bool was_active;
        public int active_count;
        public string error;
    }

    [Serializable]
    public class QrTelemetryResponse
    {
        public bool success;
        public bool logged;
        public int telemetry_count;
        public string error;
    }

    [Serializable]
    private class QrVisibleRequest
    {
        public string qr_data;
        public string tracking_id;
        public string source = "hololens2";
        public double timestamp;
    }

    [Serializable]
    private class QrHiddenRequest
    {
        public string tracking_id;
        public string qr_id;
        public string source = "hololens2";
        public double timestamp;
    }

    [Serializable]
    private class QrTelemetryPayload
    {
        public bool modal_visible;
    }

    [Serializable]
    private class QrTelemetryRequestWire
    {
        public string tracking_id;
        public string qr_id;
        public string @event;
        public string source;
        public QrTelemetryPayload payload;
        public double timestamp;
    }

    public IEnumerator SendQrVisible(string qrData, string trackingId, Action<QrVisibleResponse> onSuccess, Action<string> onError)
    {
        var requestBody = new QrVisibleRequest
        {
            qr_data = qrData,
            tracking_id = trackingId,
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0
        };

        yield return PostJson("/qr/visible", JsonUtility.ToJson(requestBody), responseText =>
        {
            var response = SafeFromJson<QrVisibleResponse>(responseText);
            if (response != null && response.success)
            {
                onSuccess?.Invoke(response);
                return;
            }

            onError?.Invoke(response != null ? response.error : "Invalid /qr/visible response");
        }, onError);
    }

    public IEnumerator SendQrHidden(string trackingId, string qrId, Action<QrHiddenResponse> onSuccess, Action<string> onError)
    {
        var requestBody = new QrHiddenRequest
        {
            tracking_id = trackingId,
            qr_id = qrId,
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0
        };

        yield return PostJson("/qr/hidden", JsonUtility.ToJson(requestBody), responseText =>
        {
            var response = SafeFromJson<QrHiddenResponse>(responseText);
            if (response != null && response.success)
            {
                onSuccess?.Invoke(response);
                return;
            }

            onError?.Invoke(response != null ? response.error : "Invalid /qr/hidden response");
        }, onError);
    }

    public IEnumerator SendQrTelemetry(string trackingId, string qrId, string eventName, bool modalVisible, Action<QrTelemetryResponse> onSuccess, Action<string> onError)
    {
        var requestBody = new QrTelemetryRequestWire
        {
            tracking_id = trackingId,
            qr_id = qrId,
            @event = eventName,
            source = "hololens2",
            payload = new QrTelemetryPayload { modal_visible = modalVisible },
            timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0
        };

        yield return PostJson("/qr/telemetry", JsonUtility.ToJson(requestBody), responseText =>
        {
            var response = SafeFromJson<QrTelemetryResponse>(responseText);
            if (response != null && response.success)
            {
                onSuccess?.Invoke(response);
                return;
            }

            onError?.Invoke(response != null ? response.error : "Invalid /qr/telemetry response");
        }, onError);
    }

    private IEnumerator PostJson(string endpoint, string body, Action<string> onSuccess, Action<string> onError)
    {
        string url = baseUrl.TrimEnd('/') + endpoint;
        using (var request = new UnityWebRequest(url, UnityWebRequest.kHttpVerbPOST))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(body);
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.timeout = Mathf.CeilToInt(timeoutSeconds);
            request.SetRequestHeader("Content-Type", "application/json");

            yield return request.SendWebRequest();

#if UNITY_2020_1_OR_NEWER
            bool hasError = request.result == UnityWebRequest.Result.ConnectionError || request.result == UnityWebRequest.Result.ProtocolError;
#else
            bool hasError = request.isNetworkError || request.isHttpError;
#endif
            if (hasError)
            {
                onError?.Invoke(request.error + " (" + url + ")");
                yield break;
            }

            onSuccess?.Invoke(request.downloadHandler.text);
        }
    }

    private static T SafeFromJson<T>(string json) where T : class
    {
        try
        {
            return JsonUtility.FromJson<T>(json);
        }
        catch
        {
            return null;
        }
    }
}
