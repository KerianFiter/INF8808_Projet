import unicodedata
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import json

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


df = pd.read_csv("arbres-publics.csv", engine="python", on_bad_lines="skip")

df["cleaned_name"] = df["ARROND_NOM"].apply(clean_string)

df_total = df.groupby("cleaned_name").size().reset_index(name="nb_arbres")

df_remarquables = (
    df[df["Arbre_remarquable"] == "O"]
    .groupby("cleaned_name")
    .size()
    .reset_index(name="nb_arbres_remarquables")
)

df_grouped = pd.merge(df_total, df_remarquables, on="cleaned_name", how="left")
df_grouped["nb_arbres_remarquables"] = df_grouped["nb_arbres_remarquables"].fillna(0)

df_grouped.rename(columns={
    "nb_arbres": "Nombre d'arbres",
    "nb_arbres_remarquables": "Nombre d'arbres remarquables"
}, inplace=True)

with open("quartiers_sociologiques_2014.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

for feature in geojson_data["features"]:
    original = feature["properties"]["Arrondissement"]
    cleaned = clean_string(original)
    feature["properties"]["cleaned_name"] = cleaned

geo_rows = []
for feat in geojson_data["features"]:
    original = feat["properties"]["Arrondissement"]
    cleaned = feat["properties"]["cleaned_name"]
    geo_rows.append({
        "original_name": original,
        "cleaned_name": cleaned
    })
geo_df = pd.DataFrame(geo_rows)

df_merged = pd.merge(
    geo_df,
    df_grouped,
    how="left",
    on="cleaned_name"
)


df_merged["Nombre d'arbres"] = df_merged["Nombre d'arbres"].fillna(0)
df_merged["Nombre d'arbres remarquables"] = df_merged["Nombre d'arbres remarquables"].fillna(0)

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


app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div(style={"display": "flex", "flexDirection": "row"}, children=[
        html.Div(
            style={"width": "70%", "padding": "10px"},
            children=[dcc.Graph(id="quartiers_map", figure=fig_map, style={"height": "80vh"})]
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

if __name__ == "__main__":
    app.run_server(debug=True)
