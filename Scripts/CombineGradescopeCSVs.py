import os
import glob
import pandas as pd
from bullet import Bullet       # pip install bullet

# This script reads in all of the Gradescope data from all of the csv's in the cwd except 'allGrades.csv,'
#   then combines these data into a single csv containing all of the grades, 'allGrades.csv' The script 
#   also calculates a total grade for each experiment that has a graded report.

def setColumnOrder(allHeaders):
    firstHeaders = ['Last_Name', 'First_Name', 'SID']
    otherHeaders = list(set(allHeaders) - set(firstHeaders))
    otherHeaders.sort()
    newHeaders = firstHeaders + otherHeaders
    return newHeaders

def main():
    
    cwd = os.getcwd()

    # Get roster from main file
    files = glob.glob("*.csv") 
    cli = Bullet("Choose main file", files, margin=3)
    rosterFile = cli.launch()
     
    # The main file is used to read first name, last name, and SID. All files are indexed by
    #   Email, as this is the only info that is constant across our Gradescope courses.
    roster = pd.read_csv(
        os.path.join(os.getcwd(), rosterFile),
        converters={"Email": str.lower},
        usecols=["First Name", "Last Name", "SID", "Email"],
        index_col="Email",
    )

    all_files = glob.glob(os.path.join(cwd, "*.csv")) 
    oldOutput = glob.glob(os.path.join(cwd, "allGrades.csv"))
    if oldOutput in all_files:
        all_files.remove(oldOutput)

    # The Gradescope csv's have a bunch of columns that are not useful to us. We avoid loading that
    #   info using the info in sub_strings and usecols
    sub_strings = ['Submission', 'Max', 'Lateness','First Name', 'Last Name', 'SID', 'section_name']
    usecols = lambda x: not any(s in x for s in sub_strings)

    for filename in all_files:
        newDf = pd.read_csv(filename,
                            converters={"Email": str.lower},
                            usecols = usecols,
                            index_col='Email'
                            )
        roster = roster.combine_first(newDf)
    
    # Clean up the column names, replacing spaces with _ and removing :
    roster.columns = roster.columns.str.replace(' ', '_')
    roster.columns = roster.columns.str.replace(':', '')

    # Loop through the experiments. If all 3 pieces of the expt have Gradescope records, combine them
    #   In doing this, skip any students w/o a report grade, but consider missing prelabs/notebooks as 0
    #   The script assumes the exp parts have names 'ExpN: blahblah_Notebook', 'ExpN: blahblah_Prelab',
    #   and 'ExpN: blahblah_Report' where N is an integer. 
    roster = roster[setColumnOrder(list(roster.columns))]    # Set column order
    allHeaders = list(roster.columns)
    for i in range(1, 9):  # There are only 7 labs, but this might be used elsewhere   
        expPrefix = 'Exp' + str(i)
        expParts = [x for x in allHeaders if x.startswith(expPrefix)]
        if len(expParts) > 2:
            expTotal = expParts[0].replace('_Notebook','') + '_Total'
            roster[expTotal] = roster[expParts[0]].fillna(0) + roster[expParts[1]].fillna(0) + roster[expParts[2]]
    
    # Reorder the columns one more time because of the new lab totals.
    roster = roster[setColumnOrder(list(roster.columns))]    # Set column order
     
    roster.to_csv("allGrades.csv", index=True)

if __name__ == '__main__':
    main()

