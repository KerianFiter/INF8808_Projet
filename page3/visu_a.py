import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import json
import geopandas as gpd
from shapely.geometry import shape
from dash_extensions import EventListener

def load_page3_data():
    """Load and prepare data for page 3"""
    # Chargement et reprojection des données géospatiales
    chemin_geojson = r"../data/espace_vert.geojson"
    gdf = gpd.read_file(chemin_geojson)

    if gdf.crs is None:
        gdf.set_crs(epsg=2950, inplace=True)
    espace_vert_gdf_4326 = gdf.to_crs(epsg=4326)
    espace_vert_geojson_data = json.loads(espace_vert_gdf_4326.to_json())

    chemin_geojson = r"../data/territoires_MTL_Clean.geojson"
    gdf = gpd.read_file(chemin_geojson)

    if gdf.crs is None:
        gdf.set_crs(epsg=2950, inplace=True)
    territoires_MTL_Clean_gdf_4326 = gdf.to_crs(epsg=4326)
    territoires_MTL_Clean_gdf_4326 = territoires_MTL_Clean_gdf_4326.drop(columns=["DATEMODIF"], errors="ignore")
    territoires_MTL_Clean_geojson_data = json.loads(territoires_MTL_Clean_gdf_4326.to_json())

    # Ajout d'une étiquette combinant TYPO1 et TYPO2
    for feature in espace_vert_geojson_data["features"]:
        typo1 = feature["properties"].get("TYPO1", "Inconnu")
        typo2 = feature["properties"].get("TYPO2", "Inconnu")
        feature["properties"]["TYPO_LABEL"] = f"{typo1} | {typo2}"

    # Préparation du DataFrame des espaces verts
    df_espaces_verts = espace_vert_gdf_4326.copy()

    if "OBJECTID" not in df_espaces_verts.columns:
        df_espaces_verts["OBJECTID"] = range(1, len(df_espaces_verts) + 1)
    if "SUPERFICIE" not in df_espaces_verts.columns:
        df_espaces_verts["SUPERFICIE"] = 0
    if "Nom" not in df_espaces_verts.columns:
        df_espaces_verts["Nom"] = "Nom inconnu"
    if "TYPO1" in df_espaces_verts.columns:
        type_text = df_espaces_verts["TYPO1"].astype(str)
        if "TYPO2" in df_espaces_verts.columns:
            typo2_text = df_espaces_verts["TYPO2"].fillna("Inconnu").astype(str)
            type_text += " | " + typo2_text.where(typo2_text != "", "Inconnu").astype(str)
        df_espaces_verts["TYPE"] = type_text
    else:
        df_espaces_verts["TYPE"] = "Type inconnu"

    df_espaces_verts["SUPERFICIE"] = df_espaces_verts["SUPERFICIE"].astype(float)
    df_espaces_verts["OBJECTID"] = df_espaces_verts["OBJECTID"].astype(int)
    df_espaces_verts["TYPE"] = df_espaces_verts["TYPE"].astype(str)
    df_espaces_verts["Nom"] = df_espaces_verts["Nom"].astype(str)

    # Mise à jour des données GeoJSON avec le champ TYPE
    for feature in espace_vert_geojson_data["features"]:
        objectid = feature["properties"].get("OBJECTID")
        if objectid is not None:
            matching_rows = df_espaces_verts.loc[df_espaces_verts["OBJECTID"] == objectid, "TYPE"]
            type_value = matching_rows.values[0] if not matching_rows.empty else "Type inconnu"
        else:
            type_value = "Type inconnu"
        feature["properties"]["TYPE"] = type_value

    # Préparation du DataFrame des territoires
    df_territoires = territoires_MTL_Clean_gdf_4326.copy()
    if "CODEID" not in df_territoires.columns:
        df_territoires["CODEID"] = range(1, len(df_territoires) + 1)
    if "NOM" not in df_territoires.columns:
        df_territoires["NOM"] = "Nom inconnu"

    # Convert CODEID to string to match GeoJSON format
    df_territoires["CODEID"] = df_territoires["CODEID"].astype(str)

    # Calcul des intersections entre espaces verts et territoires
    territory_superficie = {str(territory["properties"]["CODEID"]): 0 for territory in territoires_MTL_Clean_geojson_data["features"]}
    territory_shapes = {str(territory["properties"]["CODEID"]): shape(territory["geometry"]) for territory in territoires_MTL_Clean_geojson_data["features"]}

    for espace in espace_vert_geojson_data["features"]:
        espace_shape = shape(espace["geometry"])
        espace_superficie = espace["properties"].get("SUPERFICIE", 0)
        for codeid, territory_shape in territory_shapes.items():
            if espace_shape.intersects(territory_shape):
                intersection = espace_shape.intersection(territory_shape)
                intersection_area_ratio = intersection.area / espace_shape.area
                territory_superficie[codeid] += float(espace_superficie) * intersection_area_ratio

    df_territoires["SUPERFICIE"] = df_territoires["CODEID"].map(territory_superficie)

    # Calcul du nombre de parcs par territoire
    territory_parc_count = {str(territory["properties"]["CODEID"]): 0 for territory in territoires_MTL_Clean_geojson_data["features"]}

    for espace in espace_vert_geojson_data["features"]:
        espace_shape = shape(espace["geometry"])
        for codeid, territory_shape in territory_shapes.items():
            if espace_shape.intersects(territory_shape):
                territory_parc_count[codeid] += 1

    df_territoires["PARC_COUNT"] = df_territoires["CODEID"].map(territory_parc_count)

    # Conversion des unités en km²
    df_territoires["SUPERFICIE"] = (df_territoires["SUPERFICIE"].astype(float) / 100).round(3)
    df_espaces_verts["SUPERFICIE"] = (df_espaces_verts["SUPERFICIE"].astype(float) / 100).round(3)
    
    return {
        'df_espaces_verts': df_espaces_verts,
        'df_territoires': df_territoires,
        'espace_vert_geojson_data': espace_vert_geojson_data,
        'territoires_MTL_Clean_geojson_data': territoires_MTL_Clean_geojson_data,
        'territory_shapes': territory_shapes
    }

