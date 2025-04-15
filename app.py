import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import json
import geopandas as gpd
from dash_extensions import EventListener
import plotly.express as px
import plotly.graph_objects as go
from shapely.geometry import shape

# Import your visualization modules
from page1.visu_a import load_page1_data, create_page1_figures
from page2.visu_a import load_page2_data, create_page2_figures
from page3.visu_a import load_page3_data, create_page3_figures, carte_espaces_verts
from page4.visu_a import load_page4_data, create_page4_figures

# Initialize the Dash app
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
app.title = "Montréal en Visualisations"
server = app.server  # For deployment platforms

# Load data for all pages
data1 = load_page1_data()
data2 = load_page2_data()
data3 = load_page3_data() 
data4 = load_page4_data()

# Create figures
figures1 = create_page1_figures(data1)
figures2 = create_page2_figures(data2)
figures3 = create_page3_figures(data3)
figures4 = create_page4_figures(data4)

# App Layout with Scrollytelling
app.layout = html.Div([
    # Header
    html.Header([
        html.H1("Montréal en Visualisations", className="header-title"),
        html.P("Une exploration des espaces verts, arbres et jardins communautaires de Montréal", 
               className="header-subtitle")
    ], className="app-header"),
    
    # Navigation bar
    html.Nav([
        html.Ul([
            html.Li(html.A("Mon quartier est-il vert ?", href="#section1")),
            html.Li(html.A("Arbres urbains", href="#section2")),
            html.Li(html.A("Parcs de mon quartier", href="#section3")),
            html.Li(html.A("Jardins communautaires", href="#section4"))
        ], className="nav-links")
    ], className="nav-bar"),
    
    # Section 1: Page 1 visualization
    html.Section([
        html.H2("Mon quartier est-il vert ?", id="section1"),
        html.Div([
            html.Div([
                html.P("Découvrez la proportion de surface végétale dans chaque arrondissement de Montréal."),
                dcc.Graph(id="pie_chart", figure=figures1["pie"]),
            ], className="viz-column"),
            html.Div([
                html.H3("Proportion de surface végétale par arrondissement"),
                dcc.Graph(id="map_section1", figure=figures1["map"])
            ], className="viz-column-wide")
        ], className="viz-row")
    ], className="section"),
    
    # Section 2: Page 2 visualization
    html.Section([
        html.H2("Arbres urbains", id="section2"),
        html.Div([
            html.Div([
                dcc.Graph(id="quartiers_map", figure=figures2["map"]),
            ], className="viz-column-wide"),
            html.Div([
                html.H3("Détails du quartier"),
                html.Div("Cliquez sur un quartier pour voir les détails.", id="info"),
            ], className="viz-column")
        ], className="viz-row")
    ], className="section"),
    
    # Section 3: Page 3 visualization
    html.Section([
        html.H2("Parcs de mon quartier", id="section3"),
        html.Div([
            html.Div([
                html.H3("km² d'espaces verts par arrondissement"),
                dcc.Graph(id="territoires_map", figure=figures3["territoires_map"]),
            ], className="viz-column"),
            html.Div([
                html.Div(
                    id="hover-info",
                    style={"textAlign": "center", "marginBottom": "10px"},
                ),
                EventListener(
                    dcc.Graph(id="espace_verts_map", figure=figures3["espace_verts_map"]),
                    events=[{"event": "plotly_hover", "props": ["points[0].location"]}],
                ),
            ], className="viz-column-wide")
        ], className="viz-row")
    ], className="section"),
    
    # Section 4: Page 4 visualization
    html.Section([
        html.H2("Jardins communautaires", id="section4"),
        html.Div([
            html.Div([
                html.H3("Jardins communautaires près de mon quartier"),
                html.Div(id="info-text-jardins"),
            ], className="viz-column"),
            html.Div([
                html.H3("Parcelles de jardins communautaires de montréal"),
                dcc.Graph(id="fig_map", figure=figures4["map"], 
                         config={'scrollZoom': True, 'displayModeBar': False, 'editable': False}),
            ], className="viz-column-wide")
        ], className="viz-row")
    ], className="section"),
    
    # Footer
    html.Footer([
        html.P("© 2025 INF8808E - Visualisation de données", className="footer-text")
    ], className="app-footer"),
    
    # Add this scrolling JavaScript
    html.Script("""
        document.addEventListener('DOMContentLoaded', function() {
            // Smooth scrolling for navigation links
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function(e) {
                    e.preventDefault();
                    document.querySelector(this.getAttribute('href')).scrollIntoView({
                        behavior: 'smooth'
                    });
                });
            });
        });
    """, type="text/javascript")
])

