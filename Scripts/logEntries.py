import streamlit as st
import pandas as pd
import os
from datetime import datetime
import streamlit.components.v1 as components

# Streamlit script to automate the collection and saving of Student IDs at the beginning
#   of lab. Students swipe their ID card to enter their student ID. The ID number and
#   their time of entry are recorded in a pandas database. When the section is finished,
#   the TA saves the file locally, then is taken to an upload site in another browser
#   tab. After uploading, the TA signs out using a button.
#
#   Usage: streamlit run logEntries.py
#
#   Melissa A. Hines, Dept. of Chemistry, Cornell University
#   Melissa.Hines@cornell.edu   December 20, 2025

DATA_SITE = 'https://cornell.app.box.com/f/c27d552e7bf64c4d914c2a9366cca0ce'

@st.dialog('Enter TA name before proceeding', dismissible=False)
def nameOfTA_dialog():
    """ Use a modal dialog to ask the user for a name for the analysis. This will appear at the top of the main page"""

    user_input = st.text_input('TA Name:',
                                key="dialog_input")
    
    # Check if the user clicked the 'Submit' button inside the form
    if st.button('Submit'):
        if user_input:
            # Store the input in session state to access it in the main app
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime('%a_%b_%d_%Y_') # Ex Sat_Dec_20_2025_
            if int(current_datetime.strftime('%H')) < 12:
                formatted_datetime += 'morning'
            else:
                formatted_datetime += 'afternoon'
            st.session_state['TA_name'] = user_input
            st.session_state['filename'] = user_input + ' ' + formatted_datetime + '.csv'
            
            # Set up the dataframe to hold the students
            column_names = ['ID', 'Time']
            entries_df = pd.DataFrame(columns=column_names)
            st.session_state.entries_df = entries_df
    
            st.session_state['class_initiated'] = True   
            
            st.rerun() # Rerun the app to close the dialog and update the main view
        else:
            st.warning("Please enter a non-empty string.")

# Function to inject JavaScript for focusing the input
def focus_text_input():
    # This script searches for text inputs and focuses the first one
    js_script = """
    <script>
        var input = window.parent.document.querySelectorAll("input[type=text]");
        for (var i = 0; i < input.length; ++i) {
            input[i].focus();
        }
    </script>
    """
    components.html(js_script, height=0, width=0)

def submit_ID():
    st.session_state.last_input = st.session_state.card_input
    st.session_state.card_input = ''
    cornellID_number = st.session_state.last_input[8:15]
    
    current_datetime = datetime.now()
    formatted_datetime = current_datetime.strftime("%A, %d %B %Y, %I:%M %p")
    
    new_entry = [cornellID_number, formatted_datetime]
    
    st.session_state.entries_df.loc[len( st.session_state.entries_df)] = new_entry
    st.session_state['df_populated'] = True
    
def save_attendance_file():
    
    filename = '/Users/mah/Desktop/testFile.csv'
    cwd = os.getcwd()
    filePath = cwd + '/' + st.session_state['filename']
    st.session_state.entries_df.to_csv(filePath, 
                                       index=False,
                                       encoding='utf-8')
    st.session_state['file_saved'] = True
    
def sign_out():
    st.session_state['class_initiated'] = False
    st.session_state['file_saved'] = False
    st.session_state['df_populated'] = False
    st.session_state['TA_name'] = 'Unknown TA'
    st.session_state['filename'] = 'unknown'
    st.session_state.entries_df = None
    
# Initialization
if 'class_initiated' not in st.session_state:
    st.session_state['class_initiated'] = False
if 'file_saved' not in st.session_state:
    st.session_state['file_saved'] = False
if 'df_populated' not in st.session_state:
    st.session_state['df_populated'] = False
if 'TA_name' not in st.session_state:
    st.session_state['TA_name'] = 'Unknown TA'
if 'filename' not in st.session_state:
    st.session_state['filename'] = 'unknown'
    
# Display the TA Name
st.title(st.session_state['TA_name'] + '\'s Section')

if not st.session_state['class_initiated']:
    nameOfTA_dialog()

if st.button('Update TA Name'):
    nameOfTA_dialog()
    
if not st.session_state['TA_name'] == 'Unknown TA':

    card_data = st.text_input("Students must swipe their Cornell ID. Make sure the cursor is in the field below before swiping.",
                              key = 'card_input',
                              on_change = submit_ID)
    
    # Display database for entries
    st.dataframe(st.session_state.entries_df)
    
if st.session_state['df_populated']:
    st.write('Data will be saved to file = ' + st.session_state['filename'])
    st.button('Write attendance file to disk',
                key = 'save_file_button',
                on_click = save_attendance_file)
    

if st.session_state['file_saved']:
    st.write("""Upload your saved attendance file to Box using the uploader link below,
     then come back and sign out. You may save the attendance file multiple
      times before uploading""")
    st.link_button(':blue[Open file uploader]', DATA_SITE)
    st.button('Sign out after uploading and before leaving',
               key = 'sign_out',
               on_click = sign_out)
    
# Call the function to focus the input at the end of the script. This attempts to keep the cursor in the text box.
focus_text_input()
