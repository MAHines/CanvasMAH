import glob
import pandas as pd
import warnings
from bullet import Bullet       # pip install bullet

# This script reads in 2 csv's:
#                   Canvas gradebook
#                   Gradescope gradebook for pre-semester math test
# The script fills in two Canvas assignments that contain 'pre-test' in their name:
#       – A column with 'credit' in its name gets either a 10 or 0 depending on the existence of the pre-test
#       – A column with 'math' in its name gets the actual pre-test score
#       – The pre- and post-lab assignments have "pre-lab" and "post-lab" in the assignment names
# The script outputs a csv called 'PreTestGrades.csv' that is ready for Canvas upload
#
#   Usage:
#    (canvas) ~/Desktop $ python /Users/mah/Programming/CanvasMAH/Scripts/TransferExtraCredit.py 

def main():
    
    # Silences warning from pandas about having 'EX' entries
    warnings.simplefilter(action='ignore', category=FutureWarning)
    
    # Get roster from main file
    files = glob.glob("*.csv") 
    cli = Bullet("Choose Gradescope file", files, margin=3)
    gradescopeFile = cli.launch()
    cli = Bullet("Choose Canvas file", files, margin=3)
    canvasFile = cli.launch()
     
    # Save this for debugging
    # gradescopeFile = '/Users/mah/Desktop/MathPreTest.csv'
    # canvasFile = '/Users/mah/Desktop/canvas.csv'
    
    # Read in the required columns of canvas csv plus any that include 'lab'
    columns = ["Student", "ID", "SIS User ID", "SIS Login ID", "Section"]
    good_sub_strings = ['pre-test']
    usecols = lambda x: (x in columns) or ((any(s in x.lower() for s in good_sub_strings)))
    canvas = pd.read_csv(canvasFile,
                         skiprows=[1,2],
                         usecols = usecols
                         )
    canvas = canvas[~canvas['Student'].str.contains('Student, Test', na=False)]
        
    # The Gradescope csv's have a bunch of columns that are not useful to us. We avoid loading that
    #   info using the info in sub_strings and usecols
    # sub_strings = ['Submission', 'Max', 'Lateness','First Name', 'Last Name', 'section_name']
    bad_sub_strings = ['Submission', 'Max', 'Lateness']
    good_sub_strings = ['pre-semester']
    columns = ["SID"]
    usecols = lambda x: (x in columns) or ((any(s in x.lower() for s in good_sub_strings)) and (not any(s in x for s in bad_sub_strings)))

    gradescope = pd.read_csv(gradescopeFile,
                             usecols = usecols
                             )
    gradescope.rename(columns={'SID': 'SIS User ID'}, inplace=True)
    
    # Missing grades are replaced by 0
    # gradescope = gradescope.fillna(0)
    
    # Make lists of the pre-test columns
    canvas_list = canvas.columns.tolist()
    gradescope_list = gradescope.columns.tolist()
    filtered_canvas_list = [item for item in canvas_list if 'pre-test' in item.lower()]
    filtered_gradescope_list = [item for item in gradescope_list if 'math test' in item.lower()]
    filtered_gradescope_list.sort()     # Makes debugging easier; not necessary
    
    # Merge the gradescope and canvas dataframes
    merged = pd.merge(canvas, gradescope, on='SIS User ID', how='left')
    
    # Here is the actual calculation
    for entry in filtered_canvas_list:
        if 'Credit' in entry:
            merged[entry] = 0
            merged.loc[merged[filtered_gradescope_list[0]].notna(), entry] = 10
        else:
            merged[entry] = merged[filtered_gradescope_list[0]]        
         
    # Remove all of the unnecessary columns
    merged.drop(columns = filtered_gradescope_list[0], inplace = True)
    
    merged.to_csv('/Users/mah/Desktop/PreTestGrades.csv', index=False)
                             

if __name__ == '__main__':


    main()

