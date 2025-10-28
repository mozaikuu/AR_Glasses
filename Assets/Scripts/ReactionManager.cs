using UnityEngine;
using System.Collections;

[System.Serializable]
public class SimpleReaction
{
    public string shortName;
    public AudioClip audioClip; // ✅ بدل AudioSource
    public ColorFader colorFader;
    public PrecipitateSpawner spawner;
    public float startDelay = 0f;
    public float duration = 4f;
    public string youtubeUrl = "";
    public int precipAmount = 4;
}

public class ReactionManager : MonoBehaviour
{
    public SimpleReaction[] reactions;
    private AudioSource audioSource; // ✅ مكون صوت واحد نستخدمه لكل التفاعلات

    void Awake()
    {
        // نضيف AudioSource لو مش موجود
        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
        }
    }

    public void PlayReactionByIndex(int index)
    {
        if (index < 0 || index >= reactions.Length) return;
        StartCoroutine(PlayRoutine(reactions[index]));
    }

    private IEnumerator PlayRoutine(SimpleReaction r)
    {
        if (r == null) yield break;
        if (r.startDelay > 0f) yield return new WaitForSeconds(r.startDelay);

        // 🎵 تشغيل الصوت
        if (r.audioClip != null)
        {
            audioSource.Stop();
            audioSource.clip = r.audioClip;
            audioSource.Play();
        }

        // 📺 فتح الفيديو على اليوتيوب (اختياري)
        if (!string.IsNullOrEmpty(r.youtubeUrl))
        {
            Application.OpenURL(r.youtubeUrl);
        }

        // 🌈 بدء تغيير اللون
        if (r.colorFader != null)
        {
            r.colorFader.StartFade();
        }

        // 💛 توليد الراسب
        if (r.spawner != null && r.precipAmount > 0)
        {
            int total = Mathf.Max(1, r.precipAmount);
            float interval = r.duration / total;
            for (int i = 0; i < total; i++)
            {
                r.spawner.SpawnPrecipitate(1);
                yield return new WaitForSeconds(interval);
            }
        }

        // ⏳ انتظار لنهاية التفاعل
        yield return new WaitForSeconds(r.duration);

        // 🔇 إيقاف الصوت لو لسه شغال
        if (audioSource.isPlaying)
        {
            audioSource.Stop();
        }
    }
}
