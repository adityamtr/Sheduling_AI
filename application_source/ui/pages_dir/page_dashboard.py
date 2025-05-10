import datetime
import io
import json
import os
import os.path
import pickle
import re
import time

import pytz
import streamlit as st
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CREDENTIALS_FILE = 'secrets/credentials.json'
TOKEN_PICKLE_FILE = 'secrets/token.pickle'
SESSION_STATE_BACKUP_FILE = 'secrets/session_backup.json'  # For OAuth state persistence
REDIRECT_URI = 'http://localhost:8501/'  # Must match Google Cloud Console configuration

WORKING_HOUR_START = 9
WORKING_HOUR_END = 17
NUM_DAYS_TO_CHECK = 14


# --- Session State Backup ---
def backup_session_state_for_oauth():
    """Saves essential session data before OAuth redirect."""
    state_to_backup = {
        'transcript_data': st.session_state.get('transcript_data'),
        'analysis_results': st.session_state.get('analysis_results'),
        'show_auth_flow_intended': True,
        'auth_purpose': st.session_state.get('auth_purpose'),
    }
    try:
        with open(SESSION_STATE_BACKUP_FILE, 'w') as f:
            json.dump(state_to_backup, f)
    except Exception as e:
        st.error(f"Failed to backup session state: {e}")


def restore_session_state_after_oauth():
    """Loads backed-up session data after OAuth redirect, if available."""
    if os.path.exists(SESSION_STATE_BACKUP_FILE):
        try:
            with open(SESSION_STATE_BACKUP_FILE, 'r') as f:
                backed_up_state = json.load(f)
            for key, value in backed_up_state.items():
                st.session_state[key] = value
            os.remove(SESSION_STATE_BACKUP_FILE)
            return True
        except Exception as e:
            st.error(f"Failed to restore session state: {e}")
            if os.path.exists(SESSION_STATE_BACKUP_FILE):
                os.remove(SESSION_STATE_BACKUP_FILE)
    return False


# --- Placeholder Backend Functions ---
def analyse_transcripts(transcript_data_list):
    # Simulates backend transcript analysis
    st.info("Simulating transcript analysis...")
    results = {}
    scores = {}
    for item in transcript_data_list:
        client_name = item['client_name']
        content_len = len(item.get('content', ''))
        score = min(1.0, content_len / 1500.0 + 0.1)
        summary = f"Analysis for {client_name} (transcript: '{item['filename']}'). Length: {content_len}. "
        if score > 0.8:
            summary += "Very positive outlook."
        elif score > 0.5:
            summary += "Shows good potential."
        else:
            summary += "Further review suggested."
        results[client_name] = {'summary': summary, 'score': round(score, 2)}
        scores[client_name] = score
    results['priority_order'] = sorted(scores, key=scores.get, reverse=True)
    st.success("Transcript analysis complete.")
    return results


def schedule_meetings(analysis_results, free_slots_by_day):
    # Simulates meeting scheduling based on priority and availability
    st.info("Simulating meeting scheduling...")
    suggestions = []
    priority_list = analysis_results.get('priority_order', [])

    flat_slots = []
    for date_str in sorted(free_slots_by_day.keys()):
        for slot in free_slots_by_day[date_str]:
            flat_slots.append({'date': str(date_str),
                               'time': str(slot.split(' - ')[0]),
                               'slot_str': str(slot)})
    slot_idx = 0
    for client_name in priority_list:
        client_score = analysis_results.get(client_name, {}).get('score', 0)
        if slot_idx < len(flat_slots):
            slot = flat_slots[slot_idx]
            suggestions.append(f"**{str(client_name)}** (Score: {client_score:.2f}): "
                               f"Suggest on **{slot['date']} at {slot['time']}** (Slot: {slot['slot_str']})")
            slot_idx += 1
        else:
            suggestions.append(
                f"**{str(client_name)}** (Score: {client_score:.2f}): No more free slots available in the checked range.")
    st.success("Meeting scheduling simulation complete.")
    return suggestions if suggestions else ["No suitable meeting slots or clients to schedule."]


