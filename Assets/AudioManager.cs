using UnityEngine;

public class AudioManager : MonoBehaviour
{
    [SerializeField] AudioSource pixabay;

    public AudioClip vinegarfizz;
    public AudioClip bubblepop;
    public AudioClip fizzle;
    public AudioClip waterpour;
    public AudioClip pouringliquid;
    public AudioClip liquidbubbling;
    public AudioClip gashiss;
    public AudioClip fizzy;

    private void Start()
    {
        pixabay.clip=vinegarfizz;
        pixabay.Play();
    }
    public void PlayPixabay(AudioClip clip)
    {
        pixabay.PlayOneShot(clip);
    }



}
