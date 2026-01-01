import streamlit as st
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta

LATE_MINUTES = 5.0   # If you are later than LATEMINUTES, you are tardy
FIRST_DATE = '2026-02-02' # Monday of first week of classes

def read_timesheet():

    timesheetFile = 'fakeTimesheet.csv'
    rosterFile = 'processedCanvasRoster.csv'
    
    # Read the timesheet, converting entry time to a datetime and the rest to strings
    timesheet_df =  pd.read_csv(timesheetFile, dtype=str) # ['course', 'TA', 'section', 'ID', 'Entry time']
    timesheet_df['Entry time'] = pd.to_datetime(timesheet_df['Entry time'], format = '%a, %d %b %y, %I:%M %p')
    timesheet_df.rename(columns = {'section': 'loggedSection'}, inplace = True)
    timesheet_df.rename(columns = {'ID': 'enteredID'}, inplace = True)
        
    # Read the roster
    roster_df = pd.read_csv(rosterFile, dtype=str)
    
    # Convert the roster into a mapping series for netID -> ID
    mapSeries_netID_to_ID = roster_df.set_index('netID')['ID']
    mapSeries_ID_to_section = roster_df.set_index('ID')['section']
    mapSeries_ID_to_name = roster_df.set_index('ID')['studentName']
    
    # Calculate sectionAttended from entry time 
    timesheet_df['sectionAttended'] = timesheet_df['Entry time'].dt.strftime('%a') + ' ' + timesheet_df['Entry time'].dt.strftime('%p')
    
    # Process any netID's 
    timesheet_df['actualID'] = timesheet_df['enteredID']    # What if wrong ID?
    mask = timesheet_df['actualID'].isin(mapSeries_netID_to_ID.index)
    timesheet_df.loc[mask, 'actualID'] = timesheet_df.loc[mask, 'actualID'].map(mapSeries_netID_to_ID)
    timesheet_df['existsID'] = timesheet_df['actualID'].isin(roster_df['ID'])
    
    # Now remove any rows where 'existsID' is False
    timesheet_df = timesheet_df[timesheet_df['existsID']]
    
    # Find assigned sections
    timesheet_df['sectionAssigned'] = timesheet_df['actualID'].astype('string').map(mapSeries_ID_to_section)
    
    # Calculate week
    timesheet_df['week'] = np.ceil((timesheet_df['Entry time'] - pd.to_datetime(FIRST_DATE, format = '%Y-%m-%d'))/timedelta(weeks = 1))
    
    # In wrong section
    timesheet_df['inWrongSection'] = timesheet_df['sectionAttended'] != timesheet_df['sectionAssigned']
        
    cols_to_drop = ['existsID']
    timesheet_df.drop(columns = cols_to_drop, inplace = True) 
    
    timesheet_df.rename(columns = {'actualID': 'ID'}, inplace = True)
    timesheet_df['studentName'] = timesheet_df['ID'].astype('string').map(mapSeries_ID_to_name)    

    # Reorder columns
    first_5_cols = ['studentName', 'TA', 'sectionAttended','inWrongSection']
    all_cols = timesheet_df.columns.to_list()
    rem_cols = [col for col in all_cols if col not in first_5_cols]
    new_col_order = first_5_cols + rem_cols
    timesheet_df = timesheet_df[new_col_order]
    
    return timesheet_df

def produce_weekly_summary(timesheet_df):
    wkSummary_df = timesheet_df.groupby(['studentName', 'week']).agg(
                                            In = ('Entry time', 'min'),
                                            Out = ('Entry time', 'max'),
                                            SectionAttended = ('sectionAttended', 'first'),
                                            InWrongSection = ('inWrongSection', 'first'),
                                            TA = ('TA', 'first')
                                            )
    wkSummary_df['duration'] = wkSummary_df['Out'] - wkSummary_df['In']
    
    # Calculate minutes late and tardiness from entry in section 
    maskAM = wkSummary_df['SectionAttended'].astype(str).str.split().str[1].fillna('') == 'AM'
    maskPM = wkSummary_df['SectionAttended'].astype(str).str.split().str[1].fillna('') == 'PM'
    wkSummary_df.loc[maskAM, 'tardyTime'] = wkSummary_df['In'] - wkSummary_df['In'].dt.normalize() - timedelta(hours = 8)
    wkSummary_df.loc[maskPM, 'tardyTime'] = wkSummary_df['In'] - wkSummary_df['In'].dt.normalize() - timedelta(hours = 13, minutes = 25)
    wkSummary_df['tardyTime'] = (wkSummary_df['tardyTime'].dt.total_seconds()/60.0).clip(lower = 0)
    wkSummary_df['tardy'] = wkSummary_df['tardyTime'] > LATE_MINUTES
    
    conditions = [
        (wkSummary_df['In'].notnull() == True) & (wkSummary_df['tardy'] == False),
        (wkSummary_df['In'].notnull() == True) & (wkSummary_df['tardy'] == True),
        (wkSummary_df['In'].notnull() == False)]
    values = ['P', 'T', 'A']
    wkSummary_df['Attendance'] = np.select(conditions, values, default = 'Unknown')
    
    summary_df = wkSummary_df.unstack()
    
    shortSummary_df = summary_df
    cols_to_remove = ['In', 'Out', 'tardy']
    shortSummary_df = shortSummary_df.drop(columns = cols_to_remove)
    new_order = ['Attendance', 'tardyTime', 'SectionAttended', 'TA', 'InWrongSection' , 'duration']
    shortSummary_df = shortSummary_df[new_order]
    
    return summary_df, shortSummary_df

st.markdown("# Attendance Report")    
timesheet_df = read_timesheet()
summary_df, shortSummary_df = produce_weekly_summary(timesheet_df)
shortSummary_df

attendance_cols = shortSummary_df.columns[shortSummary_df.columns.map(lambda x: x[0]) == 'Attendance']
absences = shortSummary_df[attendance_cols].copy()

absences.columns = absences.columns.droplevel(0)

absences['totAbsences'] = absences.isnull().sum(axis=1)

mask = absences['totAbsences'] > 1
selectedRows = absences[absences['totAbsences'] > 1]

st.markdown("## Multiple Absences (A > 1)")    
st.dataframe(selectedRows)

tardyTime_cols = shortSummary_df.columns[shortSummary_df.columns.map(lambda x: x[0]) == 'tardyTime']
tardies = shortSummary_df[tardyTime_cols].copy()

tardies.columns = tardies.columns.droplevel(0)

mask = tardies > LATE_MINUTES
tardies['totalTardies'] = mask.sum(axis=1)

selectedTardyRows = tardies[tardies['totalTardies'] > 1]

st.markdown("## Multiple Tardiness (T > 1)")
st.dataframe(selectedTardyRows)

st.markdown("## Processed Raw Data")
st.dataframe(timesheet_df)

  

