import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import geopandas as gpd

# --------------------------------------------------------------------
# 1) Lecture + reprojection
# --------------------------------------------------------------------
chemin_geojson = r"../data/taux_veg.geojson"
gdf = gpd.read_file(chemin_geojson)

if gdf.crs is None:
    gdf.set_crs(epsg=2950, inplace=True)
gdf_4326 = gdf.to_crs(epsg=4326)
geojson_data = json.loads(gdf_4326.to_json())

# --------------------------------------------------------------------
# 2) DataFrame
# --------------------------------------------------------------------
df = gdf_4326.copy()
if "CODEID" not in df.columns:
    df["CODEID"] = range(1, len(df)+1)
if "Veg_km2" not in df.columns:
    df["Veg_km2"] = 0
if "Min_km2" not in df.columns:
    df["Min_km2"] = 0
if "NOM" not in df.columns:
    df["NOM"] = "Inconnu"

if "Veg_Taux" not in df.columns:
    total = (df["Veg_km2"] + df["Min_km2"]).replace(0,1)
    df["Veg_Taux"] = (df["Veg_km2"] / total) * 100

df["CODEID"] = df["CODEID"].astype(int)

# Si besoin : eau / non classé
if "Eau_km2" not in df.columns:
    df["Eau_km2"] = 0
if "NonCl_km2" not in df.columns:
    df["NonCl_km2"] = 0

# --------------------------------------------------------------------
# 3) Figure carte (choropleth_map)
# --------------------------------------------------------------------
fig_map = px.choropleth_map(
    df,
    geojson=geojson_data,
    locations="CODEID",
    featureidkey="properties.CODEID",
    color="Veg_Taux",
    hover_name="NOM",
    hover_data={
        "Veg_km2": ":.2f",
        "Min_km2": ":.2f",
        "CODEID": False
    },
    labels={"Veg_km2":"km2 Vég.","Min_km2":"km2 Min."},
    map_style="open-street-map",
    center={"lat":45.55, "lon":-73.65},
    zoom=9,
    color_continuous_scale="Greens",
    range_color=(0,100)
)
fig_map.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0},
    hovermode="closest",
    coloraxis_showscale=True
)

# --------------------------------------------------------------------
# 4) Diagramme en secteurs initial
# --------------------------------------------------------------------
quartier_init = df.iloc[0]
autres_init = quartier_init["Eau_km2"] + quartier_init["NonCl_km2"]

labels = ["Végétale", "Minérale", "Autres"]
values_init = [
    quartier_init["Veg_km2"],
    quartier_init["Min_km2"],
    autres_init
]

fig_pie = go.Figure(data=[
    go.Pie(
        labels=labels,
        values=values_init,
        # On désactive le texte auto par défaut
        textinfo="none",
        # On veut étiquettes + km²
        texttemplate="%{label}\n%{value:.2f} km²",
        # On peut placer le texte en dehors du camembert
        textposition="outside"
    )
])
# Mise à jour du layout (titre, marge, pas de légende)
fig_pie.update_layout(
    title={
        "text": f"{quartier_init['NOM']}",
        "x":0.5,
        "y":0.88,
        "xanchor":"center",
        "yanchor":"top"
    },
    margin={"t":60},
    showlegend=False
)

# --------------------------------------------------------------------
# 5) Application Dash
# --------------------------------------------------------------------
app = dash.Dash(__name__)

app.layout = html.Div(
    style={"display":"flex", "flexDirection":"row"},
    children=[
        # Colonne gauche (1/3): Titre + Pie Chart
        html.Div(
            style={"width":"33%", "padding":"10px"},
            children=[
                html.H1(
                    "Mon quartier est-il vert ?",
                    style={"textAlign":"center", "margin":"0 0 20px 0"}
                ),
                dcc.Graph(
                    id="pie_chart",
                    figure=fig_pie,
                    style={"height":"80vh"}
                )
            ]
        ),
        # Colonne droite (2/3): Carte
        html.Div(
            style={"width":"67%", "padding":"10px"},
            children=[
                html.H3("Proportion de surface végétale par arrondissement"),
                dcc.Graph(
                    id="map",
                    figure=fig_map,
                    style={"height":"80vh"},
                    hoverData=None
                )
            ]
        )
    ]
)

# --------------------------------------------------------------------
# 6) Callback : survol => maj du Pie Chart
# --------------------------------------------------------------------
@app.callback(
    Output("pie_chart","figure"),
    Input("map","hoverData")
)
def update_pie_on_hover(hoverData):
    if not hoverData:
        return fig_pie

    try:
        codeid = hoverData["points"][0]["location"]
    except (IndexError, KeyError, TypeError):
        return fig_pie

    row_df = df.loc[df["CODEID"] == codeid]
    if row_df.empty:
        return fig_pie

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

# --------------------------------------------------------------------
# 7) Lancement
# --------------------------------------------------------------------
if __name__=="__main__":
    app.run(debug=True)