# Copy all your callback functions from each page
@app.callback(
    Output("pie_chart","figure"),
    Input("map","hoverData")
)
def update_pie_on_hover(hoverData):
    if not hoverData:
        return figures1['pie']

    try:
        codeid = hoverData["points"][0]["location"]
    except (IndexError, KeyError, TypeError):
        return figures1['pie']

    row_df = data1['df'].loc[data1['df']["CODEID"] == codeid]
    if row_df.empty:
        return figures1['pie']

    row = row_df.iloc[0]
    autre_val = row["Eau_km2"] + row["NonCl_km2"]

    new_labels = ["Végétale", "Minérale", "Autres"]
    new_values = [row["Veg_km2"], row["Min_km2"], autre_val]

    new_fig = go.Figure(data=[
        go.Pie(
            labels=new_labels,
            values=new_values,
            textinfo="none",
            texttemplate="%{label}\n%{value:.2f} km²",
            textposition="outside"
        )
    ])
    new_fig.update_layout(
        title={
            "text": f"{row['NOM']}",
            "x":0.5,
            "y":0.88,
            "xanchor":"center",
            "yanchor":"top"
        },
        margin={"t":60},
        showlegend=False
    )
    return new_fig

@app.callback(
    Output("info", "children"),
    Input("quartiers_map", "clickData")
)
def display_click_info(clickData):
    if clickData is None:
        return "Cliquez sur un quartier pour voir les détails."
    try:
        loc = clickData["points"][0]["location"]
        df_merged = data2['df_merged']
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

# Callback pour mettre à jour la carte et les informations de survol
@app.callback(
    [Output("espace_verts_map", "figure"), Output("hover-info", "children")],
    Input("territoires_map", "hoverData"),
)
def update_map_and_hover_info(hoverData):
    if not hoverData:
        return figures3['espace_verts_map'], "Survolez un territoire pour voir les détails."

    try:
        codeid = hoverData["points"][0]["location"]
        df_territoires = data3['df_territoires']
        df_espaces_verts = data3['df_espaces_verts']
        territoires_MTL_Clean_geojson_data = data3['territoires_MTL_Clean_geojson_data']
        espace_vert_geojson_data = data3['espace_vert_geojson_data']
        territory_shapes = data3['territory_shapes']
        
        selected_territory = next(
            (feature for feature in territoires_MTL_Clean_geojson_data["features"] if feature["properties"]["CODEID"] == codeid),
            None,
        )
        if not selected_territory:
            return figures3['espace_verts_map'], "Aucun territoire trouvé."

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
        return figures3['espace_verts_map'], "Erreur lors du traitement des données de survol."


# Callback to count jardins in the hovered arrondissement
@app.callback(
    Output("info-text-jardins", "children"),
    Input("fig_map", "hoverData")
)
def display_jardin_count(hover_data):
    if hover_data is None:
        return "Survolez un point pour voir le nombre de jardins dans l'arrondissement."
    
    try:
        df = data4['df']
        arrondissement = hover_data["points"][0]["customdata"][0]  # arrondissement is first in customdata
        jardin_count = len(df[df["arrondissement"] == arrondissement])
        return html.Div([
            html.H3(f"Arrondissement: {arrondissement}"),
            html.P(f"Nombre de jardins communautaires: {jardin_count}"),
            html.P("Cliquez sur un jardin pour voir ses détails.")
        ])
    except (KeyError, IndexError):
        return "Hover data unavailable. Try another marker."

# Add CSS for the scrollytelling layout
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Scrollytelling CSS */
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                color: #333;
                background-color: #f9f9f9;
            }
            .app-header {
                background-color: #125C13;
                color: white;
                padding: 1rem 2rem;
                text-align: center;
            }
            .header-title {
                margin: 0;
                font-size: 2.5rem;
            }
            .header-subtitle {
                margin-top: 0.5rem;
                font-size: 1.2rem;
            }
            .nav-bar {
                position: sticky;
                top: 0;
                background-color: #1a7a1a;
                z-index: 1000;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .nav-links {
                display: flex;
                justify-content: space-around;
                list-style: none;
                padding: 0;
                margin: 0;
            }
            .nav-links li {
                padding: 0;
            }
            .nav-links a {
                display: block;
                color: white;
                text-decoration: none;
                padding: 1rem;
                transition: background-color 0.3s;
            }
            .nav-links a:hover {
                background-color: #0d450e;
            }
            .section {
                padding: 2rem 1rem;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }
            .section:nth-child(odd) {
                background-color: #f0f7f0;
            }
            .viz-row {
                display: flex;
                flex-direction: row;
                flex-wrap: wrap;
                gap: 1rem;
                height: calc(100vh - 200px);
            }
            .viz-column {
                flex: 1;
                min-width: 300px;
                overflow: hidden;
            }
            .viz-column-wide {
                flex: 2;
                min-width: 500px;
                overflow: hidden;
            }
            h2 {
                text-align: center;
                color: #125C13;
                margin-top: 0;
                margin-bottom: 2rem;
            }
            h3 {
                color: #1a7a1a;
            }
            .app-footer {
                background-color: #125C13;
                color: white;
                text-align: center;
                padding: 1rem;
            }
            /* Ensure graphs fill their containers */
            .js-plotly-plot, .plot-container {
                width: 100%;
                height: 100%;
            }
            @media (max-width: 900px) {
                .viz-row {
                    flex-direction: column;
                    height: auto;
                }
                .viz-column, .viz-column-wide {
                    width: 100%;
                    height: 70vh;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

if __name__ == "__main__":
    app.run_server(debug=True)