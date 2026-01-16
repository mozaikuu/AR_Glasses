using UnityEngine;

/// <summary>
/// Very simple 2-point line between the user and the target.
/// Add this to a GameObject with a LineRenderer and set position count = 2.
/// </summary>
[RequireComponent(typeof(LineRenderer))]
public class LinePathRenderer : MonoBehaviour
{
    [Tooltip("User head / camera transform.")]
    public Transform user;

    [Tooltip("Destination / room transform.")]
    public Transform target;

    private LineRenderer _line;

    private void Awake()
    {
        _line = GetComponent<LineRenderer>();
        if (_line.positionCount < 2)
        {
            _line.positionCount = 2;
        }
    }

    private void Update()
    {
        if (user == null || target == null || _line == null)
            return;

        _line.SetPosition(0, user.position);
        _line.SetPosition(1, target.position);
    }
}



