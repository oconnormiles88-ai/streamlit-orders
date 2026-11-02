# config.py
# gets the supabase url, key, and app password
# online they come from streamlit's secrets settings, on my laptop they come from .env
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def get_setting(name):
    # try streamlit secrets first (for the deployed app), then fall back to .env
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        # no secrets file on my laptop, that's fine, .env covers it
        pass
    return os.getenv(name)


SUPABASE_URL = get_setting("SUPABASE_URL")
SUPABASE_KEY = get_setting("SUPABASE_KEY")
APP_PASSWORD = get_setting("APP_PASSWORD")