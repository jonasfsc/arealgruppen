import streamlit as st
import pandas as pd
import pydeck as pdk
import geopandas as gpd
import json
import os

crs_plot = "EPSG:4326"

st.set_page_config(layout="wide")
st.title("Stasjoner med hyppige avganger")
st.subheader(
    "Avganger fra samme holdeplass minst hvert 10 / 15 min i intervallet for buss / skinnegående"
)

current_dir = os.path.dirname(__file__)
file_path = os.path.join(current_dir, "buffrede_sentrumssoner.gpkg")


@st.cache_data
def load_data():
    # 1. Last Sentrumssoner
    gdf = gpd.read_file(file_path, engine="pyogrio")
    gdf["name"] = gdf["område"] + " - " + gdf["kommunenavn"]
    if gdf.crs != crs_plot:
        gdf = gdf.to_crs(crs_plot)

    # "Vask" GeoJSON for å unngå TypeError på Cloud
    clean_gdf = json.loads(gdf.to_json())

    # 2. Last Parquet-filer
    df_7_20 = pd.read_parquet("stasjoner_med_frekvens_10_15_7_20.parquet")

    df_7_18_raw = pd.read_parquet("stasjoner_med_frekvens_10_15_7_18.parquet")
    df_7_18_gpd = gpd.GeoDataFrame(
        df_7_18_raw,
        geometry=gpd.points_from_xy(
            df_7_18_raw["location_longitude"], df_7_18_raw["location_latitude"]
        ),
        crs=crs_plot,
    )
    # "Vask" denne også
    clean_df_7_18 = json.loads(df_7_18_gpd.to_json())

    return clean_gdf, clean_df_7_18, df_7_20


# Hent ferdigvaskede data
gdf_json, df_7_18_json, df_7_20 = load_data()

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
            gdf_json,  # Bruker vasket JSON
            opacity=0.5,
            get_fill_color=[20, 100, 200, 150],
            get_line_color=[255, 255, 255],
            pickable=True,
            stroked=True,
            filled=True,
        )
    )

if show_busstasjoner_7_18:
    layers.append(
        pdk.Layer(
            "GeoJsonLayer",
            df_7_18_json,  # Bruker vasket JSON
            stroked=True,
            get_line_width=8,
            get_fill_color=[255, 0, 0, 0],
            get_line_color=[255, 0, 0, 255],
            pickable=True,
        )
    )

tooltip = {
    "html": "<b>Navn:</b> {name}",
    "style": {"backgroundColor": "steelblue", "color": "white"},
}

view_state = pdk.ViewState(latitude=60, longitude=10, zoom=6, pitch=0)

# BRUK CARTO BASMAP FOR Å UNNGÅ MAPBOX TOKEN FEIL
st.pydeck_chart(
    pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="https://basemaps.cartocdn.com/gl/light-all-gl-style/style.json",
    )
)
