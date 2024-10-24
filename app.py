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
import time

# Define departments for dropdown
departments = [
    "Administration", "Finance", "Production", "Quality Control", "Logistics",
    "Maintenance", "Human Resources", "Safety", "IT", "Research and Development",
    "Sales", "Marketing", "Purchasing", "Customer Service"
]

# Define the GitHub repository information and the CSV file path.
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "jstevenson3434"  # Replace with your GitHub username
REPO_NAME = "ProjectTicket"  # Replace with your GitHub repository name
CSV_FILE_PATH = "Data.csv"  # The path to your CSV file in the repo

# Get the GitHub token from the secrets
GITHUB_TOKEN = st.secrets["github_token"]

# Check if the token was retrieved
if not GITHUB_TOKEN:
    st.error("GitHub token not found! Please set the GITHUB_TOKEN environment variable.")
    st.stop()

# Admin login credentials stored in secrets
ADMIN_USERNAME = st.secrets["admin_username"]
ADMIN_PASSWORD = st.secrets["admin_password"]

# Set page configuration with a wide layout.
st.set_page_config(page_title="Analytics and AI Project Management System", page_icon="📊")
st.title("📊 Analytics and AI Project Submission Portal")
st.write(
    """
    This portal is designed for users to submit their Business Intelligence project ideas in one centralized location for review, priority setting, and timeline planning.
    """
)

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
        time.sleep(1)  # Delay to ensure the message is displayed
        reset_form()
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
        # Decode the content from base64
        content = response.json()['content']
        decoded_content = pd.read_csv(StringIO(base64.b64decode(content).decode()))
        return decoded_content
    else:
        # Create an empty DataFrame with specified columns.
        columns = ["ID", "Name", "Title", "Description", "Business Case", "Status", "Priority", 
                   "Date Submitted", "Reviewed Priority", "ROI (hours saved per day)", "ROI (financial savings)", "Department"]
        return pd.DataFrame(columns=columns)

# Function to reset form fields
def reset_form():
    st.session_state.name = ''
    st.session_state.title = ''
    st.session_state.description = ''
    st.session_state.bc = ''
    st.session_state.roi_hours_saved = 0
    st.session_state.roi_money_saved = 0.0
    st.session_state.department = departments[0]
    st.session_state.priority = 'Medium'

# Initialize DataFrame
st.session_state.df = load_projects_from_github()

# Show admin login
st.header("Admin Login")
admin_username = st.text_input("Username", type="text")
admin_password = st.text_input("Password", type="password")

if st.button("Login"):
    if admin_username == ADMIN_USERNAME and admin_password == ADMIN_PASSWORD:
        st.success("Logged in as admin.")
        admin_mode = True  # Set a flag for admin mode
    else:
        st.error("Invalid credentials, please try again.")

if 'admin_mode' in locals() and admin_mode:
    # Admin functionality (like editing the DataFrame) can go here
    st.write("Admin functionalities can be implemented here.")
    # For example, allow editing the DataFrame directly or other admin tasks.

# Show a section to add a new project.
st.header("Submit a New Project")

with st.form("add_project_form"):
    name = st.text_input("Name", key="name", help="Enter your name here.")
    title = st.text_input("Project Title", key="title", help="Enter the title of your project.")
    description = st.text_area("Project Description", key="description", help="Provide a brief description of your project.")
    bc = st.text_area("Business Case", key="bc", help="Explain the business case for your project.")
    
    # New ROI fields
    roi_hours_saved = st.number_input("ROI (hours saved per day)", min_value=0, step=1, key="roi_hours_saved", help="Estimated hours saved daily by this project.")
    roi_money_saved = st.number_input("ROI (financial savings)", min_value=0.0, step=100.0, key="roi_money_saved", help="Estimated financial savings per year.")

    # Department dropdown
    department = st.selectbox("Department", departments, key="department", help="Select the department this project relates to.")
    
    # Move Priority to the bottom
    priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="priority", help="Select the priority level for this project.")
    
    submitted = st.form_submit_button("Submit")

if submitted:
    # Check if any required fields are empty
    if not name:
        st.error("Please enter a name for the project.")
    elif not title:
        st.error("Please enter a project title.")
    elif not description:
        st.error("Please enter a project description.")
    elif not bc:
        st.error("Please enter a business case.")
    else:
        recent_project_number = len(st.session_state.df) + 1100  # Start IDs from PROJECT-1100
        today = datetime.datetime.now().strftime("%m-%d-%Y")
        
        # Create a DataFrame for the new project
        df_new = pd.DataFrame(
            [
                {
                    "ID": f"PROJECT-{recent_project_number}",
                    "Name": name,
                    "Title": title,
                    "Description": description,
                    "Business Case": bc,
                    "Status": "Open",
                    "Priority": priority,
                    "Date Submitted": today,
                    "Reviewed Priority": "Set After Review",
                    "ROI (hours saved per day)": roi_hours_saved,
                    "ROI (financial savings)": roi_money_saved,
                    "Department": department
                }
            ]
        )

        st.write("Project submitted! Here are the project details:")
        st.dataframe(df_new, use_container_width=True, hide_index=True)

        # Append the new project to the existing DataFrame and save it to GitHub.
        st.session_state.df = pd.concat([st.session_state.df, df_new], ignore_index=True)

        content = st.session_state.df.to_csv(index=False)
        save_to_github(content)

# Display the existing projects table for all users
st.dataframe(st.session_state.df, use_container_width=True)
