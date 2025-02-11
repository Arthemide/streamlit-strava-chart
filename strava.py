import base64
import os

import arrow
import httpx
import streamlit as st
from bokeh.models.widgets import Div
from dotenv import load_dotenv
from datetime import datetime
load_dotenv()

APP_URL = os.environ["APP_URL"]
STRAVA_CLIENT_ID = os.environ["STRAVA_CLIENT_ID"]
STRAVA_CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
STRAVA_AUTHORIZATION_URL = "https://www.strava.com/oauth/authorize"
STRAVA_API_BASE_URL = "https://www.strava.com/api/v3"
SCOPE = "activity:read_all,profile:read_all,activity:write"
DEFAULT_ACTIVITY_LABEL = "NO_ACTIVITY_SELECTED"
STRAVA_ORANGE = "#fc4c02"



@st.cache_data
def load_image_as_base64(image_path):
    with open(image_path, "rb") as f:
        contents = f.read()
    return base64.b64encode(contents).decode("utf-8")


def powered_by_strava_logo():
    base64_image = load_image_as_base64("./static/api_logo_pwrdBy_strava_horiz_light.png")
    st.markdown(
        f'<img src="data:image/png;base64,{base64_image}" width="100%" alt="powered by strava">',
        unsafe_allow_html=True,
    )

@st.cache_data
def authorization_url():
    request = httpx.Request(
        method="GET",
        url=STRAVA_AUTHORIZATION_URL,
        params={
            "client_id": STRAVA_CLIENT_ID,
            "redirect_uri": APP_URL,
            "response_type": "code",
            "approval_prompt": "auto",
            "scope": SCOPE
        }
    )

    return request.url


def login_header(header=None):
    strava_authorization_url = authorization_url()

    if header is None:
        base = st
    else:
        col1, _, _, button = header
        base = button

    with col1:
        powered_by_strava_logo()

    base64_image = load_image_as_base64("./static/btn_strava_connectwith_orange@2x.png")
    base.markdown(
        (
            f"<a href=\"{strava_authorization_url}\">"
            f"  <img alt=\"strava login\" src=\"data:image/png;base64,{base64_image}\" width=\"100%\">"
            f"</a>"
        ),
        unsafe_allow_html=True,
    )


def logout_header(header=None):
    if header is None:
        base = st
    else:
        _, col2, _, button = header
        base = button


    with col2:
        powered_by_strava_logo()

    if base.button("Log out"):
        js = f"window.location.href = '{APP_URL}'"
        html = f"<img src onerror=\"{js}\">"
        div = Div(text=html)
        st.bokeh_chart(div)


def logged_in_title(strava_auth, header=None):
    if header is None:
        base = st
    else:
        col, _, _, _ = header
        base = col

    first_name = strava_auth["athlete"]["firstname"]
    last_name = strava_auth["athlete"]["lastname"]
    col.markdown(f"*Welcome, {first_name} {last_name}!*")


@st.cache_data
def exchange_authorization_code(authorization_code):
    response = httpx.post(
        url="https://www.strava.com/oauth/token",
        json={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "code": authorization_code,
            "grant_type": "authorization_code",
        }
    )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError:
        st.error("Something went wrong while authenticating with Strava. Please reload and try again")
        st.experimental_set_query_params()
        st.stop()
        return

    strava_auth = response.json()

    return strava_auth

def authenticate(header=None, stop_if_unauthenticated=True):
    query_params = st.experimental_get_query_params()
    authorization_code = query_params.get("code", [None])[0]

    if authorization_code is None:
        authorization_code = query_params.get("session", [None])[0]

    if authorization_code is None:
        login_header(header=header)
        if stop_if_unauthenticated:
            st.stop()
        return
    else:
        logout_header(header=header)
        strava_auth = exchange_authorization_code(authorization_code)
        logged_in_title(strava_auth, header)
        st.experimental_set_query_params(session=authorization_code)

        return strava_auth


def header():
    col1, col2, col3 = st.columns(3)

    with col3:
        strava_button = st.empty()

    return col1, col2, col3, strava_button

def catch_strava_api_error(response):
    if response.status_code == 200:
        return
    st.write(response.status_code)
    if response.status_code == 401:
        st.error("You are not authorized to access this resource. Please relog yourself.")
        st.stop()
        return
    else:
        st.error(response)
        if response["errors"]:
            st.error(f"Something went wrong while fetching data from Strava. Please reload and try again (error message: {response['message']})")
            st.stop()
            return

def strava_call(auth, uri_params, params = None):
    access_token = auth["access_token"]
    response = httpx.get(
        url=f"{STRAVA_API_BASE_URL}/{uri_params}",
        params=params,
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )
    catch_strava_api_error(response)
    return response.json()

@st.cache_data
def get_athlete_detail(auth, page=1):
    return strava_call(auth, "athlete")

@st.cache_data
def get_shoes(athlete):
    return athlete["shoes"]

@st.cache_data
def get_activity(activity_id, auth):
    return strava_call(auth, f"activities/{activity_id}")

@st.cache_data
def get_activities_on_period(auth, activities, start_date, end_date, page):
    response = get_activities(auth, page)
    number_added = 0
    for activity in response:
        strava_start_date = datetime.strptime(activity["start_date"], '%Y-%m-%dT%H:%M:%SZ').date()
        if strava_start_date >= start_date and strava_start_date <= end_date:
            activities.append(activity)
            number_added += 1
    if number_added == 0:
        return activities
    else:
        return get_activities_on_period(auth, activities, start_date, end_date, page + 1)

@st.cache_data
def get_activities(auth, page=1):
    return strava_call(auth, f"athlete/activities", params={"page": page})

@st.cache_data
def get_activity_zones(auth, activity_id):
    return strava_call(auth, f"activities/{activity_id}/zones")

@st.cache_data
def get_athlete_zones(auth):
    return strava_call(auth, f"athlete/zones")

# @st.cache_data
# def get_all_activities(auth):
#     page = 1
#     activities = []
#     while True:
#         new_activities = strava_call(auth, f"athlete/activities", params={
#                 "page": page,
#                 "per_page": 200
#             })
#         activities.append(new_activities)
#         if len(new_activities) == 0:
#             break
#         page += 1
#
#     return activities

# def export_all_activities(auth):
#     activities = get_all_activities(auth=auth)
#     st.write(f"You got {len(activities)} activities")
#     with open('activities.json', 'w') as f:
#         json.dump(activities, f)
