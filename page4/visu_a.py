from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import geopandas as gpd

def load_page4_data():
    """Load and prepare data for page 4"""
    # Load data
    csv_jardins_path = r"data/jardins-communautaires.csv"
    df = pd.read_csv(csv_jardins_path)

    geojson_jardins_path = r"data/montreal.json"
    with open(geojson_jardins_path, "r", encoding="utf-8") as f:
        geojson_jardins_data = json.load(f)
    
    return {
        'df': df,
        'geojson_jardins_data': geojson_jardins_data
    }

def create_page4_figures(data):
    """Create figures for page 4"""
    df = data['df']
    geojson_jardins_data = data['geojson_jardins_data']
    
    # Create a scatter mapbox plot with orange markers
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        hover_name="nom",
        hover_data={"arrondissement": True, "adresse": True, "latitude": False, "longitude": False},
        height=600,
        color_discrete_sequence=["orange"],
        size_max=20,  # Increase marker size
        opacity=0.8
    )

    # Add GeoJSON boundaries using Choroplethmapbox, filled with green
    fig.add_trace(
        go.Choroplethmapbox(
            geojson=geojson_jardins_data,
            featureidkey="properties.NOM",
            locations=[feature["properties"]["NOM"] for feature in geojson_jardins_data["features"]],
            z=[1] * len(geojson_jardins_data["features"]),
            colorscale=[[0, 'rgb(0,128,128)'], [1, 'rgb(0,128,128)']],  # Solid teal fill
            showscale=False,
            name="Arrondissement Boundaries",
            marker=dict(line=dict(width=1, color="white"), opacity=0.2),  # Solid white outline
            hoverinfo="skip"
        )
    )

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox=dict(
            center=dict(lat=45.5017, lon=-73.5673),  # Center on Montreal
            zoom=9,  # Initial zoom level to show districts
            pitch=0,
            bearing=0
        ),
        margin={"r":0, "t":0, "l":0, "b":0},
        dragmode="pan",
        clickmode="event+select"
    )
    
    return {
        'map': fig
    }

# The following part remains for when the file is run directly as a standalone app
if __name__ == "__main__":
    app = Dash(__name__)
    
    # Load data and create figures
    data = load_page4_data()
    figures = create_page4_figures(data)
    
    # Layout
    app.layout = html.Div(
        style={"display":"flex", "flexDirection":"row"},
        children=[
            html.Div(
                style={"width":"33%", "padding":"10px"},
                children=[
                    html.H1(
                        "Jardins communautaire près de mon quartier",
                        style={"textAlign":"center", "margin":"0 0 20px 0"}
                    ),
                    html.Div(id='info-text-jardins')
                ]
            ),
            html.Div(
                style={"width":"67%", "padding":"10px", "height":"80vh", "overflow":"visible"},
                children=[
                    html.H3("Parcelles de jardins communautaires de montréal"),
                    dcc.Graph(
                        id="fig_map",
                        figure=figures['map'],
                        style={"height":"100%", "width":"100%"},
                        hoverData=None,
                        config={'scrollZoom': True, 'displayModeBar': False, 'editable': False}
                    )
                ]
            )
        ]
    )

    # Callback to count jardins in the hovered arrondissement
    @app.callback(
        Output("info-text-jardins", "children"),
        Input("fig_map", "hoverData")
    )
    def display_jardin_count(hover_data):
        if hover_data is None:
            return "Survolez un point pour voir le nombre de jardins dans l'arrondissement."
        
        try:
            df = data['df']
            arrondissement = hover_data["points"][0]["customdata"][0]  # arrondissement is first in customdata
            jardin_count = len(df[df["arrondissement"] == arrondissement])
            return html.Div([
                html.H3(f"Arrondissement: {arrondissement}"),
                html.P(f"Nombre de jardins communautaires: {jardin_count}"),
                html.P("Cliquez sur un jardin pour voir ses détails.")
            ])
        except (KeyError, IndexError):
            return "Hover data unavailable. Try another marker."

    # Run the app
    app.run(debug=True)