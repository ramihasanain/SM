import streamlit as st
import requests

# Set page config for a wider layout and better title
st.set_page_config(page_title="AI Social Analysis Dashboard", layout="wide")

# The base URL of your Django API (assuming it's running locally here)
API_BASE_URL = "http://127.0.0.1:8000/api"

st.title("📊 AI Social Analysis Dashboard")

# Create tabs for different sections
tabs = st.tabs(["Users", "Profiles", "Posts", "Analytics"])

# ==========================================
# USERS TAB
# ==========================================
with tabs[0]:
    st.header("Platform Users")
    
    # Refresh button
    if st.button("Refresh Users"):
        try:
            response = requests.get(f"{API_BASE_URL}/users/")
            if response.status_code == 200:
                users = response.json()
                st.dataframe(users, use_container_width=True)
            else:
                st.error("Failed to fetch users from the API.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

# ==========================================
# PROFILES TAB
# ==========================================
with tabs[1]:
    st.header("Social Profiles")
    
    if st.button("Refresh Profiles"):
        try:
            response = requests.get(f"{API_BASE_URL}/profiles/")
            if response.status_code == 200:
                profiles = response.json()
                st.dataframe(profiles, use_container_width=True)
            else:
                st.error("Failed to fetch profiles.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

# ==========================================
# POSTS TAB
# ==========================================
with tabs[2]:
    st.header("Analyzed Posts")
    
    if st.button("Refresh Posts"):
        try:
            response = requests.get(f"{API_BASE_URL}/posts/")
            if response.status_code == 200:
                posts = response.json()
                st.dataframe(posts, use_container_width=True)
            else:
                st.error("Failed to fetch posts.")
        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

# ==========================================
# ANALYTICS TAB
# ==========================================
with tabs[3]:
    st.header("System Analytics overview")
    st.info("Here you can build out charts using the sentiment-results and analysis-batches endpoints.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Total Scrape Jobs Runs", value="--")
    with col2:
        st.metric(label="Total Reports Generated", value="--")

st.markdown("---")
st.caption("Developed with Streamlit and Django REST Framework")
