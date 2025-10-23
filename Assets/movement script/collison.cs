using UnityEngine;

public class CollisionHandler : MonoBehaviour
{
    public GameObject purplePrefab;
     // The purple cube to spawn

    private void OnCollisionEnter(Collision collision)
    {
        
        // Check if the other object is tagged as "Red" or "Blue"
        if (collision.gameObject.CompareTag("Red") || collision.gameObject.CompareTag("Blue"))
        {
            // Get the midpoint between both cubes
            Vector3 spawnPosition = (transform.position + collision.transform.position) / 2;

            // Create purple cube
            Instantiate(purplePrefab, spawnPosition, purplePrefab.transform.rotation);

            // Destroy both cubes
            Destroy(collision.gameObject);
            Destroy(gameObject);
        }
    }
}
