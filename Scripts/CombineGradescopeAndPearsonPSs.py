import os
import glob
import math
import pandas as pd
import warnings
from bullet import Bullet       # pip install bullet
from bullet import Numbers

# This script reads in 3 csv's: one each from Canvas, Gradescope, and Pearson. The script
#   combines all PS-related columns (identified by names starting with 'PS ') into a single
#   dataframe, then calculates a final score based on 30% of Gradescope score and 70% of
#   Pearson score (normalized to 100). This calculation is placed in the Canvas column
#   UNLESS there is an 'EX' entry (which is preserved). The script cleans up the excess columns
#   and outputs allGrades.csv that is almost ready for upload to Canvas.
#
# Note that the bizarre 2nd and 3rd rows of the Canvas gradebook.csv are not really necessary,
#   so the allGrades.csv file can be used as is.
#
#   Usage:
#    (canvas) ~/Desktop $ python /Users/mah/Programming/CanvasMAH/Scripts/CombineGradescopeAndPearsonPSs.py 

# Currently unused
def setColumnOrder(allHeaders):
    firstHeaders = ['Last_Name', 'First_Name', 'SID']
    otherHeaders = list(set(allHeaders) - set(firstHeaders))
    otherHeaders.sort()
    newHeaders = firstHeaders + otherHeaders
    return newHeaders

