import streamlit as st
import pandas as pd
import pydeck as pdk
import geopandas as gpd
import json
import os
import numpy as np


crs_plot = "EPSG:4326"
crs_norge = "EPSG:25833"

st.set_page_config(layout="wide")
st.title("Stasjoner med hyppige avganger")
st.subheader(
    "Avganger fra samme holdeplass minst hvert 10 / 15 min i intervallet for buss / skinnegående"
)

current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "buffrede_sentrumssoner.gpkg")


class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)


@st.cache_data
def load_data():
    # 1. Last Sentrumssoner
    gdf = gpd.read_file(file_path, engine="pyogrio")
    gdf["name"] = gdf["område"].astype(str) + " - " + gdf["kommunenavn"].astype(str)
    if gdf.crs != crs_plot:
        gdf = gdf.to_crs(crs_plot)

    gdf["geometry"] = gdf.to_crs(crs_norge).simplify(10).to_crs(crs_plot)
    # "Vask" med NpEncoder for å unngå ndarray-feilen
    # Vi bruker __geo_interface__ som er en renere vei til JSON for GeoPandas
    # clean_gdf = json.loads(json.dumps(gdf.__geo_interface__, cls=NpEncoder))

    # 2. Last Parquet-filer
    df_7_18 = pd.read_parquet("stasjoner_med_frekvens_10_15_7_18.parquet")
    df_7_18 = df_7_18.drop(columns=["color"])
    gdf_7_18 = gpd.GeoDataFrame(
        df_7_18,
        geometry=gpd.points_from_xy(
            df_7_18["location_longitude"], df_7_18["location_latitude"]
        ),
        crs=crs_plot,
    )
    gdf_7_18["geometry"] = gdf_7_18.to_crs(crs_norge).buffer(500).to_crs(crs_plot)

    df_7_20 = pd.read_parquet("stasjoner_med_frekvens_10_15_7_20.parquet")

    gdf_7_20 = gpd.GeoDataFrame(
        df_7_20,
        geometry=gpd.points_from_xy(
            df_7_20["location_longitude"], df_7_20["location_latitude"]
        ),
        crs=crs_plot,
    )

    return gdf, gdf_7_18, gdf_7_20


# Hent ferdigvaskede data
gdf, gdf_7_18, gdf_7_20 = load_data()


# --- Sidebar ---
st.sidebar.header("Velg kartlag")
show_sentrum = st.sidebar.checkbox("Sentrumssoner SSB + 1000 m gangvei", value=True)
show_busstasjoner_7_18 = st.sidebar.checkbox(
    "Busstasjoner med høy frekvens 7-18", value=False
)

# --- Lag ---
layers = []

if show_sentrum:
    layers.append(
        pdk.Layer(
            "GeoJsonLayer",
            gdf,
            opacity=0.5,
            get_fill_color=[20, 100, 200, 150],
            get_line_color=[255, 255, 255],
        )
    )

if show_busstasjoner_7_18:
    layers.append(
        pdk.Layer(
            "GeoJsonLayer",
            gdf_7_18.query("route_type=='Bus'"),
            stroked=True,
            get_line_width=8,
            get_fill_color=[255, 0, 0, 0],
            get_line_color=[255, 0, 0, 255],
        )
    )


initial_view = pdk.ViewState(longitude=10, latitude=59.9, zoom=8)

r = pdk.Deck(layers=layers, initial_view_state=initial_view, map_style=None)

st.pydeck_chart(r)
