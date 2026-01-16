using UnityEngine;
using System.Collections.Generic;
using System.Linq;

public class ElementManager : MonoBehaviour 
{
    public List<ElementData> AllReactionsData = new List<ElementData>();

    public string csvFileName = "Elements"; 

    public static ElementManager Instance; 

    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
        }
        else if (Instance != this)
        {
            Destroy(gameObject);
            return;
        }

        LoadReactionsFromCSV();
    }

    private void LoadReactionsFromCSV()
    {
        TextAsset reactionCsv = Resources.Load<TextAsset>(csvFileName);

        if (reactionCsv == null)
        {
            // Error message: CSV file not found in Resources folder. Check path and name.
            Debug.LogError($"❌ CSV file '{csvFileName}.csv' not found in Resources folder. Check path and name."); 
            return;
        }

        string[] lines = reactionCsv.text.Split('\n');
        
        for (int i = 1; i < lines.Length; i++)
        {
            string line = lines[i].Trim();
            if (string.IsNullOrWhiteSpace(line)) continue;

            string[] values = line.Split(',');
            ElementData reaction = ElementData.FromStrings(values);

            if (reaction != null)
            {
                AllReactionsData.Add(reaction); 
            }
        }

        Debug.Log($"✅ Successfully loaded reactions. Total count: {AllReactionsData.Count}");
    }

    // Function to find a reaction by keyword
    public ElementData FindReaction(string searchKeyword)
    {
        string key = searchKeyword.Trim(); 

        return AllReactionsData.Find(r => 
            // Case-insensitive search on the Equation field
            r.Equation.ToUpper().Contains(key.ToUpper())
        );
    }
}