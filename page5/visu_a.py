import dash
from dash import Dash, dcc, html, Input, Output
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import json
import copy
import logging
logging.basicConfig(level=logging.DEBUG)
import geopandas as gpd
import plotly.graph_objects as go
from shapely.geometry import shape
from dash_extensions import EventListener

# Function for data loading
POLLUTANT_FULL_NAMES = {
    "NO2": "dioxyde d’azote",
    "O3": "Ozone",
    "PM": "Particules fines",
    "SO2": "Dioxyde de soufre"
}
def load_page5_data():
    import os
    if os.path.exists("data/rsqa-indice-qualite-air-station-2022-2024.csv"):
        base_path = "data/"
    else:
        base_path = "../data/"
    csv_path = os.path.join(base_path, "rsqa-indice-qualite-air-station-2022-2024.csv")
    
    base_path="data/"
    stations_filename = 'liste-des-stations-rsqa.csv'
    if  os.path.exists(os.path.join(base_path, stations_filename)):
        stations_filepath=os.path.join(base_path,stations_filename)

    else:
        base_path = "../data/"
        stations_filepath=os.path.join(base_path,stations_filename)
            
    df_stations_info = pd.read_csv(stations_filepath)
    df = pd.read_csv(csv_path, parse_dates=["date"])
    
    # keep only data from 2024
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == 2024].copy()
    #print(f'liste de tous les polluants mesurés {df['polluant'].unique()}')
    # get a list of all the polluants mesured in each station
    polluant_dict = df.groupby("stationId")["polluant"].unique().apply(list).to_dict()
    df["polluants_list"] = df["stationId"].map(polluant_dict).apply(lambda x: x if isinstance(x, list) else [])
    df["polluants_list"] = df["polluants_list"].apply(lambda x: ', '.join(x))
    # get only one value per day, the one with the highest value
    df = df.loc[df.groupby(["stationId", "date"])["valeur"].idxmax()]
    
    geojson_station_path = os.path.join(base_path, "updated_montreal.json")
    with open(geojson_station_path, "r", encoding="utf-8") as f:
        geojson_station_path_data = json.load(f)
        
    df = df.merge(  df_stations_info[["numero_station", "nom"]], 
                    left_on="stationId", right_on="numero_station", 
                    how="left").drop(columns=["numero_station"])
    
    df["nom"] = df["nom"].str.replace("Saint", "St")
    df.loc[df["nom"] == "Hochelaga-Maisonneuve", "nom"] = "Maisonneuve"
    
    
    # maximum catégorisation et comptage
    def cat(v):
        return "Bon" if v<=25 else "Acceptable" if v<=50 else "Mauvais"
    df["quality_cat"] = df["valeur"].map(cat)
    
    cnt = ( df.pivot_table(index="stationId", columns="quality_cat", aggfunc="size", fill_value=0).reset_index())
    
    # ajoute coordonnées + adresse
    coords = (
        df[["stationId","nom","adresse","latitude","longitude","polluants_list"]]
        .drop_duplicates("stationId")
    )
    df_stats =  coords.merge(cnt, on="stationId", how="left").fillna(0)

    return {
        'df': df,
        'df_stats':df_stats,
        'geojson_station_data': geojson_station_path_data
    }


def create_base_map(geojson, stats_df):
    fig = go.Figure()

    # 1) fond choropleth (Arrondissements)
    fig.add_trace(go.Choroplethmapbox(
        geojson=geojson,
        locations=[f["properties"]["NOM"] for f in geojson["features"]],
        z=[1]*len(geojson["features"]),
        featureidkey="properties.NOM",
        colorscale=[[0,"rgb(128,150,128)"],[1,"rgb(128,150,128)"]],
        showscale=False,
        marker_line_color="black",
        marker_line_width=1,
        hoverinfo="skip"
    ))

    # 2) points pour chaque station, on stocke le triplet [id, bon, acc, mau] dans customdata
    stats_df["custom"] = stats_df[["stationId","Bon","Acceptable","Mauvais","nom"]].values.tolist()
    fig.add_trace(go.Scattermapbox(
        lat=stats_df["latitude"],
        lon=stats_df["longitude"],
        mode="markers",
        marker=dict(size=12, color="black"),
        customdata=stats_df[["nom", "Bon", "Acceptable", "Mauvais"]].values.tolist(),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} bon jours, %{customdata[2]} jours acceptables et %{customdata[3]} jours mauvais<extra></extra>",
        
        showlegend=False
    ))
    
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_center={"lat":45.55,"lon":-73.65},
        mapbox_zoom=9.9,
        margin=dict(l=0,r=0,t=0,b=0),
        height=600,
        dragmode=False
    )
    # add a annotation in the upper left corner for explaining the polluants abreviations
    fig.update_layout(
        annotations=[
            # Title of the annotation
            dict(
                x=0.01, y=0.99,  # Upper-left corner
                xref="paper", yref="paper",
                text="<b>Descriptif des sigles des polluants mesurés</b>",
                showarrow=False,
                font=dict(size=14, color="black")
            ),
            # List of pollutants (formatted)
            dict(
                x=0.01, y=0.95,
                xref="paper", yref="paper",
                text="<br>".join([f"• <b>{abbr}:</b> {name}" for abbr, name in POLLUTANT_FULL_NAMES.items()]),
                showarrow=False,
                align="left",
                font=dict(size=12, color="black")
            )
        ],
    )

    return fig

