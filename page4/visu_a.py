from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import geopandas as gpd

def load_page4_data():
    """Load and prepare data for page 4"""
    import os
    
    # Check if we're running from the main directory or page4 directory
    if os.path.exists("data/jardins-communautaires.csv"):
        base_path = "data/"
    else:
        base_path = "../data/"
        
    # Use the correct path for loading files
    csv_jardins_path = os.path.join(base_path, "jardins-communautaires.csv")
    df = pd.read_csv(csv_jardins_path)

    geojson_jardins_path = os.path.join(base_path, "updated_montreal.json")
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
    
    # Create base figure
    fig = go.Figure()

    # Add choropleth layer first
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson_jardins_data,
        locations=[feature["properties"]["NOM"] for feature in geojson_jardins_data["features"]],
        z=[1] * len(geojson_jardins_data["features"]),  # Dummy values
        featureidkey="properties.NOM",
        colorscale=[[0, "rgb(128,150,128)"], [1, "rgb(128,150,128)"]],  # Solid color
        showscale=False,
        marker_line_width=1,
        marker_line_color="white",
        hoverinfo="none",
        customdata=["arrondissement"],  # Explicitly include arrondissements
    ))

    # Add scatter markers on top
    fig.add_trace(go.Scattermapbox(
        lat=df["latitude"],
        lon=df["longitude"],
        mode="markers",
        marker=go.scattermapbox.Marker(
            size=12,
            color="green",
            opacity=0.95
        ),
        hovertext=df["nom"],  # Main title
        hoverinfo="text",
        customdata=df[["arrondissement", "adresse"]],
        hovertemplate=(
            "<b>%{hovertext}</b><br>" +
            " %{customdata[0]}<br>" +
            " %{customdata[1]}<extra></extra>"
        )
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat":45.55,"lon":-73.65},
        mapbox_zoom=9.9,
        margin=dict(l=0,r=0,t=0,b=0),
        height=600,
        dragmode=False
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
        Output("info_text_jardins", "children"),
        Input("fig_map", "clickData")
    )
    def display_jardin_count(clickData):
        if clickData is None:
            return "cliquez sur un point pour voir le nombre de jardins dans l'arrondissement."
        
        try:
            df = data['df']
            arrondissement = clickData["points"][0]["customdata"][0]  # arrondissement is first in customdata
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