# --- Authentication & Calendar Utilities ---
def get_google_oauth_flow():
    return Flow.from_client_secrets_file(CREDENTIALS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)


def save_credentials(credentials):
    with open(TOKEN_PICKLE_FILE, 'wb') as token: pickle.dump(credentials, token)
    st.session_state.credentials = credentials


def load_credentials():
    if os.path.exists(TOKEN_PICKLE_FILE):
        with open(TOKEN_PICKLE_FILE, 'rb') as token: return pickle.load(token)
    return None


def clear_all_auth_state():
    """Clears all authentication, token, and OAuth related session state."""
    if os.path.exists(TOKEN_PICKLE_FILE): os.remove(TOKEN_PICKLE_FILE)
    keys_to_reset = ['credentials', 'user_timezone', 'free_slots_data', 'auth_purpose',
                     'auth_url', 'auth_flow_started', 'show_auth_flow_intended',
                     'oauth_state_param_generated', 'oauth_state_param_returned']  # For CSRF state if used
    for key in keys_to_reset:
        if key in st.session_state: del st.session_state[key]
    st.session_state.show_auth_flow = False
    if os.path.exists(SESSION_STATE_BACKUP_FILE): os.remove(SESSION_STATE_BACKUP_FILE)


def get_free_slots(busy_intervals, day_start_local, day_end_local):
    free_slots = []
    current_time = day_start_local
    for busy_start, busy_end in busy_intervals:
        bs_clamped = max(busy_start, day_start_local)
        be_clamped = min(busy_end, day_end_local)
        if current_time < bs_clamped:
            if bs_clamped > current_time: free_slots.append(
                f"{current_time.strftime('%H:%M')} - {bs_clamped.strftime('%H:%M')}")
        current_time = max(current_time, be_clamped)
    if current_time < day_end_local: free_slots.append(
        f"{current_time.strftime('%H:%M')} - {day_end_local.strftime('%H:%M')}")
    return free_slots


def fetch_calendar_free_slots(credentials):
    st.info("Fetching Google Calendar free slots...")
    free_slots_by_day = {}
    try:
        service = build('calendar', 'v3', credentials=credentials)

        user_tz_str = st.session_state.get('user_timezone_str')
        if not user_tz_str:
            timezone_fetched = False
            for attempt in range(3):  # Try up to 3 times
                try:
                    settings = service.settings().get(setting='timezone').execute()
                    user_tz_str = settings['value']
                    st.session_state.user_timezone_str = user_tz_str
                    timezone_fetched = True
                    break
                except HttpError as e:
                    st.warning(f"API error fetching timezone (attempt {attempt + 1}/3): {e}. Will retry...")
                    time.sleep(1 * (attempt + 1))
                except Exception as e:
                    st.warning(f"Error fetching timezone (attempt {attempt + 1}/3): {e}. Will retry...")
                    time.sleep(1 * (attempt + 1))

            if not timezone_fetched:
                st.warning("Could not reliably fetch user's timezone after multiple attempts. Defaulting to UTC.")
                user_tz_str = 'UTC'
                st.session_state.user_timezone_str = user_tz_str

        user_tz = pytz.timezone(user_tz_str)
        if user_tz_str != 'UTC':
            st.caption(f"Using calendar timezone: {user_tz_str}")

        now_local = datetime.datetime.now(user_tz)
        start_date = now_local.date()
        end_date = start_date + datetime.timedelta(days=NUM_DAYS_TO_CHECK)

        query_start_utc = user_tz.localize(datetime.datetime.combine(start_date, datetime.time.min)).astimezone(
            pytz.utc)
        query_end_utc = user_tz.localize(datetime.datetime.combine(end_date, datetime.time.min)).astimezone(pytz.utc)

        api_body = {"timeMin": query_start_utc.isoformat(), "timeMax": query_end_utc.isoformat(),
                    "timeZone": user_tz.zone, "items": [{"id": "primary"}]}

        busy_intervals_raw = service.freebusy().query(body=api_body).execute().get('calendars', {}).get('primary',
                                                                                                        {}).get('busy',
                                                                                                                [])

        all_busy_dt = sorted([
            (datetime.datetime.fromisoformat(i['start'].replace('Z', '+00:00')).astimezone(user_tz),
             datetime.datetime.fromisoformat(i['end'].replace('Z', '+00:00')).astimezone(user_tz))
            for i in busy_intervals_raw
        ])

        for i in range(NUM_DAYS_TO_CHECK):
            current_date = start_date + datetime.timedelta(days=i)
            day_start_local = user_tz.localize(
                datetime.datetime.combine(current_date, datetime.time(WORKING_HOUR_START, 0)))
            day_end_local = user_tz.localize(
                datetime.datetime.combine(current_date, datetime.time(WORKING_HOUR_END, 0)))

            busy_today = [(s, e) for s, e in all_busy_dt if s < day_end_local and e > day_start_local]
            slots = get_free_slots(busy_today, day_start_local, day_end_local)
            if slots: free_slots_by_day[current_date.strftime('%Y-%m-%d')] = slots

        st.success("Successfully fetched calendar slots.")
        return free_slots_by_day
    except HttpError as e:
        st.error(f"A Google Calendar API error occurred: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while fetching calendar data: {e}")
        # st.error(f"Trace: {traceback.format_exc()}") # Uncomment for full traceback in app
        return None


