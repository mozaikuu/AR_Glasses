using UnityEngine;

public class ItemInfo : MonoBehaviour
{
    [TextArea(2, 4)]
    public string tooltipText = "Default info";

    void OnMouseDown()
    {
        Debug.Log("Clicked on: " + name);
        Debug.Log("Tooltip text: " + tooltipText);
        WorldTooltip.Instance?.Show(tooltipText);
    }
}