
import dash
from dash import dcc, html
import pandas as pd
import plotly.graph_objects as go
import os

# Use optimized data files
DATA_PATH = "data/optimized" if os.path.exists("data/optimized") else "../data/optimized"

# Load the pre-aggregated data instead of processing the raw CSV
df_merged = pd.read_csv(os.path.join(DATA_PATH, "arbres_aggregated.csv"))
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