# --- Streamlit App UI and Logic ---
# st.set_page_config(layout="wide")
st.title("AI Client Scheduler Assistant")

# Initialize all session state keys to avoid KeyErrors
default_session_keys = {
    'credentials': None, 'auth_url': None, 'auth_flow_started': False,
    'user_timezone_str': None,  # Store timezone as string for JSON serializability if needed
    'transcript_data': None, 'analysis_results': None, 'suggested_schedule': None,
    'show_auth_flow': False, 'free_slots_data': None, 'auth_purpose': None,
    'show_auth_flow_intended': False,
}
for key, default_value in default_session_keys.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# Attempt to load credentials from token file if not already in session
if st.session_state.credentials is None:
    st.session_state.credentials = load_credentials()

# --- OAuth Callback Handling (processed high in the script) ---
query_params = st.query_params
auth_code = query_params.get("code")

if auth_code:
    was_restored_from_backup = restore_session_state_after_oauth()

    # Proceed with token exchange if auth flow was started (live or restored)
    if st.session_state.get('auth_flow_started') or st.session_state.get('show_auth_flow_intended'):
        st.info("Processing Google authentication...")
        try:
            flow = get_google_oauth_flow()
            code_to_use = auth_code[0] if isinstance(auth_code, list) else auth_code
            flow.fetch_token(code=code_to_use)
            save_credentials(flow.credentials)

            st.session_state.auth_flow_started = False
            st.session_state.show_auth_flow_intended = False
            st.session_state.auth_url = None

            st.success("✅ Google Authentication successful!")
            st.query_params.clear()

            # Restore intent for scheduling
            if st.session_state.get('auth_purpose') == 'schedule_meetings':
                st.session_state.show_auth_flow = True
            else:  # Fallback if purpose wasn't set or doesn't match
                st.session_state.show_auth_flow = False
                st.session_state.auth_purpose = None
            st.rerun()
        except Exception as e:
            st.error(f"Authentication error: {e}")
            clear_all_auth_state()  # Clear all auth state on error
            st.rerun()

# --- Main Application Flow ---

# Section 1: Transcript Upload
st.header("1. Upload Meeting Transcripts")
st.markdown("Client names are derived from filenames (e.g., `ClientX_Meeting.txt` → `ClientX_Meeting`). "
            "Filenames must use only letters, numbers, and underscores.")

