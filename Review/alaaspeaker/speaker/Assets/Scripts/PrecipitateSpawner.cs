using UnityEngine;

public class PrecipitateSpawner : MonoBehaviour
{
    public GameObject precipitatePrefab;
    public Transform spawnPoint;
    public float scale = 0.08f;

    public void SpawnPrecipitate(int amount = 1)
    {
        if (precipitatePrefab == null || spawnPoint == null) return;
        for (int i = 0; i < amount; i++)
        {
            Vector3 pos = spawnPoint.position + Random.insideUnitSphere * 0.03f;
            GameObject p = Instantiate(precipitatePrefab, pos, Quaternion.identity);
            p.transform.localScale = Vector3.one * scale;
            Destroy(p, 12f);
        }
    }
}
