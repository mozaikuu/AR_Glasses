using UnityEngine;
using TMPro;

public class WorldTooltip : MonoBehaviour
{
    public static WorldTooltip Instance;
    public GameObject tooltipPanel;
    public TMP_Text tooltipText;

    void Awake()
    {
        // تهيئة Singleton
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        
        // إخفاء اللوحة في البداية
        if (tooltipPanel != null)
            tooltipPanel.SetActive(false);
    }

    // دالة الإظهار: تحدد النص وتجعل اللوحة مرئية
    public void Show(string text)
    {
        if (tooltipText != null) 
            tooltipText.text = text;
        
        if (tooltipPanel != null) 
            tooltipPanel.SetActive(true);
        
        // **ملاحظة:** تم إزالة تحديث الموضع من هنا
    }

    // دالة الإخفاء: تجعل اللوحة غير مرئية
    public void Hide()
    {
        if (tooltipPanel != null) 
            tooltipPanel.SetActive(false);
    }

    // **ملاحظة:** تم حذف دالة Update() ودالة UpdatePosition() بالكامل
}