with st.form("transcript_upload_form", clear_on_submit=True):
    uploaded_files = st.file_uploader("Choose transcript files (.txt, .csv)",
                                      accept_multiple_files=True, type=['txt', 'csv'], key="file_uploader")
    submit_transcripts_button = st.form_submit_button("Submit Transcripts")

    if submit_transcripts_button:
        if not uploaded_files:
            st.warning("No files uploaded. Please select transcript files.")
        else:
            processed_data = []
            valid_submission = True
            seen_client_names = set()
            for uf in uploaded_files:
                client_name_base, _ = os.path.splitext(uf.name)
                if not client_name_base or not re.match(r"^[a-zA-Z0-9_]+$", client_name_base):
                    st.error(f"Invalid filename format for '{uf.name}'. Please use only letters, numbers, underscores.")
                    valid_submission = False
                    break
                if client_name_base in seen_client_names:
                    st.error(
                        f"Duplicate client name '{client_name_base}' derived from filenames. Please ensure unique base names.")
                    valid_submission = False
                    break
                seen_client_names.add(client_name_base)
                try:
                    content = io.StringIO(uf.getvalue().decode("utf-8")).read()
                    processed_data.append({'client_name': client_name_base, 'content': content, 'filename': uf.name})
                except Exception as e:
                    st.error(f"Error reading file '{uf.name}': {e}")
                    valid_submission = False
                    break

            ###
            query_dict = {
                "table": "customer",
                "columns": ["customer_id", "customer_name"],
                "where": {"associated_salesrep_id": st.session_state.user}
            }

            associated_customers = st.session_state.db.fetch_json(query_dict)
            customers_list = associated_customers["customer_name"].tolist()
            customers_list = [name.lower() for name in customers_list]

            for data in processed_data:
                if data['client_name'].lower().replace('_', ' ') not in customers_list:
                    valid_submission = False
                    st.warning(f"Error finding Assocated Customer: {data['client_name'].replace('_', ' ')}")

            if valid_submission:
                st.session_state.transcript_data = processed_data
                # Reset subsequent step states
                for key in ['analysis_results', 'suggested_schedule', 'free_slots_data', 'show_auth_flow',
                            'auth_purpose', 'auth_url', 'auth_flow_started', 'show_auth_flow_intended']:
                    st.session_state[key] = default_session_keys[key]
                st.success(f"{len(processed_data)} transcripts processed successfully.")
                st.rerun()

# Section 2: Actions after transcript upload
if st.session_state.transcript_data:
    st.header("2. Choose Your Next Step")
    st.write(f"Clients to process: {', '.join([item['client_name'] for item in st.session_state.transcript_data])}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Analyse Transcripts & Prioritize Clients"):
            with st.spinner("Analyzing transcripts..."):
                st.session_state.analysis_results = analyse_transcripts(st.session_state.transcript_data)
            # Reset states for scheduling if analysis is re-run
            for key in ['suggested_schedule', 'show_auth_flow', 'auth_purpose', 'free_slots_data',
                        'auth_url', 'auth_flow_started', 'show_auth_flow_intended']:
                st.session_state[key] = default_session_keys[key]
            st.rerun()
    with col2:
        if st.button("Suggest Meeting Times (Requires Calendar Access)"):
            if not st.session_state.analysis_results:
                st.warning("Please analyse transcripts first to determine client priority.")
            else:
                st.session_state.show_auth_flow = True  # Trigger display of Section 4
                st.session_state.suggested_schedule = None  # Clear any old schedule
                st.session_state.free_slots_data = None  # Clear old slots
                st.rerun()

# Section 3: Display Analysis Results
if st.session_state.analysis_results and not st.session_state.get('show_auth_flow', False):
    st.header("3. Client Analysis & Priority")
    results = st.session_state.analysis_results
    priority_order = results.get('priority_order', [])

    if not priority_order:
        st.warning("Analysis complete, but no clients were prioritized or scored.")
    else:
        st.subheader("Client Priority Order (Highest First):")
        for i, client_name in enumerate(priority_order):
            score = results.get(client_name, {}).get('score', 'N/A')
            st.markdown(f"**{i + 1}. {client_name}** (Conversion Score: {score})")

        st.subheader("Client Summaries:")
        for client_name in priority_order:
            client_data = results.get(client_name)
            if client_data:  # Ensure client_data exists
                with st.expander(f"Details for {client_name} (Score: {client_data.get('score', 'N/A')})"):
                    st.write(client_data.get('summary', "No summary available."))
    st.markdown("---")

