using UnityEngine;

public class controll : MonoBehaviour
{
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        
    }
    public void Exit()
    {
        Application.Quit();
        Debug.Log("Quit");

    }
    public void CloseGame(){
        UnityEditor.EditorApplication.isPlaying=false;
        Application.Quit();


    }
}
