using UnityEngine;

public class ObjectTooltip : MonoBehaviour
{
    [Tooltip("الرسالة التي ستظهر عند مرور الماوس فوق هذا الكائن.")]
    [TextArea(3, 5)]
    public string tooltipMessage = "معلومات عن الكائن";

    private void OnMouseEnter()
    {
        if (WorldTooltip.Instance != null)
        {
            WorldTooltip.Instance.Show(tooltipMessage);
        }
    }

    private void OnMouseExit()
    {
        if (WorldTooltip.Instance != null)
        {
            WorldTooltip.Instance.Hide();
        }
    }
}