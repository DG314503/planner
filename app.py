
import pandas as pd
from datetime import datetime, timedelta, time
from datetime import datetime, timezone
import time as pytime
from datetime import datetime, time as dt_time
import pyrebase
import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

if not hasattr(st, "rerun") and hasattr(st, "experimental_rerun"):
    st.rerun = st.experimental_rerun


# --- Firebase Config (replace with your own) ---
firebaseConfig = {
    "apiKey": "AIzaSyBcCRHdv1g0lmx3jMR_50SC9_e0roeCexI",
    "authDomain": "planner-1db73.firebaseapp.com",
    "databaseURL": "https://planner-1db73-default-rtdb.firebaseio.com/",
    "projectId": "planner-1db73",
    "storageBucket": "planner-1db73.appspot.com",
    "messagingSenderId": "755874773812",
    "appId": "1:755874773812:web:ed20cf27fac6724e6d0361",
    "measurementId": "G-Y1DFP2TM0V"
}


firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()





def show_timed_message(msg, msg_type="info", seconds=10):
    # Only set if not already set, to avoid resetting the timer on rerun
    if "timed_msg" not in st.session_state or st.session_state.timed_msg is None:
        st.session_state.timed_msg = {
            "msg": msg,
            "type": msg_type,
            "timestamp": pytime.time(),
            "duration": seconds
        }

def render_timed_message():
    msg_data = st.session_state.get("timed_msg")
    if msg_data:
        elapsed = pytime.time() - msg_data["timestamp"]
        if elapsed < msg_data["duration"]:
            # Show the message
            if msg_data["type"] == "success":
                st.success(msg_data["msg"])
            elif msg_data["type"] == "warning":
                st.warning(msg_data["msg"])
            elif msg_data["type"] == "error":
                st.error(msg_data["msg"])
            else:
                st.info(msg_data["msg"])
            # Schedule a rerun after 1 second to check for expiration
            st.rerun()
        else:
            st.session_state.timed_msg = None




