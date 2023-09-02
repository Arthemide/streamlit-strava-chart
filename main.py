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
athlete = strava.get_athlete_detail(strava_auth)
shoes = strava.get_shoes(athlete)

dict_shoes = {shoe["name"]: shoe["converted_distance"] for shoe in shoes}

all_shoes_names = dict_shoes.keys()
selected_shoes = st.multiselect(
    label="Select columns to plot",
    options=all_shoes_names,
)

distances = [dict_shoes[shoe_name] for shoe_name in selected_shoes]
if selected_shoes:
    chart_data = pd.DataFrame({
        'index':selected_shoes,
        'kilometers':distances
    })
    st.bar_chart(chart_data)
else:
    st.write("No column(s) selected")

# activity = strava.select_strava_activity(strava_auth)

# analysis on zones
# athlete_zones = strava.get_athlete_zones(strava_auth)
# if athlete_zones:
#     st.success("Athlete zones")
#     st.write(athlete_zones)


# get activities on a period
st.divider()
st.header("Display zones on a period")

start_date, end_date = find_default_publish_start_end_date()

col_start_date, col_end_date = st.columns(2)
with col_start_date:
    real_start_date = st.date_input("Start date", value=start_date, min_value=None, max_value=None, key=None)
with col_end_date:
    real_end_date = st.date_input("End date", value=end_date, min_value=None, max_value=None, key=None)
if real_start_date > real_end_date:
    st.error("Error: End date must fall after start date.")
else:
    activities = strava.get_activities_on_period(strava_auth, [], real_start_date, real_end_date, 1)

st.write(f"You got {len(activities)} activities")

activities_zones = {}
for activity in activities:
    if not activity["has_heartrate"]:
        continue
    try:
        activity_zones = strava.get_activity_zones(strava_auth, activity["id"])[0]["distribution_buckets"]
    except Exception as e:
        st.write(e)
    if not activities_zones:
        activities_zones = {idx: zone["time"] // 60 for idx, zone in enumerate(activity_zones)}
    else:
        for idx, zone in enumerate(activity_zones):
            activities_zones[idx] += (zone["time"] // 60)

zones_df = pd.DataFrame({
    'zones': ["zone 1", "zone 2", "zone 3", "zone 4", "zone 5"],
    'minutes': activities_zones.values()
})

scale = alt.Scale(
    domain=["zone 1", "zone 2", "zone 3", "zone 4", "zone 5"],
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