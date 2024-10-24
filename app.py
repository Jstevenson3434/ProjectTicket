import datetime
import pandas as pd
import streamlit as st
import requests
import json
import base64
from io import StringIO
import time  # Import time for sleep function

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
    return response.status_code in (200, 201)

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

# Initialize DataFrame in session state if not already loaded
if 'df' not in st.session_state:
    st.session_state.df = load_projects_from_github()

# Initialize session state for form fields if not set
for key in ['name', 'title', 'description', 'bc', 'roi_hours_saved', 'roi_money_saved', 'department', 'priority']:
    if key not in st.session_state:
        st.session_state[key] = ""

# Function to submit the form
def submit():
    # Store values from input fields in session state
    st.session_state.name = st.session_state.widget_name
    st.session_state.title = st.session_state.widget_title
    st.session_state.description = st.session_state.widget_description
    st.session_state.bc = st.session_state.widget_bc
    st.session_state.roi_hours_saved = st.session_state.widget_roi_hours_saved
    st.session_state.roi_money_saved = st.session_state.widget_roi_money_saved
    st.session_state.department = st.session_state.widget_department
    st.session_state.priority = st.session_state.widget_priority

    # Create a new project DataFrame
    recent_project_number = len(st.session_state.df) + 1100  # Start IDs from PROJECT-1100
    today = datetime.datetime.now().strftime("%m-%d-%Y")
    
    df_new = pd.DataFrame(
        [
            {
                "ID": f"PROJECT-{recent_project_number}",
                "Name": st.session_state.widget_name,
                "Title": st.session_state.widget_title,
                "Description": st.session_state.widget_description,
                "Business Case": st.session_state.widget_bc,
                "Status": "Open",
                "Priority": st.session_state.widget_priority,
                "Date Submitted": today,
                "Reviewed Priority": "Set After Review",
                "ROI (hours saved per day)": st.session_state.widget_roi_hours_saved,
                "ROI (financial savings)": st.session_state.widget_roi_money_saved,
                "Department": st.session_state.widget_department
            }
        ]
    )

    # Append the new project to the existing DataFrame
    st.session_state.df = pd.concat([st.session_state.df, df_new], ignore_index=True)

    # Save to GitHub
    content = st.session_state.df.to_csv(index=False)
    if save_to_github(content):
        st.success("Project ticket saved to GitHub!")
    else:
        st.error("Failed to save project ticket to GitHub.")
    
    # Add a delay before clearing fields
    time.sleep(0.25)  # Wait for 1 second

    # Reset the input fields
    st.session_state.widget_name = ""
    st.session_state.widget_title = ""
    st.session_state.widget_description = ""
    st.session_state.widget_bc = ""
    st.session_state.widget_roi_hours_saved = 0
    st.session_state.widget_roi_money_saved = 0.0
    st.session_state.widget_department = departments[0]
    st.session_state.widget_priority = "Medium"

# Show a section to add a new project.
st.header("Add a new project")

# Display the form
with st.form("add_project_form"):
    st.text_input("Name", key="widget_name")
    st.text_input("Project Title", key="widget_title")
    st.text_area("Project Description", key="widget_description")
    st.text_area("Business Case", key="widget_bc")
    
    # New ROI fields
    st.number_input("ROI (hours saved per day)", min_value=0, step=1, key="widget_roi_hours_saved")
    st.number_input("ROI (financial savings)", min_value=0.0, step=100.0, key="widget_roi_money_saved")

    # Department dropdown
    st.selectbox("Department", departments, key="widget_department")
    
    # Priority selection
    st.selectbox("Priority", ["High", "Medium", "Low"], key="widget_priority")
    
    submitted = st.form_submit_button("Submit", on_click=submit)

# Display the existing projects table for all users
st.dataframe(st.session_state.df, use_container_width=True)