def forgot_password():
    st.markdown("""
        <style>
            .forgot-card {
                max-width: 370px;
                margin-left: auto;
                margin-right: auto;
                margin-top: 2.5em;
                background: none;
                padding: 0;
            }
            .forgot-logo {
                display: flex;
                justify-content: center;
                margin-bottom: 1.1em;
            }
            
            .forgot-title {
                text-align: center;
                font-size: 2.3em;
                font-weight: 900;
                color: #fff;
                margin-bottom: 1.2em;
                letter-spacing: 0.01em;
            }
            .stTextInput, .stTextInput > div, .stTextInput > div > div {
                max-width: 350px;
                margin-left: auto;
                margin-right: auto;
            }
            .stButton>button {
                background: linear-gradient(90deg, #1976D2 0%, #388E3C 100%);
                color: #fff;
                font-weight: 700;
                border-radius: 8px;
                border: none;
                padding: 0.7em 1.5em;
                font-size: 1.1em;
                margin-top: 0.7em;
                margin-bottom: 0.2em;
                box-shadow: 0 2px 8px 0 rgba(25,118,210,0.08);
                transition: background 0.2s, transform 0.15s;
                display: block;
                margin-left: auto;
                margin-right: auto;
            }
            .stButton>button:hover {
                background: linear-gradient(90deg, #1565C0 0%, #2E7D32 100%);
                transform: translateY(-2px) scale(1.03);
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="forgot-card">', unsafe_allow_html=True)
    st.markdown('<div class="forgot-title">Forgot Password?</div>', unsafe_allow_html=True)

    # --- Clear email if flag is set ---
    if st.session_state.get("clear_forgot_email", False):
        st.session_state.forgot_email = ""
        st.session_state.clear_forgot_email = False

    # Use session state to store/reset the email field
    if "forgot_email" not in st.session_state:
        st.session_state.forgot_email = ""

    # Render any timed message
    render_timed_message()

    email = st.text_input("Enter your email", value=st.session_state.forgot_email, key="forgot_email")
    send_btn = st.button("Send Reset Email")
    back_btn = st.button("Back to Login")

    if send_btn:
        if not email:
            show_timed_message("Please enter your email address.", "warning")
            st.rerun()
        else:
            try:
                auth.send_password_reset_email(email)
                st.session_state.clear_forgot_email = True  # Set flag to clear on next run
                show_timed_message("Password reset email sent! Please check your inbox (and spam folder).", "success")
                st.rerun()
            except Exception as e:
                err = str(e)
                if "EMAIL_NOT_FOUND" in err:
                    show_timed_message("This email address is not registered.", "warning")
                else:
                    # If the error is not EMAIL_NOT_FOUND, but no error is thrown, assume success
                    if "EMAIL_NOT_FOUND" not in err and "TOO_MANY_ATTEMPTS_TRY_LATER" not in err:
                        st.session_state.clear_forgot_email = True
                        show_timed_message("Password reset email sent! Please check your inbox (and spam folder).", "success")
                    else:
                        show_timed_message("Something went wrong sending the reset email.", "error")
                st.rerun()

    if back_btn:
        st.session_state.show_forgot = False
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)





# --- Authentication ---
def login_signup():
    st.markdown("""
        <style>
            .login-logo {
                display: flex;
                justify-content: center;
                margin-bottom: 1.1em;
            }
            .login-logo img {
                width: 64px;
                height: 64px;
                border-radius: 16px;
                box-shadow: 0 2px 12px 0 rgba(25,118,210,0.13);
            }
            .login-title {
                text-align: center;
                font-size: 2.3em;
                font-weight: 900;
                color: #fff;
                margin-bottom: 0.1em;
                letter-spacing: 0.01em;
            }
            .login-subtitle {
                text-align: center;
                font-size: 1.13em;
                color: #b0b8c9;
                margin-bottom: 1.5em;
            }
            /* Center and reduce width of input fields and their containers */
            .stTextInput, .stTextInput > div, .stTextInput > div > div {
                max-width: 350px;
                margin-left: auto;
                margin-right: auto;
            }
            .stTextInput>div>div>input, .stTextInput>div>div>div>input {
                background: #1a2233;
                color: #fff;
                border-radius: 8px;
                border: 1.5px solid #3a4666;
                font-size: 1.08em;
                width: 100% !important;
                min-width: 0 !important;
                text-align: center;
                box-sizing: border-box;
            }
            .stTextInput>div>div>input:focus, .stTextInput>div>div>div>input:focus {
                border: 2px solid #1976D2;
            }
            /* Make radio selector HUGE and centered */
            .stRadio > div { justify-content: center; }
            .stRadio label {
                font-size: 1.6em !important;
                font-weight: 800 !important;
                padding: 0.5em 2em !important;
                margin-right: 2em !important;
                color: #fff !important;
            }
            .stRadio [data-baseweb="radio"] {
                width: 32px !important;
                height: 32px !important;
                min-width: 32px !important;
                min-height: 32px !important;
                margin-right: 1em !important;
                accent-color: #1976d2 !important;
                transform: scale(1.5);
            }
            .stButton>button {
                background: linear-gradient(90deg, #1976D2 0%, #388E3C 100%);
                color: #fff;
                font-weight: 700;
                border-radius: 8px;
                border: none;
                padding: 0.7em 1.5em;
                font-size: 1.1em;
                margin-top: 0.7em;
                margin-bottom: 0.2em;
                box-shadow: 0 2px 8px 0 rgba(25,118,210,0.08);
                transition: background 0.2s, transform 0.15s;
                display: block;
                margin-left: auto;
                margin-right: auto;
            }
            .stButton>button:hover {
                background: linear-gradient(90deg, #1565C0 0%, #2E7D32 100%);
                transform: translateY(-2px) scale(1.03);
            }
                
            .forgot-link {
                color: #90caf9;
                text-decoration: underline;
                cursor: pointer;
                font-size: 1em;
                display: block;
                text-align: right;
                margin-top: -0.5em;
                margin-bottom: 1.2em;
                transition: color 0.2s;
            }
            .forgot-link:hover {
                color: #42a5f5;
            }
        </style>
    """, unsafe_allow_html=True)

    

    
    st.markdown('<div class="login-center"><div class="login-card">', unsafe_allow_html=True)

    # --- Logo (replace src with your own if you want) ---
    st.markdown(
        '<div class="login-logo"><img src="https://img.icons8.com/color/96/000000/calendar--v2.png" alt="logo"></div>',
        unsafe_allow_html=True
    )

    if "user" not in st.session_state:
        st.session_state.user = None

    # --- Show forgot password form if requested ---
    if st.session_state.get("show_forgot", False):
        forgot_password()
        st.markdown("</div></div>", unsafe_allow_html=True)
        st.stop()

    # --- Login/Signup Form ---
    st.markdown('<div class="login-title">Weekly Planner</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">Plan your week, stay productive!</div>', unsafe_allow_html=True)

    render_timed_message()

    st.markdown("""
        <style>
        /* Target selectbox container */
        div[data-testid="stSelectbox"] {
            max-width: 350px !important;
            width: 350px !important;
            margin-left: auto;
            margin-right: auto;
            text-align: center;
        }
        /* Target the actual select input */
        div[data-testid="stSelectbox"] > div {
            max-width: 350px !important;
            width: 350px !important;
            text-align: center;
        }
        /* Target the select label area (hide if needed) */
        div[data-testid="stSelectbox"] label {
            width: 100%;
            display: block;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    choice = st.selectbox(
        "", ["Login", "Sign up"], key="login_selectbox"
    )



    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    # Show "Forgot Password?" as a link
    if st.button("Forgot Password?", key="forgot_pw_btn"):
        st.session_state.show_forgot = True
        st.rerun()

    # --- Action buttons ---
    if choice == "Sign up":
        if st.button("Create Account", key="signup_btn"):
            try:
                user = auth.create_user_with_email_and_password(email, password)
                show_timed_message("Account created! Please log in.", "success")
                st.rerun()
            except Exception as e:
                error_str = str(e)
                if "EMAIL_EXISTS" in error_str:
                    show_timed_message("This email is already registered. Please log in instead.", "error")
                else:
                    show_timed_message(f"Error: {e}", "error")
                st.rerun()
    else:
        if st.button("Login", key="login_btn"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.rerun()
            except Exception as e:
                show_timed_message(f"Error: {e}", "error")
                st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)
    st.stop()


    

# --- Database Helpers ---
def get_user_id():
    # Firebase returns localId as the unique user id
    return st.session_state.user['localId']

from datetime import date, datetime, time

def serialize_for_json(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(i) for i in obj]
    else:
        return obj

def save_user_data(user_id, session_state):
    data = {
        'categories': session_state.categories,
        'category_colors': session_state.category_colors,
        'tasks': serialize_for_json(session_state.tasks),
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'selected_date': session_state.selected_date.isoformat() if hasattr(session_state.selected_date, 'isoformat') else str(session_state.selected_date),
        'view_mode': session_state.view_mode
    }
    db.child("user_data").child(user_id).set(data)



def parse_datetime_fields(task):
    # Assumes your 'start' and 'end' are always datetime ISO strings
    task = task.copy()
    if 'date' in task and isinstance(task['date'], str):
        try:
            task['date'] = datetime.fromisoformat(task['date']).date()
        except Exception:
            pass
    if 'start' in task and isinstance(task['start'], str):
        try:
            task['start'] = datetime.fromisoformat(task['start'])
        except Exception:
            pass
    if 'end' in task and isinstance(task['end'], str):
        try:
            task['end'] = datetime.fromisoformat(task['end'])
        except Exception:
            pass
    return task



def load_user_data(user_id):
    try:
        data = db.child("user_data").child(user_id).get()
        if data.val():
            out = data.val()
            if 'tasks' in out:
                out['tasks'] = [parse_datetime_fields(t) for t in out['tasks']]
            return out
        return None
    except requests.exceptions.HTTPError as e:
        if "404" in str(e):
            return None
        else:
            raise

def hours_to_hm(hours):
    h = int(hours)
    m = int(round((hours - h) * 60))
    return f"{h}:{m:02d} hr"



# --- Session State Initialization ---
def initialize_session_state(user_id):
    user_data_loaded = load_user_data(user_id)
    if user_data_loaded:
        st.session_state.categories = user_data_loaded.get('categories', ["Work", "Study", "Reading"])
        st.session_state.category_colors = user_data_loaded.get('category_colors', {})
        st.session_state.tasks = user_data_loaded.get('tasks', [])
        # Load selected_date and view_mode if they exist
        if 'selected_date' in user_data_loaded:
            try:
                st.session_state.selected_date = datetime.fromisoformat(user_data_loaded['selected_date']).date()
            except Exception:
                st.session_state.selected_date = datetime.now().date()
        else:
            st.session_state.selected_date = datetime.now().date()
        st.session_state.view_mode = user_data_loaded.get('view_mode', 'Week')
    else:
        st.session_state.categories = ["Work", "Study", "Reading"]
        default_palette = [
            "#1976D2", "#388E3C", "#FBC02D", "#D32F2F", "#7B1FA2", "#0288D1", "#C2185B", "#FFA000"
        ]
        st.session_state.category_colors = {cat: default_palette[i % len(default_palette)] for i, cat in enumerate(st.session_state.categories)}
        st.session_state.tasks = []
        st.session_state.selected_date = datetime.now().date()
        st.session_state.view_mode = 'Week'
    st.session_state.edit_task_idx = None
    st.session_state.initialized = True

st.set_page_config(layout="wide")

# --- Helper Functions for Planner ---
def get_week_dates(selected_date):
    start = selected_date - timedelta(days=selected_date.weekday())
    return [start + timedelta(days=i) for i in range(7)]

def get_day_label(date):
    return date.strftime("%a %d %b")

def sum_hours(tasks, categories):
    hours = {cat: 0 for cat in categories}
    for t in tasks:
        hours[t['category']] += (t['end'] - t['start']).total_seconds() / 3600
    return hours

def get_text_color(bg_color):
    bg_color = bg_color.lstrip('#')
    r, g, b = int(bg_color[0:2], 16), int(bg_color[2:4], 16), int(bg_color[4:6], 16)
    luminance = (0.299*r + 0.587*g + 0.114*b)
    return "#000000" if luminance > 186 else "#FFFFFF"

def assign_task_columns(tasks):
    tasks = sorted(tasks, key=lambda t: t['start'])
    columns = []
    end_times = []
    for t in tasks:
        placed = False
        for col, end_time in enumerate(end_times):
            if t['start'] >= end_time:
                columns.append(col)
                end_times[col] = t['end']
                placed = True
                break
        if not placed:
            columns.append(len(end_times))
            end_times.append(t['end'])
    total_columns = max(columns) + 1 if columns else 1
    return [(t, col, total_columns) for t, col in zip(tasks, columns)]

def parse_time_with_24(label, value, key):
    """
    Use st.time_input for dropdown/manual, but allow '24:00' via a text input.
    Returns (time, is_24, raw_input).
    """
    col1, col2 = st.columns([2,1])
    with col1:
        t = st.time_input(label, value=value, key=key)
    with col2:
        raw = st.text_input("Type time (e.g. 24:00)", value=value.strftime("%H:%M"), key=key+"_raw", help="Type 24:00 for midnight")
    is_24 = False
    try:
        if raw.strip() == "24:00":
            t = time(0, 0)
            is_24 = True
        else:
            h, m = map(int, raw.strip().split(":"))
            t = time(h, m)
    except Exception:
        pass  # fallback to st.time_input value
    return t, is_24, raw

def format_time(t, is_24=False):
    if is_24:
        return "12:00 AM"  # 24:00 is midnight in 12-hour format
    # Format as 12-hour with AM/PM, remove leading zero
    return t.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")


def parse_time_input(label, t, key=None):
    """
    Render a time input in 12-hour format with AM/PM.
    Returns (time, is_24)
    """
    # Build 12-hour time options (every 30 min + 12:00 AM for 24:00)
    times = []
    display_times = []
    for h in range(0, 24):
        for m in (0, 30):
            hour_12 = h % 12
            hour_12 = 12 if hour_12 == 0 else hour_12
            am_pm = "AM" if h < 12 else "PM"
            display = f"{hour_12}:{m:02d} {am_pm}"
            times.append(time(h, m))
            display_times.append(display)
    # Add 24:00 as 12:00 AM (next day)
    times.append(time(0, 0))
    display_times.append("12:00 AM (next day)")

    # Find default index
    def time_to_display(t):
        hour_12 = t.hour % 12
        hour_12 = 12 if hour_12 == 0 else hour_12
        am_pm = "AM" if t.hour < 12 else "PM"
        return f"{hour_12}:{t.minute:02d} {am_pm}"

    default = time_to_display(t)
    idx = display_times.index(default) if default in display_times else 0

    selected = st.selectbox(label, display_times, index=idx, key=key)
    if selected == "12:00 AM (next day)":
        return time(0, 0), True
    return times[display_times.index(selected)], False



# --- Main App ---
def main():
    user_id = get_user_id()
    st.write("Welcome, you are logged in as:", st.session_state.user['email'])

    # --- Session State Initialization ---
    if 'initialized' not in st.session_state:
        initialize_session_state(user_id)

    # --- Sidebar: Category Management ---
    st.sidebar.header("Categories")
    new_cat = st.sidebar.text_input("Add Category", "")
    new_cat_color = st.sidebar.color_picker("Pick Color", "#1976D2")
    if st.sidebar.button("Add") and new_cat and new_cat not in st.session_state.categories:
        st.session_state.categories.append(new_cat)
        st.session_state.category_colors[new_cat] = new_cat_color
        save_user_data(user_id, st.session_state)  # Auto-save

    remove_cat = st.sidebar.selectbox("Remove Category", [""] + st.session_state.categories)
    if st.sidebar.button("Remove") and remove_cat:
        st.session_state.categories.remove(remove_cat)
        st.session_state.category_colors.pop(remove_cat, None)
        st.session_state.tasks = [t for t in st.session_state.tasks if t['category'] != remove_cat]
        save_user_data(user_id, st.session_state)  # Auto-save

    st.sidebar.markdown("**Category Colors**")
    for cat in st.session_state.categories:
        color = st.sidebar.color_picker(f"{cat} color", st.session_state.category_colors.get(cat, "#1976D2"), key=f"color_{cat}")
        st.session_state.category_colors[cat] = color
        save_user_data(user_id, st.session_state)  # Auto-save


    # --- Sidebar: Date and View Selection ---
    st.sidebar.header("Planner Settings")
    st.session_state.selected_date = st.sidebar.date_input("Select Date", st.session_state.selected_date)
    st.session_state.view_mode = st.sidebar.radio("View Mode", ["Day", "Week"])

        # Save selected_date if it changed
    if 'prev_selected_date' not in st.session_state or st.session_state.selected_date != st.session_state.prev_selected_date:
        st.session_state.prev_selected_date = st.session_state.selected_date
        save_user_data(user_id, st.session_state)

    # Save view_mode if it changed
    if 'prev_view_mode' not in st.session_state or st.session_state.view_mode != st.session_state.prev_view_mode:
        st.session_state.prev_view_mode = st.session_state.view_mode
        save_user_data(user_id, st.session_state)


    # --- Logout Button ---
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.initialized = False
        st.rerun()

    # --- Main: Add Task ---
    st.header("Add Task")
    with st.form("add_task_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            task_name = st.text_input("Task Name")
        with col2:
            category = st.selectbox("Category", st.session_state.categories)
        with col3:
            date = st.date_input("Date", st.session_state.selected_date)
        with col4:
            start_time, _ = parse_time_input("Start Time", time(0, 0), key="add_start_time")
            end_time, end_is_24 = parse_time_input("End Time", time(1, 0), key="add_end_time")

        submitted = st.form_submit_button("Add Task")
        if submitted and task_name and start_time < end_time:
            st.session_state.tasks.append({
                "name": task_name,
                "category": category,
                "date": date,
                "start": datetime.combine(date, start_time),
                "end": datetime.combine(date, end_time)
            })
            save_user_data(user_id, st.session_state)  # Auto-save

            st.rerun()

    # --- Main: Calendar Grid View ---
    def render_calendar_grid(dates, tasks, mode="Week", start_hour=0, end_hour=24):
        slot_height_px = 48  # px per hour slot
        total_hours = end_hour - start_hour
        total_minutes = total_hours * 60
        calendar_height = total_hours * slot_height_px
        minute_height = slot_height_px / 60

        now = datetime.now()
        now_minutes = (now.hour * 60 + now.minute) - (start_hour * 60)
        now_top = now_minutes * minute_height

        def format_12hr(hour, minute=0):
            h = hour % 12
            h = 12 if h == 0 else h
            am_pm = "AM" if hour < 12 else "PM"
            return f"{h}:{minute:02d} {am_pm}"
        
        

        st.markdown(f"""
        <style>
        .calendar-outer {{
            display: flex;
            flex-direction: column;
            width: 100%;
            min-height: {calendar_height + 8 + 38}px;
        }}
        .calendar-header-row {{
            display: flex;
            flex-direction: row;
            width: 100%;
            min-height: 38px;
            font-size: 1.08em;
            font-weight: 600;
            background: transparent;
            border-bottom: 2px solid #b0b0b0;
        }}
        .calendar-header-cell {{
            flex: 1 1 0;
            min-width: 120px;
            text-align: center;
            padding: 8px 0 6px 0;
            border-left: 2px solid #b0b0b0;
            border-right: 2px solid #b0b0b0;
            background: transparent;
            color: #fff !important;
            font-weight: 600;
            letter-spacing: 0.01em;
        }}
        .calendar-header-time {{
            width: 60px;
            min-width: 60px;
            text-align: right;
            padding-right: 6px;
            background: transparent;
            color: #fff !important;
            font-size: 1.02em;
            font-weight: 600;
            border-left: 2px solid #b0b0b0;
            border-right: 2px solid #b0b0b0;
        }}
        .calendar-day-row {{
            display: flex;
            flex-direction: row;
            width: 100%;
        }}
        .calendar-day-col {{
            flex: 1 1 0;
            border-left: 2px solid #b0b0b0;
            border-right: 2px solid #b0b0b0;
            position: relative;
            min-width: 120px;
            background: transparent;
            height: {calendar_height}px;
        }}
        .calendar-grid-bg {{
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            z-index: 0;
            pointer-events: none;
            height: {calendar_height}px;
        }}
        .calendar-grid-hour {{
            position: absolute;
            left: 0; right: 0;
            height: 0;
            border-top: 1.5px solid #b0b0b0;
            font-size: 0.8em;
            color: #fff !important;
            padding-left: 2px;
            box-sizing: border-box;
            background: transparent;
        }}
        .calendar-block {{
            border-radius: 6px;
            font-size: 1.18em;
            font-weight: 500;
            cursor: pointer;
            text-align: center;
            padding: 0 10px;
            box-sizing: border-box;
            z-index: 2;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            margin: 0;
            border: 2px solid #fff;
            box-shadow: 0 2px 8px 0 rgba(0,0,0,0.07);
            transition: box-shadow 0.1s;
        }}
        .calendar-block:hover {{
            box-shadow: 0 4px 16px 0 rgba(0,0,0,0.13);
            filter: brightness(1.05);
        }}
        .calendar-time-col {{
            width: 70px;
            min-width: 70px;
            text-align: right;
            padding-right: 6px;
            color: #fff !important;
            font-size: 0.95em;
            font-weight: 400;
            position: relative;
            border-left: 2px solid #b0b0b0;
            border-right: 2px solid #b0b0b0;
            background: transparent;
            height: {calendar_height}px;
        }}
        .calendar-time-col .calendar-grid-hour {{
            border-top: 1.5px solid #b0b0b0;
            left: 0; right: 0;
            text-align: right;
            padding-right: 6px;
            color: #fff !important;
            font-size: 0.95em;
            background: transparent;
            box-sizing: border-box;
        }}
        .calendar-now-line {{

            position: absolute;
            left: 0; right: 0;
            height: 0;
            border-top: 2.5px solid #e53935;
            z-index: 10 !important;

            pointer-events: none;
        }}

        .calendar-header-time, .calendar-time-col {{
            width: 70px;
            min-width: 70px;
            max-width: 70px;
            box-sizing: border-box;
        }}

        .calendar-header-cell, .calendar-day-col {{
            flex: 1 1 0;
            min-width: 120px;
            max-width: 1fr;
            box-sizing: border-box;
        }}
        </style>
        """, unsafe_allow_html=True)

        html = '<div class="calendar-outer">'

        # --- HEADER ROW ---
        if mode == "Week":
            html += '<div class="calendar-header-row">'
            html += '<div class="calendar-header-time"></div>'  # Time column header
            for day in dates:
                html += (
                    f'<div class="calendar-header-cell">'
                    f'<b>{day.strftime("%A")}</b><br>{day.strftime("%d %b")}'
                    f'</div>'
                )
            html += '</div>'

        html += '<div class="calendar-day-row">'

        

        # --- Time column (12hr format) ---
        html += f'<div class="calendar-time-col" style="height:{calendar_height}px; position:relative;">'
        for h in range(total_hours + 1):
            top = h * slot_height_px
            hour_label = format_12hr(start_hour + h)
            html += f'<div class="calendar-grid-hour" style="top:{top}px;">{hour_label}</div>'
        html += '</div>'

        # --- Day columns ---
        for day_idx, day in enumerate(dates):
            day_tasks = [t for t in tasks if t['date'] == day]
            task_columns = assign_task_columns(day_tasks)

            html += f'<div class="calendar-day-col" style="height:{calendar_height}px; position:relative;">'
            html += f'<div class="calendar-grid-bg">'
            for h in range(total_hours + 1):
                top = h * slot_height_px
                # NO hour_label here!
                html += f'<div class="calendar-grid-hour" style="top:{top}px;"></div>'

            html += '</div>'


            # Red "now" line if today
            if day == datetime.now().date() and 0 <= now_minutes < total_minutes:
                html += f'<div class="calendar-now-line" style="top:{now_top}px;"></div>'
            for idx, (t, col, total_cols) in enumerate(task_columns):
                # Calculate start and end in minutes from start_hour
                task_start_minutes = (t['start'].hour * 60 + t['start'].minute) - (start_hour * 60)
                # Handle 24:00
                if t.get('end_is_24', False):
                    task_end_minutes = (24 * 60) - (start_hour * 60)
                else:
                    task_end_minutes = (t['end'].hour * 60 + t['end'].minute) - (start_hour * 60)

                # Clamp to visible grid
                bubble_start = max(task_start_minutes, 0)
                bubble_end = min(task_end_minutes, total_minutes)

                if bubble_end <= 0 or bubble_start >= total_minutes:
                    continue  # Task outside visible range

                top = bubble_start * minute_height
                height = max(1, (bubble_end - bubble_start) * minute_height)  # Always at least 1px

                left_pct = (col / total_cols) * 100
                width_pct = (1 / total_cols) * 100
                color = st.session_state.category_colors.get(t['category'], "#1976D2")
                text_color = get_text_color(color)

                # --- 12hr formatting for bubble times ---
                def task_time_12hr(t_, is_24=False):
                    if is_24:
                        return "12:00 AM"
                    return format_12hr(t_.hour, t_.minute)

                start = task_time_12hr(t['start'].time())
                end = task_time_12hr(t['end'].time(), t.get('end_is_24', False))

                task_idx = st.session_state.tasks.index(t)
                # Tooltip: name, start, end
                tooltip = f"{t['name']} ({start} - {end})"
                html += (
                    f"<div style='position:absolute;top:{top}px;height:{height}px;left:{left_pct}%;width:{width_pct}%;z-index:4;'>"
                    f"<div class='calendar-block' title='{tooltip}' style='background:{color};color:{text_color};height:100%;width:100%;"
                    f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:flex;align-items:center;justify-content:center;'>"
                    f"<span style='font-size:1em;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>"
                    f"{t['name']} <span style='font-size:0.95em;font-weight:400;'>({start}-{end})</span>"
                    f"</span></div></div>"
                )

            html += '</div>'
        html += '</div>'  # end calendar-day-row
        html += '</div>'  # end calendar-outer

        st.markdown(html, unsafe_allow_html=True)




    # --- Render Calendar View ---
    start_hour = 0
    end_hour = 24
    if st.session_state.view_mode == "Week":
        week_dates = get_week_dates(st.session_state.selected_date)
        st.subheader(f"Week of {week_dates[0].strftime('%d %b %Y')} - {week_dates[-1].strftime('%d %b %Y')}")
        render_calendar_grid(week_dates, st.session_state.tasks, mode="Week", start_hour=start_hour, end_hour=end_hour)
        visible_dates = week_dates
    else:
        st.subheader(f"Day: {get_day_label(st.session_state.selected_date)}")
        render_calendar_grid([st.session_state.selected_date], st.session_state.tasks, mode="Day", start_hour=start_hour, end_hour=end_hour)
        visible_dates = [st.session_state.selected_date]

    # --- Add two <br> between calendar and edit tasks ---
    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Edit Buttons (side by side, but header is just "Edit Tasks") ---
    st.markdown("#### Edit Tasks:")
    for day_idx, day in enumerate(visible_dates):
        day_tasks = [t for t in st.session_state.tasks if t['date'] == day]
        if not day_tasks:
            continue
        st.markdown(f"**{get_day_label(day)}**")
        cols = st.columns(len(day_tasks))
        for idx, t in enumerate(day_tasks):
            color = st.session_state.category_colors.get(t['category'], "#1976D2")
            text_color = get_text_color(color)
            start = format_time(t['start'].time())
            end = format_time(t['end'].time(), t.get('end_is_24', False))
            tooltip = f"{t['name']} ({start} - {end})"
            btn_label = (
                f"<div title='{tooltip}' style='background:{color};color:{text_color};"
                "border-radius:6px;padding:8px 12px;font-weight:500;text-align:center;'>"
                f"{t['name']}<br><span style='font-size:0.95em'>{start}-{end}</span></div>"
            )
            if cols[idx].button("Edit", key=f"edit_btn_{day}_{idx}"):
                st.session_state.edit_task_idx = st.session_state.tasks.index(t)
            cols[idx].markdown(btn_label, unsafe_allow_html=True)
        # Add one <br> between days
        if day_idx < len(visible_dates) - 1:
            st.markdown("<br>", unsafe_allow_html=True)

    # --- Show edit form if a task is selected for editing ---
    def task_edit_form(idx, task, user_id):
        st.markdown(f"### Edit Task: {task['name']}")
        with st.form(f"edit_task_form_{idx}"):
            new_name = st.text_input("Task Name", value=task['name'], key=f"edit_name_{idx}")
            new_category = st.selectbox("Category", st.session_state.categories, index=st.session_state.categories.index(task['category']), key=f"edit_cat_{idx}")
            new_date = st.date_input("Date", value=task['date'], key=f"edit_date_{idx}")
            new_start, _ = parse_time_input("Start Time", task['start'].time(), key=f"edit_start_{idx}")
            new_end, new_end_is_24 = parse_time_input("End Time", task['end'].time(), key=f"edit_end_{idx}")
            col1, col2, col3 = st.columns(3)
            with col1:
                save = st.form_submit_button("Save")
            with col2:
                cancel = st.form_submit_button("Cancel")
            with col3:
                delete = st.form_submit_button("Delete", type="primary")
            if save and new_name and (
                (not new_end_is_24 and new_start < new_end) or (new_end_is_24 and (new_start < time(23,59,59) or new_start == time(0,0)))
            ):
                st.session_state.tasks[idx] = {
                    "name": new_name,
                    "category": new_category,
                    "date": new_date,
                    "start": datetime.combine(new_date, new_start),
                    "end": datetime.combine(new_date, new_end),
                    "end_is_24": new_end_is_24
                }
                save_user_data(user_id, st.session_state)
                st.session_state.edit_task_idx = None
                st.rerun()
            if cancel:
                st.session_state.edit_task_idx = None
                st.rerun()
            if delete:
                st.session_state.tasks.pop(idx)
                save_user_data(user_id, st.session_state)
                st.session_state.edit_task_idx = None
                st.rerun()

    # --- Render the edit form below the calendar ---
    if st.session_state.edit_task_idx is not None:
        idx = st.session_state.edit_task_idx
        if 0 <= idx < len(st.session_state.tasks):
            task_edit_form(idx, st.session_state.tasks[idx], user_id)





    # --- Total Hours Summary Table (Categories only, colored) ---
    st.markdown("---")
    st.subheader("Total Hours Summary")

    all_categories = st.session_state.categories
    week_dates = get_week_dates(st.session_state.selected_date)
    week_tasks = [t for t in st.session_state.tasks if t['date'] in week_dates]
    day = st.session_state.selected_date
    day_tasks = [t for t in st.session_state.tasks if t['date'] == day]

    def task_hours(tasks, categories):
        hours = {cat: 0 for cat in categories}
        for t in tasks:
            end = t['end']
            if t.get('end_is_24', False):
                end = datetime.combine(t['date'] + timedelta(days=1), time(0, 0))
            hours[t['category']] += (end - t['start']).total_seconds() / 3600
        return hours

    week_hours = task_hours(week_tasks, all_categories)
    day_hours = task_hours(day_tasks, all_categories)
    total_week_hours = 7 * 24
    percent_of_week = {cat: (week_hours[cat] / total_week_hours * 100) if total_week_hours else 0 for cat in all_categories}

    # Build table rows: one per category, with color
    table_rows = []
    for cat in all_categories:
        color = st.session_state.category_colors.get(cat, "#1976D2")
        
        text_color = get_text_color(color)
        table_rows.append({
    "Category": f"<div style='background:{color};color:{text_color};padding:6px 12px;border-radius:6px;display:inline-block;font-weight:bold'>{cat}</div>",
    "Today": f"<b>{hours_to_hm(day_hours[cat])}</b>",
    "This Week": f"<b>{hours_to_hm(week_hours[cat])}</b>",
    "% of Week": f"<b>{percent_of_week[cat]:.1f}%</b>"
})


    summary_df = pd.DataFrame(table_rows)

    def df_to_html(df):
        html = '<table style="width:100%; border-collapse:collapse; background:transparent;">'
        # Header
        html += "<tr>" + "".join([f"<th style='text-align:left; padding:6px; border-bottom:1.5px solid #bbb; background:transparent;'>{col}</th>" for col in df.columns]) + "</tr>"
        # Rows
        for _, row in df.iterrows():
            html += "<tr>"
            for i, val in enumerate(row):
                html += f"<td style='padding:6px; vertical-align:top; background:transparent;'>{val}</td>"
            html += "</tr>"
        html += "</table>"
        return html

    st.markdown(df_to_html(summary_df), unsafe_allow_html=True)

   
# --- App Entrypoint ---
if "user" not in st.session_state or st.session_state.user is None:
    login_signup()
else:
    main()
