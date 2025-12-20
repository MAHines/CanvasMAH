import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import streamlit.components.v1 as components

# This is a streamlit package that is designed primarily to analyze a folder of Gradescope
#   scores for an assignment. To get the folder, open the assignment in Gradescope and select
#   "Export Evaluations" at the bottom of the page.
#
#   Drag the folder onto "Drag and drop files here." Give the analysis a name in the modal dialog.
#   An analysis of all problems will appear. To analyze a single problem, use the dropdown menu
#   in the sidebar to select it.
#
#   Usage: streamlit run multifileAnalysis.py


def read_gradescope_csv(file_str):

    # The Gradescope csv's have a bunch of columns that are not useful to us. We avoid loading them
    columns = ['SID', 'Score', 'Grader']
    usecols = lambda x: (x in columns)

    gs_df = pd.read_csv(file_str,
                        usecols = usecols,
                        skipfooter=4,   # Skips crap at end of file
                        engine='python'
                        )
                        
    # Now summarize by grader
    grader_df = summarize_by_grader(gs_df, 'Score', 'Grader')
    
    # Need to give the Score and Grade columns unique names for this file
    problemName = file_str.name.removesuffix('.csv')
    # problemName = file_str.removesuffix('.csv')
    
    columnsToRename = ['Score', 'Grader']
    gsRenamedColumns = []
    for oldName in columnsToRename:
        newName = oldName + '_' + problemName
        gs_df.rename(columns={oldName: newName}, inplace=True)
        gsRenamedColumns.append(newName)
    
    columnsToRename = ['mean', 'std dev', 'count']
    graderRenamedColumns = []
    for oldName in columnsToRename:
        newName = oldName + '_' + problemName
        grader_df.rename(columns={oldName: newName}, inplace=True)
        graderRenamedColumns.append(newName)

    return problemName, gs_df, gsRenamedColumns, grader_df, graderRenamedColumns

def summarize_by_grader(df, scoreCol, graderCol):

    new_df = df[[scoreCol, graderCol]].groupby(graderCol).describe()
    new_df.columns = new_df.columns.droplevel(level=0)    
    # st.markdown(new_df.columns)
    
    # And all data
    all_df = df[[scoreCol]].describe()
    all_df = all_df.T
    all_df.rename(index={scoreCol: 'All'}, inplace=True)
    all_df.index.name = graderCol
    
    new_df = pd.concat([all_df, new_df])
    # new_df = new_df.rename(columns={new_df.columns[0]: graderCol})
    # st.markdown(new_df.columns)
    
    cols_to_drop = ['min', '25%', '50%', '75%', 'max']
    new_df = new_df.drop(columns = cols_to_drop)
    newOrder = ['mean', 'std', 'count']
    new_df = new_df[newOrder]
    new_df = new_df.rename(columns={'std': 'std dev'})
     
    return new_df
    
def prepare_graph(df):  # Create a bar chart with error bars
    
    plt_df = df.copy()
    plt_df['Grader'] = plt_df.index
    plt_df['sum_mean_sd'] = plt_df['mean'] + plt_df['std dev']
    plt_df['diff_mean_sd'] = plt_df['mean'] - plt_df['std dev']
    
    # Now put in order of mean
    df_header = plt_df.iloc[[0]]
    df_rest = plt_df.iloc[1:]
    df_rest = df_rest.sort_values(by='mean', ascending=True)
    plt_df = pd.concat([df_header, df_rest])
    fig = px.bar(
        plt_df,
        x='Grader',
        y="mean",
        error_y="std dev",
        color_discrete_sequence=['darkkhaki'],
        title="Mean and Std Dev by Grader"
    )
    fig.update_yaxes(range=[plt_df['diff_mean_sd'].min(), plt_df['sum_mean_sd'].max()])
    fig.add_hline(y=plt_df['mean'].iloc[0], annotation_text="mean", 
          line_dash="dot", line_color='black')
    return fig

@st.dialog('Enter string')
def nameOfAnalysis_dialog():
    # st.write('Data being analyzed.')
    user_input = st.text_input('Name of data being analyzed:',
                                key="dialog_input") # Use st.text_input for string
    
    # Check if the user clicked the 'Submit' button inside the form
    if st.button('Submit'):
        if user_input:
            # Store the input in session state to access it in the main app
            st.session_state['analysis_name'] = user_input
            st.rerun() # Rerun the app to close the dialog and update the main view
        else:
            st.warning("Please enter a non-empty string.")

if 'uploaded_files_list' not in st.session_state:
    st.session_state.uploaded_files_list = []
if 'analysis_done' not in st.session_state:
    st.session_state.analysis_done = False
if 'file_uploaded' not in st.session_state:
    st.session_state['file_uploaded'] = False
if 'uploaded_file_data' not in st.session_state:
    st.session_state['uploaded_file_data'] = None
if 'probNameList' not in st.session_state:
    st.session_state.probNameList = [' All']
if 'analysis_name' not in st.session_state:
    st.session_state['analysis_name'] = 'Analyze Exported Evaluations'
if 'current_problem' not in st.session_state:
    st.session_state['current_problem'] = 'Analysis of All Problems'
    

st.title(st.session_state['analysis_name'])
st.header(st.session_state['current_problem'])

def handle_upload_change():
    """Callback function to update session state when a file is uploaded."""
    # Check if a file was actually uploaded in the callback
    if st.session_state['uploader_key'] is not None:
        st.session_state['file_uploaded'] = True
        # Store the file details for later use
        st.session_state['uploaded_file_data'] = st.session_state['uploader_key']

