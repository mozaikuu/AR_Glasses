using UnityEngine;
using UnityEngine.UI;

[DisallowMultipleComponent]
public class QrModalController : MonoBehaviour
{
    [SerializeField] private GameObject modalRoot;
    [SerializeField] private Text titleText;
    [SerializeField] private Text detailsText;

    private bool _isVisible;

    public bool IsVisible => _isVisible;

    private void Awake()
    {
        Hide();
    }

    public void Show(BackendApiClient.QrDisplay display)
    {
        if (display == null)
        {
            Hide();
            return;
        }

        if (modalRoot != null)
        {
            modalRoot.SetActive(true);
        }

        if (titleText != null)
        {
            titleText.text = string.IsNullOrWhiteSpace(display.name) ? "Location" : display.name;
        }

        if (detailsText != null)
        {
            string floorText = display.floor > 0 ? "Floor " + display.floor : "Floor unknown";
            string buildingText = string.IsNullOrWhiteSpace(display.building) ? "" : display.building + "\n";
            string descriptionText = string.IsNullOrWhiteSpace(display.description) ? "" : display.description + "\n";
            string extraInfoText = string.IsNullOrWhiteSpace(display.additional_info) ? "" : display.additional_info;
            detailsText.text = buildingText + floorText + "\n" + descriptionText + extraInfoText;
        }

        _isVisible = true;
    }

    public void Hide()
    {
        if (modalRoot != null)
        {
            modalRoot.SetActive(false);
        }

        _isVisible = false;
    }
}
