using UnityEngine;

public class CollisionHandler : MonoBehaviour
{
    public GameObject purplePrefab;

    private void OnCollisionEnter(Collision collision)
    {
        if (collision.gameObject.CompareTag("Red") || collision.gameObject.CompareTag("Blue"))
        {
            Vector3 spawnPosition = (transform.position + collision.transform.position) / 2;
            Instantiate(purplePrefab, spawnPosition, Quaternion.identity);

            Destroy(collision.gameObject);
            Destroy(gameObject);
        }
    }
}