# Section 4: Google Calendar Authentication & Scheduling Logic
if st.session_state.get('show_auth_flow', False):
    st.header("4. Suggest Meeting Schedule via Google Calendar")
    current_credentials = st.session_state.credentials

    if not (current_credentials and current_credentials.valid):
        if current_credentials and current_credentials.expired and current_credentials.refresh_token:
            st.info("Google token expired. Attempting to refresh...")
            try:
                current_credentials.refresh(Request())
                save_credentials(current_credentials)
                st.success("Token refreshed successfully.")
                st.rerun()
            except Exception as e:
                st.error(f"Token refresh failed: {e}. Please sign in again.")
                clear_all_auth_state()
                st.rerun()
        else:  # No valid credentials, prompt for sign-in
            st.info("Access to your Google Calendar is required to find available slots.")
            if st.button("Sign In with Google & Authorize Calendar"):
                st.session_state.auth_purpose = 'schedule_meetings'
                backup_session_state_for_oauth()  # Save state before redirect

                flow = get_google_oauth_flow()
                authorization_url, _ = flow.authorization_url(access_type='offline', include_granted_scopes='true', state=st.session_state.user)

                st.session_state.auth_url = authorization_url
                st.session_state.auth_flow_started = True
                st.rerun()

            if st.session_state.auth_url and st.session_state.auth_flow_started:
                # Display the authorization link for the user to click
                st.markdown(f"""
                    <p style="font-size: 1.1em; margin-top: 1em;">
                        <a href="{st.session_state.auth_url}" target="_self" style="padding: 10px 15px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px;">
                            ➡️ Click Here to Authorize Google Calendar Access
                        </a>
                    </p>
                    <p><small>You will be redirected to Google. Please complete the authorization in the same browser tab.</small></p>
                """, unsafe_allow_html=True)
                st.markdown("---")

    elif current_credentials and current_credentials.valid:  # User is authenticated
        st.success("Successfully authenticated with Google Calendar.")
        st.session_state.auth_purpose = 'schedule_meetings'
        if st.button("Sign Out from Google"):
            clear_all_auth_state()
            st.rerun()

        analysis_data = st.session_state.get('analysis_results')  # Fetch once
        if st.session_state.get('auth_purpose') == 'schedule_meetings' and analysis_data:
            if st.session_state.free_slots_data is None:  # Fetch slots only if not already present
                with st.spinner("Finding available slots in your calendar..."):
                    st.session_state.free_slots_data = fetch_calendar_free_slots(current_credentials)

            fetched_slots = st.session_state.free_slots_data
            if fetched_slots is not None:  # Check if fetch was successful (not None)
                if st.session_state.suggested_schedule is None:  # Generate schedule only once
                    with st.spinner("Matching clients to your availability..."):
                        st.session_state.suggested_schedule = schedule_meetings(analysis_data, fetched_slots)

                current_schedule = st.session_state.suggested_schedule
                if current_schedule:
                    st.subheader("🗓️ Suggested Meeting Schedule:")
                    for suggestion_item in current_schedule:
                        st.markdown(f"- {str(suggestion_item)}")
                elif not fetched_slots:
                    st.warning("No free slots were found in your calendar for the upcoming period.")
                else:  # Slots fetched, but schedule is still None (e.g., no clients from analysis)
                    st.info(
                        "Slots found, but no specific schedule generated (e.g., no high-priority clients or other criteria not met).")
            else:  # free_slots_data is None (meaning fetch_calendar_free_slots returned None due to an error)
                st.error("Could not retrieve calendar data. Please ensure Google Calendar access is working.")
        elif not analysis_data:
            st.warning("Analysis results are not available. Please go back and analyze transcripts first.")
    st.markdown("---")

st.caption(f"AI Client Scheduler Assistant v0.1")