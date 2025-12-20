using UnityEngine;

/// <summary>
/// Simple arrow that always rotates to face the target on the horizontal plane.
/// </summary>
public class ArrowController : MonoBehaviour
{
    [Tooltip("What this arrow should point to (usually the target room's transform).")]
    public Transform target;

    private void Update()
    {
        if (target == null)
            return;

        Vector3 direction = target.position - transform.position;
        direction.y = 0f; // ignore vertical tilt

        if (direction.sqrMagnitude > 0.0001f)
        {
            transform.rotation = Quaternion.LookRotation(direction);
        }
    }
}



