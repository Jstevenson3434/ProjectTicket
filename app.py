import datetime
import pandas as pd
import streamlit as st
import requests
import json
import base64
from io import StringIO

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
        # Decode the content from base64
        content = response.json()['content']
        decoded_content = pd.read_csv(StringIO(base64.b64decode(content).decode()))
        return decoded_content
    else:
        # Create an empty DataFrame with specified columns.
        columns = ["ID", "Name", "Title", "Description", "Business Case", "Status", "Priority", 
                   "Date Submitted", "Reviewed Priority", "ROI (hours saved per day)", "ROI (financial savings)", "Department"]
        return pd.DataFrame(columns=columns)

# Initialize DataFrame in session state if not already loaded
if 'df' not in st.session_state:
    st.session_state.df = load_projects_from_github()

# Function to reset form fields
def reset_form():
    st.session_state['name'] = ''
    st.session_state['title'] = ''
    st.session_state['description'] = ''
    st.session_state['bc'] = ''
    st.session_state['roi_hours_saved'] = 0
    st.session_state['roi_money_saved'] = 0.0
    st.session_state['department'] = departments[0]
    st.session_state['priority'] = 'Medium'

# Initialize form state if not already set
if 'name' not in st.session_state:
    reset_form()

# Show a section to add a new project.
st.header("Add a new project")

# Display the form
with st.form("add_project_form"):
    name = st.text_input("Name", value=st.session_state.name, key="name")
    title = st.text_input("Project Title", value=st.session_state.title, key="title")
    description = st.text_area("Project Description", value=st.session_state.description, key="description")
    bc = st.text_area("Business Case", value=st.session_state.bc, key="bc")
    
    # New ROI fields
    roi_hours_saved = st.number_input("ROI (hours saved per day)", min_value=0, step=1, value=st.session_state.roi_hours_saved, key="roi_hours_saved")
    roi_money_saved = st.number_input("ROI (financial savings)", min_value=0.0, step=100.0, value=st.session_state.roi_money_saved, key="roi_money_saved")

    # Department dropdown
    department = st.selectbox("Department", departments, index=departments.index(st.session_state.department), key="department")
    
    # Priority selection
    priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=["High", "Medium", "Low"].index(st.session_state.priority), key="priority")
    
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

        # Reset the form fields after submission
        reset_form()

# Display the existing projects table for all users
st.dataframe(st.session_state.df, use_container_width=True)