def add_bars(   fig, stats_df, station_id,
                scale=0.00009,   # hauteur = jours * scale
                dx=0.01,         # espacement horizontal ≃ 1 km
                zoom=10,
                ):
    """
    Dessine trois segments verticaux côte à côte pour Bon / Acceptable / Mauvais.
    """
    row = stats_df.loc[stats_df["stationId"] == station_id].iloc[0]
    lon0, lat0 = row["longitude"], row["latitude"]
    colors = {"Bon": "green", "Acceptable": "orange", "Mauvais": "red"}
    cats   = ["Bon", "Acceptable", "Mauvais"]
    if row['nom']=='Maisonneuve':
        lon0+=0.05
        lat0+=-0.01
    if row['nom']=='St-Dominique':
        lon0+=0.04
        lat0-=0.03
    if row['nom']=='York/Roberval':
        lon0-=0.04
        lat0-=0.03  
        
    offset_rect_polluants = 0.001 * 10/zoom
    offset_rect_nom = 0.008 * 10/zoom
    offset_chart = 0.020 *10/zoom
    offset_txt_polluants = offset_rect_polluants+ (offset_rect_nom-offset_rect_polluants)/2
    
    offset_txt_nom = offset_rect_nom+ (offset_chart-offset_rect_nom)/2
    
    for idx, cat in enumerate(cats):
        jours = int(row.get(cat, 0))
        if jours <= 0:
            continue
        # calcul des positions
        lon_shift = lon0 + (idx - 1) * dx *10/zoom  # -dx, 0, +dx
        lat_end   = lat0  + jours * scale

        fig.add_trace(go.Scattermapbox(
            lon=[lon_shift, lon_shift],
            lat=[lat0+offset_chart, lat_end+offset_chart],
            mode="lines+text",
            textposition="top center",
            textfont=dict(size=12, color=colors[cat]),
            line=dict(width=14, color=colors[cat]),  # plus large = effet "barre"
            hoverinfo='skip',
            showlegend=False
        ))
        
    # Ajout d'un rectangle gris sous les barres avec le nom de la station sous les barres
    fig.add_trace(go.Scattermapbox(
        lon=[lon0, lon0], lat=[lat0+offset_rect_nom, lat0 + offset_chart],  
        mode="lines",
        text=["", row["nom"]],
        textposition="top center",
        textfont=dict(size=14, color="white"),
        line=dict(width=120, color="grey"), 
        showlegend=False,
        hoverinfo="skip"
    ))
    
    fig.add_trace(go.Scattermapbox(
        lon=[lon0, lon0], lat=[lat0+offset_rect_polluants, lat0 + offset_rect_nom], 
        mode="lines",
        text=["", row["polluants_list"]],
        textposition="top center",
        textfont=dict(size=12, color="white"),
        line=dict(width=120, color="lightgrey"),
        hoverinfo="skip", 
        showlegend=False
    ))
    # add polluant text
    fig.add_trace(go.Scattermapbox(
        lon=[lon0], lat=[lat0 + offset_txt_polluants],  # Position at the top of the line
        mode="text",
        text=[row["polluants_list"]],
        textposition="middle center",
        textfont=dict(size=10, color="black"),
        hoverinfo="skip",
        showlegend=False
    ))
    #add station name
    fig.add_trace(go.Scattermapbox(
        lon=[lon0], lat=[lat0 + offset_txt_nom],  # Position at the top of the line
        mode="text",
        text=[row["nom"]],
        textposition="middle center",
        textfont=dict(size=11, color="white"),
        hoverinfo="skip",
        showlegend=False
    ))
    #print(fig.layout.annotations)

    return  fig

def create_page5_figures(data):
    df= data["df"]
    geojson=data["geojson_station_data"]
    stats_df=data['df_stats']
    base_map = create_base_map(geojson, stats_df)
    # on renvoie aussi stats_df pour la callback
    return {"map": base_map, "stats": stats_df}
