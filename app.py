import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import json
import geopandas as gpd
from dash_extensions import EventListener
import plotly.express as px
import plotly.graph_objects as go
import copy
from shapely.geometry import shape

# Import your visualization modules
from page1.visu_a import load_page1_data, create_page1_figures
from page2.visu_a import load_page2_data, create_page2_figures
from page3.visu_a import load_page3_data, create_page3_figures, carte_espaces_verts
from page4.visu_a import load_page4_data, create_page4_figures
from page5.visu_a import load_page5_data, create_page5_figures, add_bars

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
data5 = load_page5_data()

# Create figures
figures1 = create_page1_figures(data1)
figures2 = create_page2_figures(data2)
figures3 = create_page3_figures(data3)
figures4 = create_page4_figures(data4)
figures5 = create_page5_figures(data5)


POLLUTANT_FULL_NAMES = {
    "CE": "Carbone élémentaire",
    "CO": "Monoxyde de carbone",
    "COV": "Composés organiques volatils",
    "H2S": "Sulfure d’hydrogène",
    "NOx": "Mono/dioxyde d’azote",
    "O3": "Ozone",
    "PUF": "Particules ultra fines",
    "PM": "Particules fines",
    "SO2": "Dioxyde de soufre"
}
initial_ts = go.Figure()
initial_ts.update_layout(
    title="Cliquez sur une station…",
    margin=dict(t=30, b=30)
)
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
            html.Li(html.A("Jardins communautaires", href="#section4")),
            html.Li(html.A("Qualité de l'air", href="#section5")),
        ], className="nav-links")
    ], className="nav-bar"),

    # Section 1: Page 1 visualization
    html.Section([
        html.H2("Mon quartier est-il vert ?", id="section1"),
        html.Div([
            html.Div([
                html.H3("Avantages des surfaces végétales en milieux urbains"),
                html.Div("Cliquez sur un quartier pour voir les détails.", id="info_veg"),
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
                html.H3("Avantages des arbres en milieux Urbains"),
                html.Div("Cliquez sur un quartier pour voir les détails.", id="info"),
            ], className="viz-column")
        ], className="viz-row")
    ], className="section"),

    # Section 3: Page 3 visualization
    html.Section([
        html.H2("Parcs de mon quartier", id="section3"),
        html.Div([
            html.Div([
                html.H3("Parcs dans montréal"),
                html.Div('',id='parcs_info',style={"width": "100%", "height": "250px", "overflow": "hidden"}),
                html.Div(   style={"width": "100%", "height": "400px", "overflow": "hidden"},  # Adjust height & prevent overlap
                            children=[
                                dcc.Graph(id="parcs_arrondissement_map", figure=figures3["territoires_map"]),
                            ])
                
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
                html.Div("",id="info_jardins"),
            ], className="viz-column"),
            html.Div([
                html.H3("Parcelles de jardins communautaires de montréal"),
                dcc.Graph(id="jardins_map", figure=figures4["map"],config={'scrollZoom': False, 'displayModeBar': False, 'editable': False}),
            ], className="viz-column-wide")
        ], className="viz-row")
    ], className="section"),