def carte_espaces_verts(df_espaces_verts, _zoom, _center, _geojson_data):
    """Helper function to create green spaces map"""
    map = px.choropleth_mapbox(
        df_espaces_verts,
        geojson=_geojson_data,
        locations="OBJECTID",
        featureidkey="properties.OBJECTID",
        color="SUPERFICIE",
        hover_name="Nom",
        hover_data={"OBJECTID": False, "TYPE": True, "SUPERFICIE": True},
        labels={"SUPERFICIE": "Superficie (km²)", "TYPE": "Type d'espace vert"},
        map_style="carto-positron",
        center=_center,
        zoom=_zoom,
        color_continuous_scale="Greens",
        range_color=(0, 3),
    )
    map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, hovermode="closest", coloraxis_showscale=True)
    return map

def create_page3_figures(data):
    """Create figures for page 3"""
    df_espaces_verts = data['df_espaces_verts']
    df_territoires = data['df_territoires']
    espace_vert_geojson_data = data['espace_vert_geojson_data']
    territoires_MTL_Clean_geojson_data = data['territoires_MTL_Clean_geojson_data']
    
    # Création de la carte des espaces verts
    espace_verts_map = carte_espaces_verts(
        df_espaces_verts, 
        10, 
        {"lat": 45.55, "lon": -73.75}, 
        espace_vert_geojson_data
    )
    
    # Création de la carte des territoires
    territoires_map = px.choropleth_mapbox(
        df_territoires,
        geojson=territoires_MTL_Clean_geojson_data,
        locations="CODEID",
        featureidkey="properties.CODEID",
        color="SUPERFICIE",
        hover_name="NOM",
        hover_data={"CODEID": False, "PARC_COUNT": True, "SUPERFICIE": True},
        labels={"PARC_COUNT": "Nombre de parcs", "SUPERFICIE": "Superficie (km²)"},
        map_style="carto-positron",
        center={"lat": 45.55, "lon": -73.75},
        zoom=9,
        color_continuous_scale="Greens",
        range_color=(0, 10),
    )
    territoires_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, hovermode="closest", coloraxis_showscale=True)
    
    return {
        'espace_verts_map': espace_verts_map,
        'territoires_map': territoires_map
    }

