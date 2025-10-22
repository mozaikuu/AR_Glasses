using UnityEngine;

public class FlaskMover : MonoBehaviour
{
    public float speed = 2f;

    public Vector3 direction = Vector3.right;

    void Update()
    {
        transform.Translate(direction * speed * Time.deltaTime, Space.World);
    }
}
