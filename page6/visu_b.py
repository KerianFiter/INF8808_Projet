import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import json
import geopandas as gpd
from shapely.geometry import shape
from dash_extensions import EventListener


#Chargement et reprojection des données géospatiales
chemin_geojson = r"../data/espace_vert.geojson"
gdf = gpd.read_file(chemin_geojson)

if gdf.crs is None:
    gdf.set_crs(epsg=2950, inplace=True)
espace_vert_gdf_4326 = gdf.to_crs(epsg=4326)
espace_vert_geojson_data = json.loads(espace_vert_gdf_4326.to_json())

chemin_geojson = r"../data/territoires_MTL_Clean.geojson"
gdf = gpd.read_file(chemin_geojson)

if gdf.crs is None:
    gdf.set_crs(epsg=2950, inplace=True)
territoires_MTL_Clean_gdf_4326 = gdf.to_crs(epsg=4326)
territoires_MTL_Clean_gdf_4326 = territoires_MTL_Clean_gdf_4326.drop(columns=["DATEMODIF"], errors="ignore")
territoires_MTL_Clean_geojson_data = json.loads(territoires_MTL_Clean_gdf_4326.to_json())