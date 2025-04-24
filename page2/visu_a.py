from dash import Dash, dcc, html, Input, Output
import pandas as pd
import geopandas as gpd
import json
import plotly.express as px


df = pd.read_csv(
    "arbres-publics.csv",
    engine="python",
    on_bad_lines="skip"
)
df["cleaned"] = (
    df["ARROND_NOM"]
      .str.lower()
      .str.replace(r"[^a-z0-9]", "", regex=True)
)
tot = df.groupby("cleaned").size().reset_index(name="nb_arbres")
rem = (
    df[df["Arbre_remarquable"] == "O"]
      .groupby("cleaned")
      .size().reset_index(name="nb_remarquables")
)
stats = pd.merge(tot, rem, on="cleaned", how="left").fillna(0)
stats["nb_remarquables"] = stats["nb_remarquables"].astype(int)

gdf = gpd.read_file("montreal.json")
gdf = gdf.set_crs(epsg=4326) if gdf.crs is None else gdf.to_crs(epsg=4326)
gdf["cleaned"] = (
    gdf["NOM"]
       .str.lower()
       .str.replace(r"[^a-z0-9]", "", regex=True)
)
gdf = gdf.merge(stats, on="cleaned", how="left").fillna(0)
gdf["nb_arbres"]       = gdf["nb_arbres"].astype(int)
gdf["nb_remarquables"] = gdf["nb_remarquables"].astype(int)
gdf["fid"] = gdf.index.astype(str)               # ID unique


gj = json.loads(gdf.to_json())


fig = px.choropleth_mapbox(
    gdf,
    geojson=gj,
    locations="fid",
    featureidkey="properties.fid",
    color="nb_arbres",
    color_continuous_scale="Greens",
    range_color=(0, gdf["nb_arbres"].max()),
    mapbox_style="open-street-map",
    center={"lat": 45.5017, "lon": -73.5673},
    zoom=9,
    hover_name="NOM",
    hover_data={
        "nb_arbres": True,
        "nb_remarquables": True,
        "fid": False
    },
    labels={
        "nb_arbres": "Total arbres",
        "nb_remarquables": "Remarquables"
    }
)
fig.update_traces(marker_line_width=1, marker_line_color="gray")
fig.update_layout(
    margin={"l":0,"r":0,"t":40,"b":0},
    title="Arbres publics par arrondissement"
)


app = Dash(__name__)
app.layout = html.Div(style={"display":"flex"}, children=[
    # Carte à gauche
    html.Div(style={"width":"70%", "padding":"10px"}, children=[
        dcc.Graph(
            id="map_arbre",
            figure=fig,
            style={"height":"90vh"},
            config={"scrollZoom": True, "displayModeBar": False}
        )
    ]),
   
    html.Div(style={"width":"30%", "padding":"10px"}, children=[
        html.H2("Détails de l'arrondissement", style={"color":"#2a9d8f"}),
        html.Div("Cliquez sur un arrondissement pour voir les détails.", id="info")
    ])
])


@app.callback(
    Output("info", "children"),
    Input("map_arbre", "clickData")
)
def display_click_info(clickData):
    if not clickData or "points" not in clickData:
        return "Cliquez sur un arrondissement pour voir les détails."
    fid = clickData["points"][0].get("location")
    if fid is None:
        return "Aucune donnée disponible."
    row = gdf.loc[gdf["fid"] == fid].iloc[0]
    return html.Div([
        html.P(f"Arrondissement : {row['NOM']}"),
        html.P(f"Nombre d'arbres : {row['nb_arbres']}"),
        html.P(f"Arbres remarquables : {row['nb_remarquables']}")
    ])

if __name__ == "__main__":
    app.run(debug=True)
