using UnityEngine;

public class Speaker : MonoBehaviour
{
    public AudioClip sound;
    private AudioSource audioSource;

    void Start()
    {
        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.clip = sound;
        audioSource.volume = 1f;
        audioSource.Play();
    }
}
