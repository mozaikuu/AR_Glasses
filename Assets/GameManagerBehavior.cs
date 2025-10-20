using UnityEngine;
using UnityEngine.SceneManagement;

public class GameManagerBehavior : MonoBehaviour
{
    [SerializeField]
    GameObject pauseMenu;
    public static bool isPaused;
    // Start is called once before the first execution of Update after the MonoBehaviour is created
    void Start()
    {
        pauseMenu.SetActive(false);
        isPaused=false;
        
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            if(!isPaused)
            {
            PauseGame();

            }
            else
            {
                ResumeGame();
            }

        }

        
    }

    private void PauseGame()
    {
        pauseMenu.SetActive(true);
        isPaused=true;
        Time.timeScale=0f;
    }

    public void ResumeGame()
    {
        pauseMenu.SetActive(false);
        isPaused=false;
        Time.timeScale=1f;

    }
    public void MainMenu()
    {
        Time.timeScale=1f;
        SceneManager.LoadScene("MainMenu");
    }
    public void QuitGame()
    {
        UnityEditor.EditorApplication.isPlaying=false;
        Application.Quit();
        Debug.Log("Quit");


    }
}
