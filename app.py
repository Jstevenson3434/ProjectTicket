import datetime
import os
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# Define the CSV file path for saving projects.
CSV_FILE_PATH = "S:\Justin Stevenson\Project File\Project_Ticket.csv"

# Show app title and description.
st.set_page_config(page_title="Project Management System", page_icon="📊")
st.title("📊 Project Management System")
st.write(
    """
    This app shows how you can build an internal tool in Streamlit for project management. Here, we are 
    implementing a project ticket workflow. Users can create new projects, edit existing projects, and view some statistics.
    """
)

# Load existing projects from the CSV file if it exists, otherwise create an empty DataFrame.
if os.path.exists(CSV_FILE_PATH):
    st.session_state.df = pd.read_csv(CSV_FILE_PATH)
else:
    # Create an empty DataFrame with specified columns.
    columns = ["ID", "Title", "Description", "Status", "Priority", "Date Submitted"]
    st.session_state.df = pd.DataFrame(columns=columns)

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

    # Append the new project to the existing DataFrame and save it to CSV.
    st.session_state.df = pd.concat([st.session_state.df, df_new], axis=0)
    st.session_state.df.to_csv(CSV_FILE_PATH, index=False)  # Save to CSV

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

# Update the session state DataFrame with edited data.
if not edited_df.equals(st.session_state.df):
    st.session_state.df = edited_df
    st.session_state.df.to_csv(CSV_FILE_PATH, index=False)  # Save to CSV

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