# Section 5: Page 5 visualization
    html.Section([
        html.H2("Réseaux de surveillance de la qualité de l'air (RSQA)", id="section5"),
        html.Div([
            html.Div(
                style={"flex": "1", "padding": "0 10px"},
                children=[
                    html.H3('Comment mesurer l\'indice de la qualité de l\'air ?'),
                    dcc.Markdown(f""" 
                            <div style="text-align:center; font-size:18px;">
                            La ville de Montréal surveille la qualité de l'air grâce à un réseau de <b>11 </b> stations de mesure réparties sur son territoire. 
                            Ces capteurs analysent différents polluants atmosphériques.\n
                            Pour chaque polluant, sous-indice entre 0 et 100 est déterminé en comparant sa concentration mesurée à une valeur de référence.
                            L'indice de la qualité de l'air <b>(IQA)</b> final correspond au sous-indice le plus élevé parmi ceux calculés.\n 
                            Un jour est dis <b>Bon</b> si son IQA est en dessous de 25, <b>Acceptable</b> entre 25 et 50 et <b>Mauvais</b> si au dessus de 50.            
                            </div>""", dangerously_allow_html=True),
                    html.H4("Cliquez sur une station pour plus de details", id='iqa_journalier'),
                    html.Div(
                            style={"width": "100%", "height": "400px", "overflow": "hidden"},  # Adjust height & prevent overlap
                            children=[
                                dcc.Graph(id="time_series", figure=None, config={'displayModeBar': False})
                            ]
                        )
                ]
            ),
            html.Div([

                html.H3("Indice de Qualité de l’Air (IQA) par station en 2024"),
                dcc.Graph(id="rsqa_map", figure=figures5["map"],
                         config={"editable": False,'scrollZoom': False , 'displayModeBar': False}),
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

### Callback affichage texte surface vegetales
@app.callback(
    [Output("pie_chart","figure"),Output('info_veg','children')],
    Input("map_section1","clickData")  # Change "map" to "map_section1"
)
def update_pie_on_click(clickData):
    text = dcc.Markdown(f""" 
                            <div style="text-align:center; font-size:20px;">
                            Les surfaces végétales sont essentielles à l’environnement et à notre bien-être. 
                            Elles régulent la température, absorbent le CO₂, réduisent la pollution et favorisent la biodiversité. 
                            À l’inverse, les surfaces minérales stockent la chaleur et accentuent les îlots de chaleur urbains.
                            Préserver les espaces verts améliore la qualité de vie et lutte contre le changement climatique.
                            Cliquez sur un arrondissement pour voir les détails.
                            </div>""", dangerously_allow_html=True)
    if not clickData:
        return figures1['pie'],text

    try:
        codeid = clickData["points"][0]["location"]
    except (IndexError, KeyError, TypeError):
        return figures1['pie'],text

    row_df = data1['df'].loc[data1['df']["CODEID"] == codeid]
    if row_df.empty:
        return figures1['pie'],text

    row = row_df.iloc[0]
    autre_val = row["Eau_km2"] + row["NonCl_km2"]

    new_labels = ["Végétale", "Minérale", "Autres"]
    new_values = [row["Veg_km2"], row["Min_km2"], autre_val]
    print(row_df.head(1))
    text = dcc.Markdown(f""" 
                            <div style="text-align:center; font-size:20px;">
                            Les surfaces végétales sont essentielles à l’environnement et à notre bien-être. 
                            Elles régulent la température, absorbent le CO₂, réduisent la pollution et favorisent la biodiversité. 
                            À l’inverse, les surfaces minérales stockent la chaleur et accentuent les îlots de chaleur urbains.
                            Préserver les espaces verts améliore la qualité de vie et lutte contre le changement climatique.
                            L\'arrondissement <b>{row['NOM']}</b> contient de <b>{new_values[0]:.2f}</b> km² de surfaces végétales
                            contre <b>{new_values[1]:.2f}</b> km² de surfaces minérales.
                            </div>""", dangerously_allow_html=True)
    
    new_fig = go.Figure(data=[
        go.Pie(
            labels=new_labels,
            values=new_values,
            textinfo="none",
            texttemplate="%{label}\n%{value:.2f} km²",
            textposition="outside",
            marker=dict(colors=["green", "grey", "brown"]),
            hovertemplate="<b>%{label}</b><br>Surface: %{value:.2f} km²"
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
    return new_fig,text
### Callback affichage texte arbres
@app.callback(
    Output("info", "children"),
    Input("quartiers_map", "clickData")
)
def display_click_info(clickData):
    print('callback arbres')
    if clickData is None:
        return dcc.Markdown(f""" 
                            <div style="text-align:center; font-size:20px;">
                            Les arbres en milieu urbain offrent de nombreux avantages. 
                            Ils purifient l'air en absorbant le dioxyde de carbone et les polluants, 
                            réduisent la chaleur en apportant de l'ombre, et améliorent le bien-être en créant des espaces verts apaisants. 
                            Ils favorisent la biodiversité et réduisent le bruit, contribuant ainsi à une meilleure qualité de vie en ville. 
                            Cliquez sur un arrondissement pour voir les détails.
                            </div>""", dangerously_allow_html=True)
    try:
        loc = clickData["points"][0]["location"]
        df_merged = data2['df_merged']
        row = df_merged[df_merged["cleaned_name"] == loc].iloc[0]
        original_name = row["original_name"]
        total_arbres = int(row["Nombre d'arbres"])
        arbres_remarquables = int(row["Nombre d'arbres remarquables"])
        if total_arbres!=0:
            return dcc.Markdown(f"""
                                <div style="text-align:center; font-size:20px;">
                                Les arbres en milieu urbain offrent de nombreux avantages. 
                                Ils purifient l'air en absorbant le dioxyde de carbone et les polluants, 
                                réduisent la chaleur en apportant de l'ombre, et améliorent le bien-être en créant des espaces verts apaisants. 
                                Ils favorisent la biodiversité et réduisent le bruit, contribuant ainsi à une meilleure qualité de vie en ville. 
                                Dans l'arrondissement <b>{original_name}</b>, on compte <b>{total_arbres}</b> arbres dont <b>{arbres_remarquables}</b> ont été jugés remarquables.
                                </div>""", dangerously_allow_html=True)
    
        else:
            return dcc.Markdown(f"""
                                <div style="text-align:center; font-size:20px;">
                                Les arbres en milieu urbain offrent de nombreux avantages. 
                                Ils purifient l'air en absorbant le dioxyde de carbone et les polluants, 
                                réduisent la chaleur en apportant de l'ombre, et améliorent le bien-être en créant des espaces verts apaisants. 
                                Ils favorisent la biodiversité et réduisent le bruit, contribuant ainsi à une meilleure qualité de vie en ville. 
                                Malheureusement, dans l'arrondissement <b>{original_name}</b>, l'inventaire des arbres n'a pas été mis à jour.
                                </div>""", dangerously_allow_html=True)
    except Exception as e:
        return f"Erreur lors de la récupération des données : {str(e)}"

# Callback pour mettre à jour la carte et les informations de survol
@app.callback(
    [Output("espace_verts_map", "figure"), Output("parcs_info", "children")],
    Input("parcs_arrondissement_map", "clickData"),
)
def update_parcs_map_info(clickData):
    base_text = """ Les parcs offrent des lieux de détente, réduisent le stress et améliorent le climat urbain. <br>"""
                            
    if not clickData:
        return figures3['espace_verts_map'], dcc.Markdown(f"""
                                                    {base_text}
                                                    🌱 **Cliquez sur un quartier pour savoir combien de parcs il abrite.**
                                                    """, dangerously_allow_html=True)

    try:
        codeid = clickData["points"][0]["location"]
        print(f"DEBUG: Hovered CODEID: {codeid}")  # Debug statement

        df_territoires = data3['df_territoires']
        # Ensure the CODEID in our DataFrame matches what we get from hover
        print(f"DEBUG: Available CODEIDs: {df_territoires['CODEID'].unique()}")

        df_espaces_verts = data3['df_espaces_verts']
        territoires_MTL_Clean_geojson_data = data3['territoires_MTL_Clean_geojson_data']
        espace_vert_geojson_data = data3['espace_vert_geojson_data']
        territory_shapes = data3['territory_shapes']

        # Check if the CODEID exists in our territory_shapes dictionary
        if codeid not in territory_shapes:
            print(f"DEBUG: CODEID {codeid} not found in territory_shapes")
            return figures3['espace_verts_map'], dcc.Markdown(f"""
                                                    {base_text}
                                                    ❌ **Malheureusement l\'arrondissement'avec CODEID {codeid} n\'a pas été trouvé.**
                                                    """, dangerously_allow_html=True)

        selected_territory = next(
            (feature for feature in territoires_MTL_Clean_geojson_data["features"]
             if str(feature["properties"]["CODEID"]) == str(codeid)),
            None,
        )

        if not selected_territory:
            print(f"DEBUG: No territory found for CODEID {codeid}")
            return figures3['espace_verts_map'], dcc.Markdown(f"""
                                                    {base_text}
                                                    ❌ **Aucun arrondissement trouvé**
                                                    """, dangerously_allow_html=True)

        territory_name = selected_territory["properties"].get("NOM", "Nom inconnu")
        parc_count = df_territoires.loc[df_territoires["CODEID"] == codeid, "PARC_COUNT"].values[0]
        superficie = df_territoires.loc[df_territoires["CODEID"] == codeid, "SUPERFICIE"].values[0]
        hover_text = base_text + f"L'arrondissement: {territory_name} compte {parc_count} parcs pour une superficie totale de {superficie} km²"
        text_info = dcc.Markdown(f"""               {base_text}
                                                    L'arrondissement **{territory_name}** compte **{parc_count}** parcs pour une superficie totale de **{superficie} km²**
                                                    """, dangerously_allow_html=True)

        territory_shape = territory_shapes[codeid]
        centroid = territory_shape.centroid
        center = {"lat": centroid.y, "lon": centroid.x}

        filtered_features = [
            feature for feature in espace_vert_geojson_data["features"]
            if shape(feature["geometry"]).intersects(territory_shape)
        ]

        filtered_geojson_data = espace_vert_geojson_data.copy()
        filtered_geojson_data["features"] = filtered_features

        updated_map = carte_espaces_verts(df_espaces_verts, 12, center, filtered_geojson_data)
        return updated_map, text_info

    except (IndexError, KeyError, TypeError) as e:
        print(f"Error: {e}")
        return figures3['espace_verts_map'], f"Erreur lors du traitement des données de survol: {str(e)}"
    
### callback jardins communautaires
@app.callback(
        Output('info_jardins', 'children'),
        Input("jardins_map", "clickData")
    )
def display_jardin_count(clickData):
    base_text = """
    Un jardin communautaire est un espace cultivé collectivement par les habitants d’un quartier, souvent sur un terrain public ou partagé. 
    Il permet aux participants de produire leurs propres fruits, légumes et herbes, favorisant ainsi une alimentation saine et locale. 
    En plus de ses bienfaits écologiques, comme la réduction des îlots de chaleur urbains et la préservation de la biodiversité, 
    il renforce les liens sociaux, encourage l’entraide et crée un sentiment d’appartenance. 
    C’est un lieu d’apprentissage où les jardiniers échangent connaissances et pratiques durables, tout en embellissant leur environnement.
    """

    if clickData is None:
        return dcc.Markdown(f"""
            {base_text}<br><br>
            🌱 **Cliquez sur un quartier pour savoir combien de jardins il abrite.**
        """, dangerously_allow_html=True)

    try:
        df = data4["df"]
        arrondissement = clickData["points"][0]["customdata"][0]  # Extract arrondissement
        jardin_count = len(df[df["arrondissement"] == arrondissement])

        return dcc.Markdown(f"""
            {base_text}<br><br>
            🌿 L'arrondissement <b>{arrondissement}</b> contient <b>{jardin_count}</b> jardins communautaires.
            
        """, dangerously_allow_html=True)

    except (KeyError, IndexError):
        return dcc.Markdown(f"""
            {base_text}<br><br>
            ❌ **Il ne semble pas y avoir de jardins communautaires par ici, essayez ailleurs.**
            
        """, dangerously_allow_html=True)

### callback time_series pour le RSQA
@app.callback(
        [Output("time_series", "figure"),Output("iqa_journalier",'children'),Output('rsqa_map','figure')],
        Input("rsqa_map", "clickData")
)
def update_time_series(clickData):
    
    #print('callback trigerred clicked on the rsqa map !!')
    map_fig = figures5["map"]

    if not clickData:
        return go.Figure(),"Cliquez sur une station pour plus de details", map_fig # Return an empty figure if nothing is clicked
    #print(clickData["points"][0]["customdata"])
    # Extract stationId from clicked marker
    station_name = clickData["points"][0]["customdata"][0]  # Assuming stationId is stored as first element in customdata
    df = data5['df']
    # Filter dataset based on stationId
    filtered_df = df[df["nom"] == station_name]

    colors = {"Bon": "green", "Acceptable": "orange", "Mauvais": "red"}
    filtered_df['colors'] = filtered_df['quality_cat'].map(colors)
    #print(filtered_df.head(5))
    # Create updated line figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=filtered_df["date"], 
        y=filtered_df["valeur"], 
        mode="lines",
        line=dict(color="black", width=2),
        customdata=filtered_df[["quality_cat", "colors", "polluant"]].values.tolist(),
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br><span style='background-color:%{customdata[1]}; padding:5px;'>%{customdata[0]} : %{y} indice atteint pour polluant %{customdata[2]}</span><extra></extra>",
        hoverlabel=dict(
            bgcolor=filtered_df['colors'],  # Use color from customdata
            font_size=12,
            font_color="white"  # Ensure readability
        ),
    ))
    fig.update_layout(
    xaxis=dict(
        showticklabels=True,  # Hide labels
        tickmode="auto",  # Auto ticks based on data range
        tickformat="%b",  # Show month abbreviations (e.g., Jan, Feb) if needed
        showgrid=True,  # Ensure grid lines are visible
        dtick="M1"  # A grid mark for each month
        )
    )
    title = f"IQA journalier de la station {station_name} en 2024"
        
    stats_df= data5['df_stats']
    for _, row in stats_df.iterrows():
        map_fig = add_bars(map_fig, stats_df, row["stationId"], scale=0.00015)  # Réduction de la hauteur
        
    
    return fig,title,map_fig

    

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
                text-align: center;
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
    app.run(debug=True)