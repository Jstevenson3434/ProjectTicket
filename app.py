import datetime
import os
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import base64
from io import StringIO

# Define the GitHub repository information and the CSV file path.
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "jstevenson3434"  # Replace with your GitHub username
REPO_NAME = "ProjectTicket"  # Replace with your GitHub repository name
CSV_FILE_PATH = "Data.csv"  # The path to your CSV file in the repo

# Get the GitHub token from the environment variable or Streamlit secrets
GITHUB_TOKEN = st.secrets["github_token"]

if not GITHUB_TOKEN:
    st.error("GitHub token not found! Please set the GitHub token in Streamlit secrets.")
    st.stop()

# Set page configuration with a wide layout.
st.set_page_config(page_title="Analytics and AI Project Management System", page_icon="📊")
st.title("📊 Analytics and AI Project Management System")
st.write("""
    Please utilize this app to submit all data analytic and artificial intelligence project ideas for priority and completion date review.
""")

# Login credentials from Streamlit secrets
ADMIN_USERNAME = st.secrets["admin"]["username"]
ADMIN_PASSWORD = st.secrets["admin"]["password"]

# Function to save content to GitHub
def save_to_github(content):
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{CSV_FILE_PATH}"
    response = requests.put(
        url,
        headers={"Authorization": f"token {GITHUB_TOKEN}"},
        data=json.dumps({
            "message": "Update Project_Ticket.csv",
            "content": base64.b64encode(content.encode()).decode(),
            "sha": get_sha_of_file()
        })
    )
    if response.status_code in (201, 200):
        st.success("Project ticket saved to GitHub!")
    else:
        st.error("Failed to save project ticket to GitHub.")

# Function to get SHA of the existing file on GitHub
def get_sha_of_file():
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{CSV_FILE_PATH}"
    response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    return response.json()['sha'] if response.status_code == 200 else None

# Function to load existing projects from GitHub
def load_projects_from_github():
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{CSV_FILE_PATH}"
    response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})

    if response.status_code == 200:
        content = response.json()['content']
        decoded_content = pd.read_csv(StringIO(base64.b64decode(content).decode()))
        return decoded_content
    else:
        columns = ["ID", "Name", "Title", "Description", "Business Case", "Status", "Priority", 
                   "Date Submitted", "Reviewed Priority", "ROI (hours saved per day)", "ROI (financial savings)", "Department"]
        return pd.DataFrame(columns=columns)

# Initialize DataFrame
st.session_state.df = load_projects_from_github()

# Sidebar for login
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False

st.sidebar.header("Admin Login")
if not st.session_state.is_authenticated:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")

    if login_button:
        # Check credentials using Streamlit secrets
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.is_authenticated = True
            st.success("You are logged in!")
        else:
            st.error("Invalid username or password.")

# If the user is authenticated, show the project table
if st.session_state.is_authenticated:
    edited_df = st.data_editor(
        st.session_state.df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                help="Project status",
                options=["Open", "Under Review", "In Progress", "Completed"],
                required=True,
            ),
            "Priority": st.column_config.SelectboxColumn(
                "Priority",
                help="Project priority",
                options=["High", "Medium", "Low"],
                required=True,
            ),
            "Reviewed Priority": st.column_config.SelectboxColumn(
                "Reviewed Priority",
                help="Project reviewed priority",
                options=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
                required=True,
            ),
            "ROI (hours saved per day)": st.column_config.NumberColumn(
                "ROI (hours saved per day)",
                help="Estimated hours saved",
                required=True,
            ),
            "ROI (financial savings)": st.column_config.NumberColumn(
                "ROI (financial savings)",
                help="Estimated money saved",
                required=True,
            ),
            "Department": st.column_config.SelectboxColumn(
                "Department",
                help="Select the department for the project",
                options=departments,
                required=True,
            ),
        },
        disabled=["ID", "Date Submitted"],
    )

    # Save the edited DataFrame to GitHub
    if not edited_df.equals(st.session_state.df):
        st.session_state.df = edited_df
        content = st.session_state.df.to_csv(index=False)
        save_to_github(content)

# Statistics and charts remain unchanged
