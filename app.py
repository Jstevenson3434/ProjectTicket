
import datetime
import os
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import requests
import json
import base64  # Import base64

# Define the GitHub repository information and the CSV file path.
GITHUB_API_URL = "https://api.github.com"
REPO_OWNER = "jstevenson3434"  # Replace with your GitHub username
REPO_NAME = "ProjectTicket"  # Replace with your GitHub repository name
CSV_FILE_PATH = "Data.csv"  # The path to your CSV file in the repo
GITHUB_TOKEN = "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"  # Replace with your GitHub token

# Function to get SHA of the file
def get_sha_of_file():
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{CSV_FILE_PATH}"
    response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    return response.json()['sha'] if response.status_code == 200 else None

# Function to save the content to GitHub
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

# Load existing projects from GitHub or create an empty DataFrame if the file doesn't exist.
def load_projects_from_github():
    url = f"{GITHUB_API_URL}/repos/{REPO_OWNER}/{REPO_NAME}/contents/{CSV_FILE_PATH}"
    response = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})

    if response.status_code == 200:
        # Decode the content from base64
        content = response.json()['content']
        decoded_content = pd.read_csv(pd.compat.StringIO(base64.b64decode(content).decode()))
        return decoded_content
    else:
        # Create an empty DataFrame with specified columns.
        columns = ["ID", "Title", "Description", "Status", "Priority", "Date Submitted"]
        return pd.DataFrame(columns=columns)

# Show app title and description.
st.set_page_config(page_title="Project Management System", page_icon="📊")
st.title("📊 Project Management System")
st.write(
    """
    This app shows how you can build an internal tool in Streamlit for project management. Here, we are 
    implementing a project ticket workflow. Users can create new projects, edit existing projects, and view some statistics.
    """
)

# Initialize DataFrame
st.session_state.df = load_projects_from_github()

# Show a section to add a new project.
st.header("Add a new project")

with st.form("add_project_form"):
    title = st.text_input("Project Title")
    description = st.text_area("Project Description")
    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
    submitted = st.form_submit_button("Submit")

if submitted:
    # Create a DataFrame for the new project and append it to the DataFrame in session state.
    recent_project_number = len(st.session_state.df) + 1100  # Start IDs from PROJECT-1100
    today = datetime.datetime.now().strftime("%m-%d-%Y")
    df_new = pd.DataFrame(
        [
            {
                "ID": f"PROJECT-{recent_project_number}",
                "Title": title,
                "Description": description,
                "Status": "Open",
                "Priority": priority,
                "Date Submitted": today,
            }
        ]
    )

    # Show a success message.
    st.write("Project submitted! Here are the project details:")
    st.dataframe(df_new, use_container_width=True, hide_index=True)

    # Append the new project to the existing DataFrame and save it to GitHub.
    st.session_state.df = pd.concat([st.session_state.df, df_new], axis=0)

    # Save to GitHub
    content = st.session_state.df.to_csv(index=False)
    save_to_github(content)

# Show section to view and edit existing projects in a table.
st.header("Existing Projects")
st.write(f"Number of projects: `{len(st.session_state.df)}`")

st.info(
    "You can edit the projects by double-clicking on a cell. Note how the plots below "
    "update automatically! You can also sort the table by clicking on the column headers.",
    icon="✍️",
)

# Show the projects DataFrame with `st.data_editor`. This lets the user edit the table cells.
edited_df = st.data_editor(
    st.session_state.df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Project status",
            options=["Open", "In Progress", "Completed"],
            required=True,
        ),
        "Priority": st.column_config.SelectboxColumn(
            "Priority",
            help="Project priority",
            options=["High", "Medium", "Low"],
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

# Show metrics side by side using `st.columns` and `st.metric`.
col1, col2 = st.columns(2)
num_open_projects = len(st.session_state.df[st.session_state.df.Status == "Open"])
col1.metric(label="Number of open projects", value=num_open_projects)
col2.metric(label="Total projects submitted", value=len(st.session_state.df))

# Show two Altair charts using `st.altair_chart`.
st.write("##### Project status distribution")
status_plot = (
    alt.Chart(edited_df)
    .mark_bar()
    .encode(
        x="Status:N",
        y="count():Q",
        color="Status:N",
    )
)
st.altair_chart(status_plot, use_container_width=True, theme="streamlit")

st.write("##### Current project priorities")
priority_plot = (
    alt.Chart(edited_df)
    .mark_arc()
    .encode(theta="count():Q", color="Priority:N")
    .properties(height=300)
)
st.altair_chart(priority_plot, use_container_width=True, theme="streamlit")

