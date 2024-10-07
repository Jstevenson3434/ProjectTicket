import datetime
import os
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import base64  # Import base64 module
from io import StringIO  # Import StringIO from io module 

# Define the GitHub repository information and the CSV file path.
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "jstevenson3434"  # Replace with your GitHub username
REPO_NAME = "ProjectTicket"  # Replace with your GitHub repository name
CSV_FILE_PATH = "Data.csv"  # The path to your CSV file in the repo
GITHUB_TOKEN = "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"  # Replace with your GitHub token

# Set page configuration with a wide layout.
st.set_page_config(page_title="Project Management System", page_icon="📊")
st.title("📊 Project Management System")
st.write(
    """
    Please utilize this app to submit projects for review.
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
        columns = ["ID", "Title", "Description", "Status", "Priority", "Date Submitted", "Reviewed Priority"]
        return pd.DataFrame(columns=columns)

# Initialize DataFrame
st.session_state.df = load_projects_from_github()

# Show a section to add a new project.
st.header("Add a new project")

with st.form("add_project_form"):
    name = st.text_input("Name")
    title = st.text_input("Project Title")
    description = st.text_area("Project Description")
    bc = st.text_area("Business Case")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
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

# Sidebar for login
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False

st.sidebar.header("Login")
if not st.session_state.is_authenticated:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    login_button = st.sidebar.button("Login")

    if login_button:
        # Replace with your actual login validation logic
        if username == "your_username" and password == "your_password":  # Change to your logic
            st.session_state.is_authenticated = True
            st.success("You are logged in!")
        else:
            st.error("Invalid username or password.")

# If the user is authenticated, show the edit section
if st.session_state.is_authenticated:
    # Show the projects DataFrame with st.data_editor. This lets the user edit the table cells.
    edited_df = st.data_editor(
        st.session_state.df,
        use_container_width=True,  # This ensures the table uses the full width of the container
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
        },
        # Disable editing the ID and Date Submitted columns.
        disabled=["ID", "Date Submitted"],
    )

    # Update the session state DataFrame with edited data and save to GitHub.
    if not edited_df.equals(st.session_state.df):
        st.session_state.df = edited_df
        content = st.session_state.df.to_csv(index=False)
        save_to_github(content)

# Show some metrics and charts about the projects.
st.header("Statistics")

# Show metrics side by side using st.columns and st.metric.
col1, col2 = st.columns(2)
num_open_projects = len(st.session_state.df[st.session_state.df.Status == "Open"])
col1.metric(label="Number of open projects", value=num_open_projects)
col2.metric(label="Total projects submitted", value=len(st.session_state.df))

# Show two Altair charts using st.altair_chart.
st.write("##### Project status distribution")
status_plot = (
    alt.Chart(st.session_state.df)
    .mark_bar()
    .encode(
        x="Status:N",
        y="count():Q",
        color="Status:N",
    )
)
st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

st.write("##### Projects via Person")
name_plot = (
    alt.Chart(st.session_state.df)
    .mark_bar()
    .encode(
        x="Name:N",
        y="count():Q",
    )
)
st.altair_chart(name_plot, use_container_width=True, theme="streamlit")
