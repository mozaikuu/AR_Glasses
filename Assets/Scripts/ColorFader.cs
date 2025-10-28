using UnityEngine;
using System.Collections;

public class ColorFader : MonoBehaviour
{
    public Renderer targetRenderer;
    public Color startColor = new Color(0.4f,0f,0.4f,1f); // purple
    public Color endColor = new Color(1f,1f,1f,0f); // transparent
    public float duration = 3f;

    public void StartFade()
    {
        StopAllCoroutines();
        StartCoroutine(FadeRoutine());
    }

    private IEnumerator FadeRoutine()
    {
        if (targetRenderer == null) yield break;
        Material mat = targetRenderer.material; // instanced material
        float t = 0f;
        while (t < duration)
        {
            t += Time.deltaTime;
            float alpha = Mathf.Lerp(startColor.a, endColor.a, t / duration);
            Color newColor = Color.Lerp(startColor, endColor, t / duration);
            newColor.a = alpha;
            mat.color = newColor;
            yield return null;
        }
        mat.color = endColor;
    }
}
