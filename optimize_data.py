import pandas as pd
import json
import os

def preprocess_arbres_data():
    """
    Process the large arbres-publics.csv file to create smaller, pre-aggregated datasets
    for different visualizations.
    """
    print("Starting data preprocessing...")
    
    # Define paths
    input_file = "data/arbres-publics.csv"
    output_dir = "data/optimized"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Reading large CSV file: {input_file}")
    # Read only the columns we need
    df = pd.read_csv(
        input_file, 
        usecols=["ARROND_NOM", "Arbre_remarquable"],
        engine="python", 
        on_bad_lines="skip"
    )
    
    print("Processing arbres data...")
    # Clean up data
    df["ARROND_NOM"] = df["ARROND_NOM"].str.strip().str.title()
    
    # Create aggregations
    # 1. Total trees per arrondissement
    df_total = df.groupby("ARROND_NOM").size().reset_index(name="Arbres")
    
    # 2. Remarkable trees per arrondissement
    df_remarquables = (
        df[df["Arbre_remarquable"] == "O"]
        .groupby("ARROND_NOM")
        .size()
        .reset_index(name="Arbres_remarquables")
    )
    
    # 3. Merge for complete dataset
    df_merged = pd.merge(df_total, df_remarquables, on="ARROND_NOM", how="left")
    df_merged["Arbres_remarquables"] = df_merged["Arbres_remarquables"].fillna(0).astype(int)
    df_merged["Arbres_non_remarquables"] = df_merged["Arbres"] - df_merged["Arbres_remarquables"]
    
    # Save the aggregated data
    output_file = os.path.join(output_dir, "arbres_aggregated.csv")
    print(f"Saving aggregated data to {output_file}")
    df_merged.to_csv(output_file, index=False)
    
    # Free memory
    del df
    
    print("Arbres data preprocessing completed!")
    return output_file

def optimize_geojson():
    """
    Create a simplified version of the quartiers_sociologiques_2014.geojson file
    by keeping only essential properties.
    """
    print("Optimizing GeoJSON file...")
    
    input_file = "data/quartiers_sociologiques_2014.geojson"
    output_file = "data/optimized/quartiers_simplified.geojson"
    
    # Load the GeoJSON file
    with open(input_file, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
    
    # Keep only essential properties for each feature
    for feature in geojson_data["features"]:
        # Keep only needed properties
        essential_props = {
            "id": feature["properties"].get("id"),
            "Arrondissement": feature["properties"].get("Arrondissement"),
            "Q_sociologique": feature["properties"].get("Q_sociologique")
        }
        feature["properties"] = essential_props
    
    # Save the simplified GeoJSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(geojson_data, f)
    
    print(f"Simplified GeoJSON saved to {output_file}")
    return output_file

def process_jardins_communautaires():
    """
    Process jardins-communautaires.csv to create a smaller aggregated file
    with counts per arrondissement.
    """
    print("Processing jardins communautaires data...")
    
    input_file = "data/jardins-communautaires.csv"
    output_file = "data/optimized/jardins_aggregated.csv"
    
    # Read the jardins communautaires data
    df = pd.read_csv(input_file)
    
    # Count jardins per arrondissement
    jardins_count = df.groupby("arrondissement").size().reset_index(name="jardins_count")
    
    # Save the aggregated data
    jardins_count.to_csv(output_file, index=False)
    
    print(f"Jardins aggregated data saved to {output_file}")
    return output_file

if __name__ == "__main__":
    print("Starting data optimization process...")
    
    # Process arbres data
    arbres_file = preprocess_arbres_data()
    
    # Optimize GeoJSON
    geojson_file = optimize_geojson()
    
    # Process jardins data
    jardins_file = process_jardins_communautaires()
    
    print("All data preprocessing completed!")
    print(f"Generated optimized files in data/optimized/ directory")