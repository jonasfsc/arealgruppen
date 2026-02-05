import streamlit as st
import pandas as pd
import pydeck as pdk
import geopandas as gpd
import json

crs_plot = "EPSG:4326"


st.set_page_config(layout="wide")
st.title("Stasjoner med hyppige avganger")
st.subheader(
    "Avganger fra samme holdeplass minst hvert 10 / 15 min i intervallet for buss / skinnegående"
)


@st.cache_data
def load_data():
    gdf = gpd.read_file("buffrede_sentrumssoner.gpkg")
    gdf["name"] = gdf["område"] + " - " + gdf["kommunenavn"]
    if gdf.crs != crs_plot:
        gdf = gdf.to_crs(crs_plot)

    df_7_20 = pd.read_parquet(
        "stasjoner_med_frekvens_10_15_7_20.parquet",
        columns=[
            "parent_station",
            "name",
            "route_type",
            "location_longitude",
            "location_latitude",
            "radius",
        ],
    )

    df_7_18 = pd.read_parquet(
        "stasjoner_med_frekvens_10_15_7_18.parquet",
        columns=[
            "parent_station",
            "route_type",
            "name",
            "location_longitude",
            "location_latitude",
            "radius",
        ],
    )
    # "Vask" dataene for Pydeck med en gang (JSON-trikset)
    # Dette gjør at selve kartvisningen går mye raskere senere
    # clean_data1 = json.loads(gdf1.to_json())
    # clean_data2 = json.loads(gdf2.to_json())

    return gdf, df_7_18, df_7_20


# Kall funksjonen i hovedkoden
gdf, df_7_18, df_7_20 = load_data()


# 2. Sidebar for valg av lag
st.sidebar.header("Velg kartlag")
show_sentrum = st.sidebar.checkbox("Sentrumssoner SSB + 1000 m gangvei", value=True)

show_busstasjoner_7_18 = st.sidebar.checkbox(
    "Busstasjoner med høy frekvens 7-18", value=False
)
# show_busstasjoner_7_20 = st.sidebar.checkbox(
#     "Busstasjoner med høy frekvens 7-20", value=False
# )
# show_skinnestasjoner_7_18 = st.sidebar.checkbox(
#     "Skinnegående med høy frekvens stasjoner 7-18", value=False
# )
# show_skinnestasjoner_7_20 = st.sidebar.checkbox(
#     "Skinnegående med høy frekvens stasjoner 7-20", value=False
# )


# 3. Definer lagene
layers = []

if show_sentrum:
    layers.append(
        pdk.Layer(
            "GeoJsonLayer",
            gdf,
            opacity=0.5,
            get_fill_color=[20, 100, 200, 150],
            get_line_color=[255, 255, 255],
            pickable=True,
            stroked=True,
            filled=True,
        )
    )


# if show_busstasjoner_7_20:
#     # Lager en kopi med senterpunkter for demonstrasjon
#     layers.append(
#         # pdk.Layer(
#         #     "ScatterplotLayer",
#         #     df_7_20.query("route_type=='Bus'"),
#         #     stroked=True,
#         #     get_line_width=3,
#         #     get_position=["location_longitude", "location_latitude"],
#         #     get_fill_color=[255, 150, 0, 40],
#         #     get_line_color=[255, 150, 0, 200],
#         #     get_radius="radius",
#         #     pickable=True,
#         # )
#         pdk.Layer(
#             "GeoJsonLayer",
#             data=map_data,  # Bruk den rene JSON-ordboken her
#             get_fill_color="[200, 30, 0, 160]",  # Eksempel på farge
#             pickable=True,
#             auto_highlight=True,
#         )
#     )

# if show_skinnestasjoner_7_20:
#     # Lager en kopi med senterpunkter for demonstrasjon
#     layers.append(
#         pdk.Layer(
#             "ScatterplotLayer",
#             df_7_20.query("route_type!='Bus'"),
#             stroked=True,
#             get_line_width=3,
#             get_position=["location_longitude", "location_latitude"],
#             get_fill_color=[68, 79, 85, 40],
#             get_line_color=[68, 79, 85, 200],
#             get_radius="radius",
#             pickable=True,
#         )
#     )


if show_busstasjoner_7_18:
    # Lager en kopi med senterpunkter for demonstrasjon
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            df_7_18.query("route_type=='Bus'"),
            stroked=True,
            get_line_width=8,
            get_position=["location_longitude", "location_latitude"],
            get_fill_color=[255, 0, 0, 0],
            get_line_color=[255, 0, 0, 255],
            get_radius="radius",
            pickable=True,
        )
    )

# if show_skinnestasjoner_7_18:
#     # Lager en kopi med senterpunkter for demonstrasjon
#     layers.append(
#         pdk.Layer(
#             "ScatterplotLayer",
#             df_7_18.query("route_type!='Bus'"),
#             stroked=True,
#             get_line_width=8,
#             get_position=["location_longitude", "location_latitude"],
#             get_fill_color=[0, 255, 0, 0],
#             get_line_color=[0, 255, 0, 255],
#             get_radius="radius",
#             pickable=True,
#         )
#     )


tooltip = {
    "html": "<b>Navn:</b> {name}",
    "style": {"backgroundColor": "steelblue", "color": "white"},
}

# 4. Sett opp kartet
view_state = pdk.ViewState(latitude=60, longitude=10, zoom=6, pitch=0)

st.pydeck_chart(
    pdk.Deck(
        layers=layers, initial_view_state=view_state, tooltip=tooltip, map_style=None
    )
)
