using UnityEngine;

/// <summary>
/// Simple generic MonoBehaviour singleton base class.
/// In this project we only use a manual singleton for NavigationManager,
/// but this is here if you want to reuse the pattern for other systems.
/// </summary>
public abstract class Singleton<T> : MonoBehaviour where T : MonoBehaviour
{
    public static T Instance { get; private set; }

    protected virtual void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        Instance = this as T;
    }
}



