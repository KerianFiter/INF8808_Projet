import dash
from dash import Dash, dcc, html, Input, Output
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import json
import copy

import geopandas as gpd
import plotly.graph_objects as go
from shapely.geometry import shape
from dash_extensions import EventListener

# Function for data loading

def load_page6_data():
    import os
    if os.path.exists("data/rsqa-indice-qualite-air-station-2022-2024 (3).csv"):
        base_path = "data/"
    else:
        base_path = "../data/"
    csv_path = os.path.join(base_path, "rsqa-indice-qualite-air-station-2022-2024 (3).csv")
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = df[df["date"].dt.year == 2024].copy()
    df['day'] = df['date'].dt.date
    geojson_station_path = os.path.join(base_path, "montreal.json")
    with open(geojson_station_path, "r", encoding="utf-8") as f:
        geojson_station_path_data = json.load(f)
    return {
        'df': df,
        'geojson_station_data': geojson_station_path_data
    }
def compute_stats(df):
    # moyenne journalière, catégorisation et comptage
    daily = df.groupby(["stationId","day"])["valeur"].mean().reset_index()
    def cat(v):
        return "Bon" if v<=25 else "Acceptable" if v<=50 else "Mauvais"
    daily["quality_cat"] = daily["valeur"].map(cat)
    cnt = (
        daily
        .pivot_table(index="stationId", columns="quality_cat", aggfunc="size", fill_value=0)
        .reset_index()
    )
    # ajoute coordonnées + adresse
    coords = (
        df[["stationId","adresse","latitude","longitude"]]
        .drop_duplicates("stationId")
    )
    return coords.merge(cnt, on="stationId", how="left").fillna(0)

def create_base_map(geojson, stats_df):
    fig = go.Figure()

    # 1) fond choropleth (Arrondissements)
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=[f["properties"]["NOM"] for f in geojson["features"]],
        z=[1]*len(geojson["features"]),
        featureidkey="properties.NOM",
        colorscale=[[0,"rgb(0,128,128)"],[1,"rgb(0,128,128)"]],
        showscale=False,
        marker_line_color="white",
        marker_line_width=1,
        hoverinfo="skip"
    ))
    # 2) points pour chaque station, on stocke le triplet [id, bon, acc, mau] dans customdata
    stats_df["custom"] = stats_df[["stationId","Bon","Acceptable","Mauvais"]].values.tolist()
    fig.add_trace(go.Scattermapbox(
        lat=stats_df["latitude"],
        lon=stats_df["longitude"],
        mode="markers",
        marker=dict(size=8, color="orange"),
        customdata=stats_df["custom"],
        hovertemplate="<b>%{customdata[0]}</b><extra></extra>",
        showlegend=False
    ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat":45.55,"lon":-73.65},
        mapbox_zoom=10,
        margin=dict(l=0,r=0,t=0,b=0),
        height=600
    )
    return fig

def add_bars_on_hover(fig, stats_df, station_id,
                      scale=0.00015,  # hauteur = jours * scale
                      dx=0.0004       # espacement horizontal
                     ):
    row = stats_df.loc[stats_df["stationId"]==station_id].iloc[0]
    lon0, lat0 = row["longitude"], row["latitude"]
    colors = {"Bon":"green","Acceptable":"orange","Mauvais":"red"}
    for i, cat in enumerate(["Bon","Acceptable","Mauvais"]):
        h = row.get(cat,0) * scale
        lon_shift = lon0 + (i-1)*dx
        fig.add_trace(go.Scattermapbox(
            lon=[lon_shift, lon_shift],
            lat=[lat0,       lat0 + h],
            mode="lines",
            line=dict(width=8, color=colors[cat]),
            hoverinfo="text",
            hovertext=f"{cat} : {int(row[cat])} jour{'s' if row[cat]>1 else ''}",
            showlegend=False
        ))
    return fig
def create_page6_figures(data):
    df= data["df"]
    geojson=data["geojson_station_data"]
    stats_df=compute_stats(df)
    base_map = create_base_map(geojson, stats_df)
    # on renvoie aussi stats_df pour la callback
    return {"map": base_map, "stats": stats_df}


if __name__ == "__main__":
    app = Dash(__name__)

    # Load data and create figures
    data = load_page6_data()
    figures = create_page6_figures(data)

    # Layout
    app.layout = html.Div(
        style={"display": "flex", "flexDirection": "row"},
        children=[
            html.Div(
                style={"width": "33%", "padding": "10px"},
                children=[
                    html.H1(
                        "Station dans mon quartier",
                        style={"textAlign": "center", "margin": "0 0 20px 0"}
                    ),
                    html.Div(id='info-text-stations')
                ]
            ),
            html.Div(
                style={"width": "67%", "padding": "10px", "height": "80vh", "overflow": "visible"},
                children=[
                    html.H3("Parcelles de stations de montréal"),
                    dcc.Graph(
                        id="iqa_map",
                        figure=figures['map'],
                        style={"height": "100%", "width": "100%"},
                        config={'scrollZoom': True, 'displayModeBar': False, 'editable': False}
                    ),
                    dcc.Graph(
                        id="bar-chart",
                        figure=go.Figure().update_layout(
                            title="Survolez une station",
                            xaxis_title="Qualité",
                            yaxis_title="Nombre de jours"
                        ),
                        config={'displayModeBar': False}
                    ),

                ],className="viz-column-wide"
            )
        ]
    )
# --------------------------------------------------------------------
# 4. Callback au survol pour le stacked bar chart
# --------------------------------------------------------------------
    stats_df = figures["stats"]
    base_map = figures["map"]


    @app.callback(
        Output("iqa_map", "figure"),
        Input("iqa_map", "hoverData")
    )
    def on_hover_air(hoverData):
        fig = copy.deepcopy(base_map)
        if hoverData and hoverData.get("points"):
            # extraire stationId depuis customdata
            for pt in hoverData["points"]:
                cd = pt.get("customdata")
                if cd:
                    station_id = cd[0]
                    # superposer les 3 barres
                    fig = add_bars_on_hover(fig, stats_df, station_id)
                    break
        return fig


    app.run(debug=True)
