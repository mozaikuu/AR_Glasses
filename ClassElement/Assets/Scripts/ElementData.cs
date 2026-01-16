using UnityEngine;

[System.Serializable]
public class ElementData
{
    // These fields map to your CSV columns
    public string Equation;
    public string Reactants;
    public string Products;
    public string ReactantStates;
    public string ProductStates;
    public string Gases;
    public string Solids;
    public string SharedCompounds;
    public int NumReactants;
    public int NumProducts;

    public static ElementData FromStrings(string[] values)
    {
        if (values.Length < 10) return null; 

        ElementData data = new ElementData();
        
        // Ensure all fields are trimmed and quotes are removed to prevent errors
        data.Equation = values[0].Trim().Replace("\"", "");
        data.Reactants = values[1].Trim().Replace("\"", "");
        data.Products = values[2].Trim().Replace("\"", "");
        data.ReactantStates = values[3].Trim().Replace("\"", "");
        data.ProductStates = values[4].Trim().Replace("\"", "");
        data.Gases = values[5].Trim().Replace("\"", "");
        data.Solids = values[6].Trim().Replace("\"", "");
        data.SharedCompounds = values[7].Trim().Replace("\"", "");

        // Parsing numbers
        int.TryParse(values[8].Trim().Replace("\"", ""), out data.NumReactants);
        int.TryParse(values[9].Trim().Replace("\"", ""), out data.NumProducts);
        
        return data;
    }
}