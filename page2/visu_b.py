
import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go

df = pd.read_csv("arbres-publics.csv", engine="python", on_bad_lines="skip")

df["ARROND_NOM"] = df["ARROND_NOM"].str.strip().str.title()

df_total = df.groupby("ARROND_NOM").size().reset_index(name="Arbres")

df_remarquables = (
    df[df["Arbre_remarquable"] == "O"]
    .groupby("ARROND_NOM")
    .size()
    .reset_index(name="Arbres_remarquables")
)

df_merged = pd.merge(df_total, df_remarquables, on="ARROND_NOM", how="left")
df_merged["Arbres_remarquables"] = df_merged["Arbres_remarquables"].fillna(0).astype(int)

df_merged["Arbres_non_remarquables"] = df_merged["Arbres"] - df_merged["Arbres_remarquables"]

df_merged = df_merged.sort_values("Arbres")

customdata = df_merged[["Arbres", "Arbres_remarquables", "ARROND_NOM"]].values

fig = go.Figure()

fig.add_trace(go.Bar(
    x=df_merged["ARROND_NOM"],
    y=df_merged["Arbres_non_remarquables"],
    marker_color="#90EE90",
    name="Arbres non remarquables",
    showlegend=False,
    hoverinfo="skip",
))

fig.add_trace(go.Bar(
    x=df_merged["ARROND_NOM"],
    y=df_merged["Arbres_remarquables"],
    marker_color="#006400",
    name="",
    showlegend=False,
    customdata=customdata,
    hovertemplate=(
        "<b>%{customdata[2]}</b><br>"          
        "Arbres : %{customdata[0]}<br>"
        "Arbres remarquables : %{customdata[1]}"
        "<extra></extra>"
    )
))

fig.update_layout(
    barmode="stack",
    hovermode="x",
    xaxis_title="Quartier",
    yaxis_title="Arbres",
    margin=dict(l=60, r=30, t=30, b=80)
)
fig.update_xaxes(tickangle=45)


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H3("Comparaison des arbres par quartier (dont remarquables)"),
    dcc.Graph(figure=fig, style={"height": "75vh"})
])

if __name__ == "__main__":
    app.run(debug=True)
