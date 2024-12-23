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

# Set page configuration with a wide layout.
st.set_page_config(page_title="Analytics and AI Project Management System", page_icon="📊")
st.title("📊 Analytics and AI Project Management System")
st.write(
    """
    Please utilize this app to submit all data analytic and artificial intelligence project ideas for priority
    and completion date review.
    
    Please leave any potentialy confidential information out of this portal. 
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
    return response

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
                   "Date Submitted", "Reviewed Priority", "ROI (hours saved annualy)", "ROI (financial savings annualy)", "Department"]
        return pd.DataFrame(columns=columns)

# Initialize DataFrame
st.session_state.df = load_projects_from_github()

# Admin login
admin_username = st.secrets["admin_username"]  # Store admin username as a Streamlit secret
admin_password = st.secrets["admin_password"]  # Store admin password as a Streamlit secret

# Sidebar for Admin Login
st.sidebar.header("Admin Login")
admin_input_username = st.sidebar.text_input("Username", type="password")
admin_input_password = st.sidebar.text_input("Password", type="password", value="", placeholder="Enter password", label_visibility="collapsed")

if st.sidebar.button("Login"):
    if admin_input_username == admin_username and admin_input_password == admin_password:
        st.sidebar.success("Logged in as Admin")
        is_admin = True  # Set admin flag to True
    else:
        st.sidebar.error("Invalid username or password")
        is_admin = False
else:
    is_admin = False

# Show a section to add a new project.
st.header("Analytics and Artificial Intelligence Project Submission Portal")

# Use session state to reset form values after submission
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Reset session state fields if form is submitted
if st.session_state.submitted:
    st.session_state.name = ''
    st.session_state.title = ''
    st.session_state.description = ''
    st.session_state.bc = ''
    st.session_state.roi_hours_saved = 0
    st.session_state.roi_money_saved = 0.0
    st.session_state.department = departments[0]
    st.session_state.priority = 'Medium'
    st.session_state.submitted = False

with st.form("add_project_form"):
    name = st.text_input("Name", key="name", help="Enter Your Name")
    title = st.text_input("Project Title", key="title", help="Enter the title of the project")
    description = st.text_area("Project Description", key="description", help="Provide a brief description of the project and what you want it to accomplish")
    bc = st.text_area("Business Case", key="bc", help="Explain how this projects benifits the company (will help determine priority)")
    
    # New ROI fields
    roi_hours_saved = st.number_input("ROI (hours saved annualy)", min_value=0, step=1, key="roi_hours_saved", help="If applicable estimate the hours this project will save per day")
    roi_money_saved = st.number_input("ROI (financial savings annualy)", min_value=0.0, step=100.0, key="roi_money_saved", help="If applicable estimate the financial savings of this project per day")

    # Department dropdown
    department = st.selectbox("Department", departments, key="department", help="Select the department related to the project")
    
    # Move Priority to the bottom
    priority = st.selectbox("Priority", ["High", "Medium", "Low"], key="priority", help="Select the priority of the project")
    
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
                    "ROI (hours saved annualy)": roi_hours_saved,
                    "ROI (financial savings annualy)": roi_money_saved,
                    "Department": department
                }
            ]
        )

        st.write("Project submitted! Here are the project details:")
        st.dataframe(df_new, use_container_width=True, hide_index=True)

        # Append the new project to the existing DataFrame and save it to GitHub.
        st.session_state.df = pd.concat([st.session_state.df, df_new], ignore_index=True)

        content = st.session_state.df.to_csv(index=False)
        response = save_to_github(content)

        if response.status_code in (201, 200):
            st.success("Project ticket saved to GitHub!")
            # Delay clearing the input fields
            time.sleep(1)
            st.session_state.submitted = True
        else:
            st.error("Failed to save project ticket to GitHub.")

# Display the existing projects table for all users
st.session_state.df = st.session_state.df.sort_values(by='Date Submitted', ascending=False)
st.dataframe(st.session_state.df, use_container_width=True)


# Admin functionality to edit the DataFrame
if is_admin:
    st.header("Admin Section: Edit Projects")
    edited_df = st.data_editor(st.session_state.df, use_container_width=True)

    if st.button("Save Changes"):
        content = edited_df.to_csv(index=False)
        response = save_to_github(content)

        if response.status_code in (201, 200):
            st.success("Changes saved to GitHub!")
        else:
            st.error("Failed to save changes to GitHub.")
