import glob
import pandas as pd
import warnings
from bullet import Bullet       # pip install bullet

# This script reads in 3 csv's:
#                   Canvas gradebook
#                   Canvas Late Report, generated from Late Assignments in Course Analytics
#                   Gradescope gradebook
# The script assumes that:
#       – The names of the pre- and post-lab assignments in Gradebook start with the same word as in canvas
#       – That word is unique to the lab
#       – The pre- and post-lab assignments have "pre-lab" and "post-lab" in the assignment names
# The script gives a 10 min grace period as per Cynthia
# The script use the late penalty rubric in place for Fall 2025
#
# Note that the bizarre 2nd and 3rd rows of the Canvas gradebook.csv are not really necessary,
#   so the allGrades.csv file can be used as is.
#
#   Usage:
#    (canvas) ~/Desktop $ python /Users/mah/Programming/CanvasMAH/Scripts/CombinePreandPostLabs.py 

def main():
    
    # Silences warning from pandas about having 'EX' entries
    warnings.simplefilter(action='ignore', category=FutureWarning)
    
    # Get roster from main file
    files = glob.glob("*.csv") 
    cli = Bullet("Choose Gradescope file", files, margin=3)
    gradescopeFile = cli.launch()
    cli = Bullet("Choose Canvas file", files, margin=3)
    canvasFile = cli.launch()
    cli = Bullet("Choose Canvas Late file", files, margin=3)
    canvasLateFile = cli.launch()
     
    # Save this for debugging
    # gradescopeFile = '/Users/mah/Desktop/gradescope.csv'
    # canvasFile = '/Users/mah/Desktop/canvas.csv'
    # canvasLateFile = '/Users/mah/Desktop/canvasLate.csv'
    
    # Read in the required columns of canvas csv plus any that include 'lab'
    columns = ["Student", "ID", "SIS User ID", "SIS Login ID", "Section"]
    good_sub_strings = ['lab']
    usecols = lambda x: (x in columns) or ((any(s in x.lower() for s in good_sub_strings)))
    canvas = pd.read_csv(canvasFile,
                         skiprows=[1,2],
                         usecols = usecols
                         )
    canvas = canvas[~canvas['Student'].str.contains('Student, Test', na=False)]
    
    # Read in the required columns of the canvasLate file
    columns = ['Student Name', 'Student ID', 'Assignment Name', 'Due Date', 'Submitted Date']
    usecols = lambda x: (x in columns)
    canvasLate = pd.read_csv(canvasLateFile,
                             usecols = usecols
                             )
    canvasLate.rename(columns={'Student ID': 'ID'}, inplace=True)
    canvasLate.rename(columns={'Assignment Name': 'Assignment_Name'}, inplace=True)
    
    # We have a problem in that pandas does not like EDT. Try replacing EDT/EST with UTC offset
    columns = ['Due Date', 'Submitted Date']
    for col in columns:
        canvasLate[col] = canvasLate[col].str.replace('EDT', '-0400')
        canvasLate[col] = canvasLate[col].str.replace('EST', '-0500')
        canvasLate[col] = pd.to_datetime(canvasLate[col], format='%b %d, %Y at %-I:%M:%S %p %z')

    # Calculate lateness in hours, then assign penalty. Give 10 min grace period as per Cynthia.
    # This assumes that all late reports get 15% off even if they are over 72 hrs late
    canvasLate['Lateness'] = (canvasLate['Submitted Date'] - canvasLate['Due Date'])/pd.Timedelta(hours = 1)
    canvasLate['Penalty'] = 0
    canvasLate.loc[(canvasLate['Lateness'] > 0.17) & (canvasLate['Lateness'] < 72.17), 'Penalty'] = -15
    canvasLate.loc[(canvasLate['Lateness'] >= 72.17), 'Penalty'] = -15 # -100
    
    # For debugging
    # canvasLate.to_csv('/Users/mah/Desktop/lateProcessed.csv', index=False)
    canvasLate = canvasLate.drop(columns=['Student Name'])
    
    # The Gradescope csv's have a bunch of columns that are not useful to us. We avoid loading that
    #   info using the info in sub_strings and usecols
    # sub_strings = ['Submission', 'Max', 'Lateness','First Name', 'Last Name', 'section_name']
    bad_sub_strings = ['Submission', 'Max', 'Lateness']
    good_sub_strings = ['post-lab', 'pre-lab']
    columns = ["SID"]
    usecols = lambda x: (x in columns) or ((any(s in x.lower() for s in good_sub_strings)) and (not any(s in x for s in bad_sub_strings)))

    gradescope = pd.read_csv(gradescopeFile,
                             usecols = usecols
                             )
    gradescope.rename(columns={'SID': 'SIS User ID'}, inplace=True)
    
    # Missing grades are replaced by 0
    gradescope = gradescope.fillna(0)
    
    # Make lists of the lab columns
    canvas_list = canvas.columns.tolist()
    gradescope_list = gradescope.columns.tolist()
    filtered_canvas_list = [item for item in canvas_list if 'lab' in item.lower()]
    filtered_gradescope_list = [item for item in gradescope_list if 'lab' in item.lower()]
    filtered_gradescope_list.sort()     # Makes debugging easier; not necessary
    
    # Merge the gradescope and canvas dataframes
    merged = pd.merge(canvas, gradescope, on='SIS User ID', how='left')
    
    # Make a list to reorder columns
    columnOrder = ["Student", "ID", "SIS User ID", "SIS Login ID", "Section"]
    columnsToBeDropped = []
    for entry in filtered_canvas_list:  
        columnOrder.append(entry)
        first_word = entry.split()[0]   # Assume the labs start with the same first word
        
        gs_entries = [item for item in filtered_gradescope_list if first_word in item]
        columnOrder.extend(sorted(gs_entries))
        columnsToBeDropped.extend(gs_entries)
        
        # Make a column for penalties
        newColumnName = first_word + '_penalty'
        merged[newColumnName] = 0.0
        columnOrder.append(newColumnName)
        columnsToBeDropped.append(newColumnName)
        
        # Make a column for testing
        newColumnName = first_word + '_testing'
        merged[newColumnName] = 0.0
        columnOrder.append(newColumnName)
        columnsToBeDropped.append(newColumnName)        

    merged = merged.reindex(columns = columnOrder)
    
    # Now we need to transfer late lab penalties into merged
    for row in canvasLate.itertuples():
        if row.Penalty < 0:
            labForPenalty = row.Assignment_Name.split()[0] + '_penalty'
            merged.loc[merged['ID'] == row.ID, labForPenalty] = 0.01 * row.Penalty * 90
    
    # Here is the actual calculation
    for entry in filtered_canvas_list:  
        first_word = entry.split()[0]   # Assume the labs start with the same first word
        
        gs_entries = [item for item in filtered_gradescope_list if first_word in item]
        pre_lab = [item for item in gs_entries if 'pre-lab' in item.lower()]
        post_lab = [item for item in gs_entries if 'pre-lab' not in item.lower()]
        penaltyColumnName = first_word + '_penalty'
        testingColumnName = first_word + '_testing'
        
        merged[testingColumnName] = merged[pre_lab[0]] + merged[post_lab[0]] + merged[penaltyColumnName]
        merged[testingColumnName] = merged[testingColumnName].clip(lower=0)     # No negative grades
        
        
    # For debugging
    # merged.to_csv('/Users/mah/Desktop/debugging.csv', index=False)

    # Copy the calculation into the output column
    for entry in filtered_canvas_list:  
        first_word = entry.split()[0]   # Assume the labs start with the same first word
        testingColumnName = first_word + '_testing'
        merged.loc[merged[entry] != 'EX', entry] = merged[testingColumnName]
        merged[entry] = merged[testingColumnName]
         
    # Remove all of the unnecessary columns
    merged.drop(columns = columnsToBeDropped, inplace = True)
    
    merged.to_csv('/Users/mah/Desktop/LabGrades.csv', index=False)
                             

if __name__ == '__main__':


    main()

