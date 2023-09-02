import base64

import altair as alt
import streamlit as st
import pandas as pd

import strava
from utils import find_default_publish_start_end_date
from pandas.api.types import is_numeric_dtype

st.set_page_config(
    page_title="Streamlit Activities analysis for Strava",
    page_icon=":safety_pin:",
)

strava_header = strava.header()

st.title(":safety_pin: Streamlit Activities analysis for Strava :safety_pin:")

strava_auth = strava.authenticate(header=strava_header, stop_if_unauthenticated=False)

if strava_auth is None:
    st.markdown("Click the \"Connect with Strava\" button at the top to login with your Strava account and get started.")
    st.stop()

# analysis on shoes
st.divider()
st.header("Display shoes analysis")
if 'athlete' not in st.session_state:
    athlete = strava.get_athlete_detail(strava_auth)
    st.session_state.athlete = athlete

if 'dict_shoes' not in st.session_state:
    shoes = strava.get_shoes(st.session_state.athlete)
    dict_shoes = {shoe["name"]: shoe["converted_distance"] for shoe in shoes}
    st.session_state.dict_shoes = dict_shoes

all_shoes_names = st.session_state.dict_shoes.keys()

selected_shoes = st.multiselect(
    label="Select columns to plot",
    options=all_shoes_names,
)

distances = [st.session_state.dict_shoes[shoe_name] for shoe_name in selected_shoes]
if selected_shoes:
    chart_data = pd.DataFrame({
        'index':selected_shoes,
        'kilometers':distances
    })
    st.bar_chart(chart_data)
else:
    st.write("No column(s) selected")

# get activities on a period
st.divider()
st.header("Display zones on a period")

default_start_date, default_end_date = find_default_publish_start_end_date()

col_start_date, col_end_date = st.columns(2)
with col_start_date:
    st.date_input("Start date", value=default_start_date, key="start_date")
with col_end_date:
    st.date_input("End date", value=default_end_date, key="end_date")
if st.session_state.start_date > st.session_state.end_date:
    st.error("Error: End date must fall after start date.")
else:
    st.session_state.activities = strava.get_activities_on_period(strava_auth, [], st.session_state.start_date, st.session_state.end_date, 1)

st.write(f"You got {len(st.session_state.activities)} activities")

activities_zones = {}
for activity in st.session_state.activities:
    if not activity["has_heartrate"]:
        continue
    try:
        st.session_state.activity_zones = strava.get_activity_zones(strava_auth, activity["id"])[0]["distribution_buckets"]
    except Exception as e:
        st.write(e)
    if not activities_zones:
        activities_zones = {idx: zone["time"] // 60 for idx, zone in enumerate(st.session_state.activity_zones)}
    else:
        for idx, zone in enumerate(st.session_state.activity_zones):
            activities_zones[idx] += (zone["time"] // 60)

zones_label = ["zone 1", "zone 2", "zone 3", "zone 4", "zone 5"]
zones_df = pd.DataFrame({
    'zones': zones_label,
    'minutes': activities_zones.values()
})

scale = alt.Scale(
    domain=zones_label,
    range=["#008000", "#ffcf3e", "#f67200", "#ee1010", "#3f2204"],
)
color = alt.Color("zones:N", scale=scale)

bars = (
    alt.Chart(zones_df)
    .mark_bar()
    .encode(
        x="zones",
        y="minutes",
        color=color,
    )
)

st.altair_chart(bars, theme="streamlit", use_container_width=True)