# The following part remains for when the file is run directly as a standalone app
if __name__ == "__main__":
    app = dash.Dash(__name__)
    
    # Load data and create figures
    data = load_page3_data()
    figures = create_page3_figures(data)
    
    espace_verts_map = figures['espace_verts_map']
    territoires_map = figures['territoires_map']
    
    app.layout = html.Div(
        style={"display": "flex", "flexDirection": "row"},
        children=[
            html.Div(
                style={"width": "33%", "padding": "10px"},
                children=[
                    html.H1("Parcs de mon quartier", style={"textAlign": "center", "margin": "0 0 20px 0"}),
                    html.H3("km² d'espaces verts par arrondissement"),
                    dcc.Graph(id="territoires_map", figure=territoires_map),
                ],
            ),
            html.Div(
                style={"width": "67%", "padding": "10px"},
                children=[
                    html.Div(
                        id="hover-info",
                        style={"textAlign": "center", "marginBottom": "10px", "fontSize": "16px", "fontWeight": "bold"},
                    ),
                    EventListener(
                        dcc.Graph(id="espace_verts_map", figure=espace_verts_map, style={"height": "80vh"}),
                        events=[{"event": "plotly_hover", "props": ["points[0].location"]}],
                    ),
                ],
            ),
        ],
    )

    # Callback pour mettre à jour la carte et les informations de survol
    @app.callback(
        [Output("espace_verts_map", "figure"), Output("hover-info", "children")],
        Input("territoires_map", "hoverData"),
    )
    def update_map_and_hover_info(hoverData):
        if not hoverData:
            return espace_verts_map, "Survolez un territoire pour voir les détails."

        try:
            codeid = hoverData["points"][0]["location"]
            df_territoires = data['df_territoires']
            df_espaces_verts = data['df_espaces_verts']
            territoires_MTL_Clean_geojson_data = data['territoires_MTL_Clean_geojson_data']
            espace_vert_geojson_data = data['espace_vert_geojson_data']
            territory_shapes = data['territory_shapes']
            
            selected_territory = next(
                (feature for feature in territoires_MTL_Clean_geojson_data["features"] if feature["properties"]["CODEID"] == codeid),
                None,
            )
            if not selected_territory:
                return espace_verts_map, "Aucun territoire trouvé."

            territory_name = selected_territory["properties"].get("NOM", "Nom inconnu")
            parc_count = df_territoires.loc[df_territoires["CODEID"] == codeid, "PARC_COUNT"].values[0]
            superficie = df_territoires.loc[df_territoires["CODEID"] == codeid, "SUPERFICIE"].values[0]
            hover_text = f"Arrondissement: {territory_name} | Nombre de parcs: {parc_count} | Superficie des parcs: {superficie} km²"

            territory_shape = territory_shapes[codeid]
            centroid = territory_shape.centroid
            center = {"lat": centroid.y, "lon": centroid.x}

            filtered_features = [
                feature for feature in espace_vert_geojson_data["features"] if shape(feature["geometry"]).intersects(territory_shape)
            ]

            filtered_geojson_data = espace_vert_geojson_data.copy()
            filtered_geojson_data["features"] = filtered_features

            updated_map = carte_espaces_verts(df_espaces_verts, 12, center, filtered_geojson_data)
            return updated_map, hover_text

        except (IndexError, KeyError, TypeError) as e:
            print(f"Error: {e}")
            return espace_verts_map, "Erreur lors du traitement des données de survol."

    # Lancement de l'application
    app.run(debug=True)