def handle_problem_change():
    # Function to update session state when the problem to be analyzed is changed
    
    if st.session_state['file_uploaded'] and st.session_state['analysis_done']:
        if st.session_state.problem_select_box == ' All':
            st.session_state['current_problem'] = 'Analysis of All Problems'
            st.session_state.primaryGrader_df = summarize_by_grader(st.session_state.combo_df, 'Total','Primary Grader')
        else:
            st.session_state['current_problem'] = 'Analysis of ' + st.session_state.problem_select_box
            score_col = 'Score_' + st.session_state.problem_select_box
            grader_col = 'Grader_' + st.session_state.problem_select_box
            cols = ['SID', score_col, grader_col]
            sub_df = st.session_state.combo_df[cols].copy()
            st.session_state.primaryGrader_df = summarize_by_grader(sub_df, score_col, grader_col)
       
        st.session_state.fig = prepare_graph(st.session_state.primaryGrader_df)
     
def reset_uploader():
    """Function to clear the uploaded file and show the uploader again."""
    st.session_state['file_uploaded'] = False
    st.session_state['uploaded_file_data'] = None
    st.session_state['analysis_done'] = False
    st.session_state['analysis_name'] = 'Analyze Exported Evaluations'
    st.session_state['current_problem'] = 'Analysis of All Problems'
    # No need to explicitly clear the widget's value here;
    # hiding and showing it again effectively resets it.

# Logic to display the file uploader or the "Analyze a different file/folder" button
if not st.session_state['file_uploaded']:
    # Display the uploader only if no file has been uploaded yet
    st.file_uploader(
        "Upload your file(s) here:",
        type=['csv'],
        accept_multiple_files=True,
        key = 'uploader_key',
        on_change=handle_upload_change
    )
else:
    st.sidebar.button("Analyze a different file/folder.", on_click=reset_uploader)

allData = st.sidebar.checkbox('Show all data.', key = 3141)
allGraderData = st.sidebar.checkbox('Show all grader data', key = 3142)

if st.session_state['file_uploaded'] and not st.session_state['analysis_done']: # uploaded_files:

    nameOfAnalysis_dialog()
    
    for uploaded_file in st.session_state['uploaded_file_data']:
                
        # Read a file and generate a number of dataframes
        #   combo_df            This contains all of the data 
        #   comboGrader_df      This contains all of the data by primary grader
        #   primaryGrader_df    This contains the analysis by primary grader
        # The primary grader is defined to be the grader who grades the most of the assignment
        
        probName, gs_df,gsCols, grader_df, graderCols = read_gradescope_csv(uploaded_file)
        
        if 'combo_df' in locals():
            combo_df = pd.merge(combo_df, gs_df, on='SID', how='left')
            combo_df['Total'] = combo_df['Total'] + combo_df[gsCols[0]]
            graderNameCols.append(gsCols[1])
            combo_df['Primary Grader'] = combo_df[graderNameCols].mode(axis=1)[0]
            
            comboGrader_df = pd.merge(comboGrader_df, grader_df, on='Grader', how='left')
            comboGrader_df['mean'] = comboGrader_df['mean'] + comboGrader_df[graderCols[0]]
            
            primaryGrader_df = summarize_by_grader(combo_df, 'Total','Primary Grader')
            
            probNameList.append(probName)
        else:
            combo_df = gs_df
            combo_df['Total'] = gs_df[gsCols[0]]
            combo_df['Primary Grader'] = gs_df[gsCols[1]]
            graderNameCols = [gsCols[1]]  # Columns containing grader names
            cols = ['Total'] + ['Primary Grader'] + [col for col in combo_df.columns if col not in ['Total', 'Primary Grader']]
            combo_df = combo_df[cols]   # Reorder columns
            
            comboGrader_df = grader_df
            comboGrader_df['mean'] = grader_df[graderCols[0]]
            cols = ['mean'] + [col for col in comboGrader_df.columns if col != 'mean']
            comboGrader_df = comboGrader_df[cols] # Reorder columns
            
            primaryGrader_df = summarize_by_grader(combo_df, 'Total', 'Primary Grader')
            
            probNameList = [' All', probName]          
            
    st.session_state.probNameList = probNameList.sort()
    
    st.session_state.fig = prepare_graph(primaryGrader_df)
    
    st.session_state.analysis_done = True
    st.session_state.combinedData = st.empty()
    st.session_state.combo_df = combo_df
    st.session_state.comboGrader_df = comboGrader_df
    st.session_state.primaryGrader_df = primaryGrader_df
    st.session_state.probNameList = probNameList

if st.session_state['file_uploaded'] and st.session_state['analysis_done']:
    with st.session_state.combinedData.container():
        
        # Display the chart in the Streamlit app
        st.plotly_chart(st.session_state.fig, width = 'stretch')
        
        st.dataframe(st.session_state.primaryGrader_df)

        st.download_button(
            "Download Primary Grader Analysis",
            st.session_state.primaryGrader_df.to_csv().encode("utf-8"),
            'PrimaryGraderAnalysis.csv',
            "text/csv",
            key = 'primary_grader_download'
        )
        if allData:
            st.dataframe(st.session_state.combo_df)
            st.download_button(
                "Download All Data",
                st.session_state.combo_df.to_csv().encode("utf-8"),
                'AllData.csv',
                "text/csv",
                key = 'all_data_download'
            )
        if allGraderData:
            st.dataframe(st.session_state.comboGrader_df)
            st.download_button(
                "Download All Grader Data",
                st.session_state.comboGrader_df.to_csv().encode("utf-8"),
                'AllGraderData.csv',
                "text/csv",
                key = 'all_grader_data_download'
            )
        
        selected_problem = st.sidebar.selectbox(
                            'Problem to be analyzed:',
                            st.session_state.probNameList,
                            key = 'problem_select_box',
                            on_change=handle_problem_change)

