import unicodedata
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import json
import os

def clean_string(s: str) -> str:
    """
    Convertit la chaîne en minuscules, retire les accents, supprime les espaces,
    tirets et traits d'union pour uniformiser le nom de quartier.
    """
    if not isinstance(s, str):
        s = str(s)
    # Normalisation Unicode (NFD) pour séparer les accents
    nfkd = unicodedata.normalize('NFD', s.lower())
    # On retire les accents
    without_accents = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
    # Retrait des tirets, espaces, etc.
    without_accents = without_accents.replace('-', '').replace('–', '').replace(' ', '')
    return without_accents.strip()

def load_page2_data():
    """Load and prepare data for page 2 from optimized files"""
    import os
    
    # Check if we're running from the main directory or page2 directory
    if os.path.exists("data/optimized"):
        base_path = "data/optimized/"
        geojson_base_path = "data/"
    else:
        base_path = "../data/optimized/"
        geojson_base_path = "../data/"
    
    # Load pre-processed data from optimized directory
    csv_path = os.path.join(base_path, "arbres_aggregated.csv")
    df_aggregated = pd.read_csv(csv_path)
    
    # Clean names for joining
    df_aggregated["cleaned_name"] = df_aggregated["ARROND_NOM"].apply(clean_string)
    
    # Rename columns for consistency with the rest of the code
    df_grouped = df_aggregated.rename(columns={
        "Arbres": "Nombre d'arbres",
        "Arbres_remarquables": "Nombre d'arbres remarquables"
    })
    
    # Load and process GeoJSON file - still need this for mapping
    geojson_path = os.path.join(geojson_base_path, "quartiers_sociologiques_2014.geojson")
    with open(geojson_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    # Process geojson to add cleaned names
    for feature in geojson_data["features"]:
        original = feature["properties"]["Arrondissement"]
        cleaned = clean_string(original)
        feature["properties"]["cleaned_name"] = cleaned

    # Create a dataframe with original and cleaned names from geojson
    geo_rows = []
    for feat in geojson_data["features"]:
        original = feat["properties"]["Arrondissement"]
        cleaned = feat["properties"]["cleaned_name"]
        geo_rows.append({
            "original_name": original,
            "cleaned_name": cleaned
        })
    geo_df = pd.DataFrame(geo_rows)

    # Merge the datasets
    df_merged = pd.merge(
        geo_df,
        df_grouped,
        how="left",
        on="cleaned_name"
    )

    # Fill NaN values
    df_merged["Nombre d'arbres"] = df_merged["Nombre d'arbres"].fillna(0)
    df_merged["Nombre d'arbres remarquables"] = df_merged["Nombre d'arbres remarquables"].fillna(0)

    return {
        'df_merged': df_merged,
        'geojson_data': geojson_data
    }

def create_page2_figures(data):
    """Create figures for page 2"""
    df_merged = data['df_merged']
    geojson_data = data['geojson_data']
    
    max_val = df_merged["Nombre d'arbres"].max()
    custom_scale = [
        [0.0, "lightgray"],   # 0 arbres = gris
        [0.000001, "#edf8e9"],
        [0.2, "#bae4b3"],
        [0.4, "#74c476"],
        [0.6, "#31a354"],
        [0.8, "#006d2c"],
        [1.0, "#00441b"],
    ]

    fig_map = px.choropleth_mapbox(
        df_merged,
        geojson=geojson_data,
        locations="cleaned_name",                # doit matcher properties.cleaned_name
        featureidkey="properties.cleaned_name",
        color="Nombre d'arbres",
        color_continuous_scale=custom_scale,
        range_color=(0, max_val),
        mapbox_style="open-street-map",
        center={"lat": 45.5017, "lon": -73.5673},
        zoom=9,  # Zoom un peu plus large que 10 pour voir davantage en périphérie
        hover_name="original_name",
        hover_data={
            "Nombre d'arbres": True,
            "Nombre d'arbres remarquables": True,
            "cleaned_name": False
        }
    )
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    
    return {
        'map': fig_map
    }

# The following part remains for when the file is run directly as a standalone app
if __name__ == "__main__":
    app = dash.Dash(__name__)
    
    # Load data and create figures
    data = load_page2_data()
    figures = create_page2_figures(data)
    
    app.layout = html.Div([
        html.Div(style={"display": "flex", "flexDirection": "row"}, children=[
            html.Div(
                style={"width": "70%", "padding": "10px"},
                children=[dcc.Graph(id="quartiers_map", figure=figures['map'], style={"height": "80vh"})]
            ),
            html.Div(
                style={"width": "30%", "padding": "10px", "fontSize": "16px", "fontWeight": "bold"},
                children=[
                    html.H2("Détails du quartier"),
                    html.Div("Cliquez sur un quartier pour voir les détails.", id="info")
                ]
            ),
        ]),
    ])

    @app.callback(
        Output("info", "children"),
        Input("quartiers_map", "clickData")
    )
    def display_click_info(clickData):
        if clickData is None:
            return "Cliquez sur un quartier pour voir les détails."
        try:
            loc = clickData["points"][0]["location"]
            df_merged = data['df_merged']
            row = df_merged[df_merged["cleaned_name"] == loc].iloc[0]
            original_name = row["original_name"]
            total_arbres = int(row["Nombre d'arbres"])
            arbres_remarquables = int(row["Nombre d'arbres remarquables"])
            return html.Div([
                html.P(f"Quartier : {original_name}"),
                html.P(f"Nombre d'arbres : {total_arbres}"),
                html.P(f"Nombre d'arbres remarquables : {arbres_remarquables}")
            ])
        except Exception as e:
            return f"Erreur lors de la récupération des données : {str(e)}"

    app.run(debug=True)