def main():
    
    # Silences warning from pandas about having 'EX' entries
    warnings.simplefilter(action='ignore', category=FutureWarning)
    
    # Get roster from main file
    files = glob.glob("*.csv") 
    cli = Bullet("Choose Gradescope file", files, margin=3)
    gradescopeFile = cli.launch()
    cli = Bullet("Choose Pearson file", files, margin=3)
    pearsonFile = cli.launch()
    cli = Bullet("Choose Canvas file", files, margin=3)
    canvasFile = cli.launch()
    cli = Numbers("What is the last PS to process? ", type = int)
    maxPS = cli.launch()
    
    # Save this for debugging
    # maxPS = 7
    # gradescopeFile = '/Users/mah/Desktop/gradescope.csv'
    # pearsonFile = '/Users/mah/Desktop/pearson.csv' 
    # canvasFile = '/Users/mah/Desktop/canvas.csv'
    
    # Read in the required columns of canvas csv plus any that start with 'PS '
    columns = ["Student", "ID", "SIS User ID", "SIS Login ID", "Section"]
    usecols = lambda x: (x in columns) or (x.startswith('PS '))
    canvas = pd.read_csv(gradescopeFile,
                         usecols = usecols
                         )
    canvas = pd.read_csv(canvasFile,
                         skiprows=[1,2],
                         usecols = usecols
                         )
    canvas = canvas[~canvas['Student'].str.contains('Student, Test', na=False)]
     
    # The Gradescope csv's have a bunch of columns that are not useful to us. We avoid loading that
    #   info using the info in sub_strings and usecols
    # sub_strings = ['Submission', 'Max', 'Lateness','First Name', 'Last Name', 'section_name']
    sub_strings = ['Submission', 'Max', 'Lateness']
    columns = ["SID"]
    usecols = lambda x: (x in columns) or ((x.startswith('PS')) and (not any(s in x for s in sub_strings)))

    gradescope = pd.read_csv(gradescopeFile,
                             usecols = usecols
                             )
    gradescope.rename(columns={'SID': 'SIS User ID'}, inplace=True)
    
    # Now work on Pearson gradebook
    columns = ["Student ID"]
    usecols = lambda x: (x in columns) or (x.startswith('PS'))
 
    pearson = pd.read_csv(pearsonFile,
                          skiprows=3,
                          usecols = usecols
                          )

    pearson.rename(columns={'Student ID': 'SIS User ID'}, inplace=True)

    # Now we need to propagate the 'EX' entries in Canvas to Gradescope and Pearson
    for i in range(1, maxPS + 1):  # Assume there are no more than 13 PSs
        colStart = 'PS ' + str(i)
        canvasCol = canvas[[col for col in canvas.columns if col.startswith(colStart)]]
        if canvasCol.shape[1] > 0:   # Found a Canvas column
            # Get the name of the column in Canvas
            canvasColName = canvasCol.columns[0]
            IDs_canvas = canvas.loc[canvas[canvasColName] == 'EX', 'SIS User ID'].tolist()
            
            # Process the gradescope data
            gsCol = gradescope[[col for col in gradescope.columns if col.startswith(colStart)]]
            if gsCol.shape[1] > 0:   # Found a corresponding Gradescope column
                gsColName = gsCol.columns[0]
            else:                    # Otherwise, make a new blank column
                gsColName = colStart
                gradescope[gsColName] = 0
                
            newGsName = 'gsPS ' + str(i)
            gradescope.rename(columns={gsColName: newGsName}, inplace=True)
                
            # Process the Pearson data
            psCol = pearson[[col for col in pearson.columns if col.startswith(colStart)]]
            if psCol.shape[1] > 0:   # Found a corresponding Gradescope column
                psColName = psCol.columns[0]
            else:
                psColName = colStart + ' Mastering'
                pearson[psColName] = 0
            
            newPsName = 'psPS ' + str(i)
            pearson.rename(columns={psColName: newPsName}, inplace=True)            
                
    merged = pd.merge(canvas, gradescope, on='SIS User ID', how='left')
    allGrades = pd.merge(merged, pearson, on='SIS User ID', how='left')
    
    for i in range(1, maxPS + 1): 
        colStart = 'PS ' + str(i)
        canvasCol = canvas[[col for col in canvas.columns if col.startswith(colStart)]]
        if canvasCol.shape[1] > 0:   # Found a Canvas column
            canvasColName = canvasCol.columns[0]
            IDs_canvas = canvas.loc[canvas[canvasColName] == 'EX', 'SIS User ID'].tolist()
            
            gsColName = 'gsPS ' + str(i)
            psColName = 'psPS ' + str(i)
            
            # Convert all missing values to 0
            allGrades[gsColName] = pd.to_numeric(allGrades[gsColName], errors='coerce').fillna(0)
            allGrades[psColName] = pd.to_numeric(allGrades[psColName], errors='coerce').fillna(0)
            
            gsMax = pd.to_numeric(allGrades[gsColName], errors='coerce').max()
            gsMax = 0 if math.isnan(gsMax) else gsMax
            gsMax = 100.0 if gsMax > 100.0 else gsMax    # Take care of extra credit
            psMax = pd.to_numeric(allGrades[psColName], errors='coerce').max()
            psMax = 0 if math.isnan(psMax) else psMax
            
            gsScale = 0.0
            psScale = 0.0
            if gsMax > 0:
                if(psMax > 0):
                    gsScale = 30.0/gsMax
                    psScale = 70.0/psMax
                else:
                    gsScale = 100.0/gsMax
                
            elif psMax > 0:
                psScale = 100.0/psMax
                
            allGrades[canvasColName] = (gsScale * allGrades[gsColName] + psScale * allGrades[psColName]).round(1)
            
            for ID in IDs_canvas:
                allGrades.loc[allGrades['SIS User ID'] == ID, canvasColName] = 'EX'
            
    # drop unneded columns. 
    for i in range(1, maxPS + 1):
        gsColName = 'gsPS ' + str(i)
        psColName = 'psPS ' + str(i)
        allGrades.drop(columns=[gsColName, psColName], inplace = True)
        
    for i in range(maxPS + 1, 14):  # Assumes no more that 14 PSs
        colStart = 'PS ' + str(i)
        xsCols = allGrades[[col for col in allGrades.columns if col.startswith(colStart)]]
        allGrades = allGrades.drop(columns = xsCols)

    
    allGrades = allGrades.round(1)
    allGrades.to_csv('allGrades.csv', index=False)

if __name__ == '__main__':


    main()

