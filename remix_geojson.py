import json

with open("data/montreal.json", "r") as f1, open("data/taux_veg.geojson", "r") as f2:
    limadmin_geojson = json.load(f1)
    vegetation_geojson = json.load(f2)
    

    # Replace the geometry while keeping original structure

    from rapidfuzz import fuzz

    # Check similarity instead of exact match
    for feature in limadmin_geojson["features"]:
        best_match = None
        highest_score = 0
        
        for veg_feature in vegetation_geojson["features"]:
            score = fuzz.ratio(feature["properties"]["NOM"], veg_feature["properties"]["NOM"])
            
            if score > highest_score:
                highest_score = score
                best_match = veg_feature
        
        # Print the closest match
        print(f"LIMADMIN: {feature['properties']['NOM']} → Closest Match in Vegetation: {best_match['properties']['NOM']} (Similarity: {highest_score}%)")

        matching_feature = next((f for f in vegetation_geojson["features"] if f["properties"]["NOM"] == feature["properties"]["NOM"]), None)
        
    if matching_feature:
        feature["geometry"] = matching_feature["geometry"]
        print(f'its a match for arrondissement {feature["properties"]["NOM"]} and {matching_feature['properties']['NOM']}')
    #else:
        #print(f'no match found for arrondissement {feature["properties"]["NOM"]}')
        # Recursively clean all string values in the dictionary
    def clean_json_strings(data):
        if isinstance(data, dict):
            return {k: clean_json_strings(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [clean_json_strings(v) for v in data]
        elif isinstance(data, str):
            return data.replace("\n", " ")  # Replace newline with space
        return data

    # Apply cleaning function to JSON
    cleaned_geojson = clean_json_strings(limadmin_geojson)
    # Save cleaned JSON
    
with open("data/updated_montreal.json", "w") as f_out:
    json.dump(cleaned_geojson, f_out, separators=(',', ':'))


    