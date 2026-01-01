import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def CUID_from_netID(roster_df, netID):
    return roster_df.loc[roster_df['netID'] == netID, 'ID'].iloc[0]
    
def netID_from_CUID(roster_df, CUID):
    return roster_df.loc[roster_df['ID'] == CUID, 'netID'].iloc[0]
    
FIRST_DATE = '2026-02-02'
    
def main():

    studentFile = '/Users/mah/Desktop/fakeStudentData.csv'
    rosterFile = 'processedCanvasRoster.csv'
    
    columns = ["Student", "ID", "SIS Login ID"]    
    usecols = lambda x: (x in columns)
    rawData_df = pd.read_csv(studentFile,
                         usecols = usecols
                         )
                         
    # Read in the roster
    roster_df = pd.read_csv(rosterFile)
    
    # Convert the IDs to strings
    rawData_df['ID'] = rawData_df['ID'].astype(str)
    roster_df['ID'] = roster_df['ID'].astype(str)
    
    # Convert the roster into a mapping series for ID -> section
    mapSeries_ID_to_section = roster_df.set_index('ID')['section']
    
    rawData_df['labDay'] = rawData_df['ID'].map(mapSeries_ID_to_section).str.split().str[0]
    rawData_df['labTime'] = rawData_df['ID'].map(mapSeries_ID_to_section).str.split().str[1]
    
    offsetDay = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4}
    labTA = {'Mon': 'Cindy', 'Tue': 'Ann', 'Wed': 'Bob', 'Thu': 'Charlie', 'Fri': 'Donna'}
    offsetHour ={'AM': 0, 'PM': 5.417}
    
    # Fill TA data
    rawData_df['TA'] = rawData_df['labDay'].map(labTA)
   
    # Fix column name
    rawData_df = rawData_df.rename(columns = {'SIS Login ID': 'netID'})    
    
    # Make a column of random numbers
    rawData_df['random_col'] = np.random.rand(len(rawData_df))
    
    # First day = Feb 2, 2026
    first_datetime = datetime.strptime(FIRST_DATE, "%Y-%m-%d") + pd.to_timedelta(8, unit = 'h')
    
    # Fill the first 4 weeks perfectly
    rawData_df['days2add'] = rawData_df['labDay'].map(offsetDay)
    rawData_df['time2add'] = rawData_df['labTime'].map(offsetHour)
    rawData_df['wk1'] = first_datetime + pd.to_timedelta(rawData_df['days2add'], unit='d') + pd.to_timedelta(rawData_df['time2add'], unit = 'h')
    rawData_df['wk2'] = rawData_df['wk1'] + pd.to_timedelta(7, unit='d')
    rawData_df['wk3'] = rawData_df['wk2'] + pd.to_timedelta(7, unit='d')
    rawData_df['wk4'] = rawData_df['wk3'] + pd.to_timedelta(7, unit='d')
    
    # Make 50 random students attend Fri each week
    num = 50
    random_indices = np.random.choice(rawData_df.index, size=num, replace=False)
    rawData_df.loc[random_indices, 'wk1'] = first_datetime + pd.to_timedelta(4, unit='d') + pd.to_timedelta(rawData_df['time2add'], unit = 'h')
    random_indices = np.random.choice(rawData_df.index, size=num, replace=False)
    rawData_df.loc[random_indices, 'wk2'] = first_datetime + pd.to_timedelta(11, unit='d') + pd.to_timedelta(rawData_df['time2add'], unit = 'h')
    random_indices = np.random.choice(rawData_df.index, size=num, replace=False)
    rawData_df.loc[random_indices, 'wk3'] = first_datetime + pd.to_timedelta(18, unit='d') + pd.to_timedelta(rawData_df['time2add'], unit = 'h')
    random_indices = np.random.choice(rawData_df.index, size=num, replace=False)
    rawData_df.loc[random_indices, 'wk4'] = first_datetime + pd.to_timedelta(25, unit='d') + pd.to_timedelta(rawData_df['time2add'], unit = 'h')
    
    # Add a small jitter to the arrival times 
    rawData_df['jitter'] = 8 * np.random.rand(len(rawData_df)) - 5
    rawData_df['wk1'] += pd.to_timedelta(rawData_df['jitter'], unit = 'm')
    rawData_df['jitter'] = 8 * np.random.rand(len(rawData_df)) - 5
    rawData_df['wk2'] += pd.to_timedelta(rawData_df['jitter'], unit = 'm')
    rawData_df['jitter'] = 8 * np.random.rand(len(rawData_df)) - 5
    rawData_df['wk2'] += pd.to_timedelta(rawData_df['jitter'], unit = 'm')
    rawData_df['jitter'] = 8 * np.random.rand(len(rawData_df)) - 5
    rawData_df['wk4'] += pd.to_timedelta(rawData_df['jitter'], unit = 'm')
    rawData_df.drop(columns = ['jitter'], inplace = True)
    
    # Make 50 random students 15 min late each week
    random_indices = np.random.choice(rawData_df.index, size=50, replace=False)
    rawData_df.loc[random_indices, 'wk1'] += pd.to_timedelta(15, unit='m')
    random_indices = np.random.choice(rawData_df.index, size=50, replace=False)
    rawData_df.loc[random_indices, 'wk2'] += pd.to_timedelta(15, unit='m')
    random_indices = np.random.choice(rawData_df.index, size=50, replace=False)
    rawData_df.loc[random_indices, 'wk3'] += pd.to_timedelta(15, unit='m')
    random_indices = np.random.choice(rawData_df.index, size=50, replace=False)
    rawData_df.loc[random_indices, 'wk4'] += pd.to_timedelta(15, unit='m')
    
    # Make 50 random students attend Fri each week
    random_indices = np.random.choice(rawData_df.index, size=50, replace=False)
    rawData_df.loc[random_indices, 'wk1'] = first_datetime + pd.to_timedelta(4, unit='d') + pd.to_timedelta(rawData_df['time2add'], unit = 'h')
    random_indices = np.random.choice(rawData_df.index, size=50, replace=False)
    rawData_df.loc[random_indices, 'wk2'] = first_datetime + pd.to_timedelta(11, unit='d') + pd.to_timedelta(rawData_df['time2add'], unit = 'h')
    random_indices = np.random.choice(rawData_df.index, size=50, replace=False)
    rawData_df.loc[random_indices, 'wk3'] = first_datetime + pd.to_timedelta(18, unit='d') + pd.to_timedelta(rawData_df['time2add'], unit = 'h')
    random_indices = np.random.choice(rawData_df.index, size=50, replace=False)
    rawData_df.loc[random_indices, 'wk4'] = first_datetime + pd.to_timedelta(25, unit='d') + pd.to_timedelta(rawData_df['time2add'], unit = 'h')
    
    # Make 20 random students absent each weak
    random_indices = np.random.choice(rawData_df.index, size=20, replace=False)
    rawData_df.loc[random_indices, 'wk1'] = np.nan
    random_indices = np.random.choice(rawData_df.index, size=20, replace=False)
    rawData_df.loc[random_indices, 'wk2'] = np.nan
    random_indices = np.random.choice(rawData_df.index, size=20, replace=False)
    rawData_df.loc[random_indices, 'wk3'] = np.nan
    random_indices = np.random.choice(rawData_df.index, size=20, replace=False)
    rawData_df.loc[random_indices, 'wk4'] = np.nan
    
    # Now make the a fake attendance sheet
    course = '2070'
    
    # Sort by wk1
    rawData_df = rawData_df.sort_values(by = 'wk1', ascending = True)

    columns_to_copy = ['TA', 'ID', 'netID', 'wk1']
    new_df = rawData_df[columns_to_copy].copy()
    new_df = new_df.rename(columns = {'wk1': 'Entry time'})
    new_df = new_df.dropna(subset = ['Entry time'])     # Remove non-entries
    
    # Sort by wk2
    rawData_df = rawData_df.sort_values(by = 'wk2', ascending = True)

    columns_to_copy = ['TA', 'ID', 'netID', 'wk2']
    new_df2 = rawData_df[columns_to_copy].copy()
    new_df2 = new_df2.rename(columns = {'wk2': 'Entry time'})
    new_df2 = new_df2.dropna(subset = ['Entry time'])     # Remove non-entries
    
    # Form combined df
    timesheet_df = pd.concat([new_df, new_df2])
    
    # Sort by wk3
    rawData_df = rawData_df.sort_values(by = 'wk3', ascending = True)

    columns_to_copy = ['TA', 'ID', 'netID', 'wk3']
    new_df3 = rawData_df[columns_to_copy].copy()
    new_df3 = new_df3.rename(columns = {'wk3': 'Entry time'})
    new_df3 = new_df3.dropna(subset = ['Entry time'])     # Remove non-entries
    
    # Form combined df
    timesheet_df = pd.concat([timesheet_df, new_df3])
    
    # Sort by wk4
    rawData_df = rawData_df.sort_values(by = 'wk4', ascending = True)

    columns_to_copy = ['TA', 'ID', 'netID', 'wk4']
    new_df4 = rawData_df[columns_to_copy].copy()
    new_df4 = new_df4.rename(columns = {'wk4': 'Entry time'})
    new_df4 = new_df4.dropna(subset = ['Entry time'])     # Remove non-entries
    
    # Form combined df
    timesheet_df = pd.concat([timesheet_df, new_df4])
    
    # Now we need to calculate the actual section they attended
    timesheet_df['section'] = timesheet_df['Entry time'].dt.strftime('%a') + ' ' + timesheet_df['Entry time'].dt.strftime('%p')
    
    # Replace 200 random CUIDs with netIDs
    random_indices = np.random.choice(timesheet_df.index, size=200, replace=False)
    timesheet_df.loc[random_indices, 'ID'] = timesheet_df.loc[random_indices, 'netID']
    
    # Remove column of netIDs
    timesheet_df.drop(columns = ['netID'], inplace = True)
    
    # Add course column
    timesheet_df['course'] = course
    column_order = ['course', 'TA', 'section', 'ID', 'Entry time']
    timesheet_df = timesheet_df[column_order]
    
    # Now make entries for student exit
    timesheetOut_df = timesheet_df.copy()
    avgTime = pd.to_timedelta(150, unit = 'm')
    #min_in_lab = pd.to_timedelta(30 * (np.random.rand(len(timesheetOut_df)) - 0.5), unit = 'm') + avgTime
    timesheetOut_df['Entry time'] = timesheetOut_df['Entry time'] + avgTime
    timesheet_df = pd.concat([timesheet_df, timesheetOut_df])
    timesheet_df = timesheet_df.sort_values(by = 'Entry time', ascending=True)
    
    # Convert to desired datetime format
    timesheet_df['Entry time'] = timesheet_df['Entry time'].dt.strftime("%a, %d %b %y, %I:%M %p")
    
    # Drop unneeded columns
    cols_to_drop = ['labDay', 'labTime', 'random_col', 'days2add', 'time2add', 'TA']
    rawData_df.drop(columns = cols_to_drop, inplace = True)
    cols_to_drop = ['course', 'section']
    timesheet_df.drop(columns = cols_to_drop, inplace = True)  

    rawData_df.to_csv('fakeAttendance.csv', index=False)
    timesheet_df.to_csv('fakeTimesheet.csv', index = False)
   
if __name__ == '__main__':

    main()

    
