import os
import glob
import pandas as pd

def main():
    
    # os.chdir('/Users/mah/Downloads/CHEM2070_Determination_of_Chemical_Formulae_Post-lab_Report')
    # os.chdir('/Users/mah/Downloads/CHEM2070_Recycling_Aluminum_Post-Lab_Report')
    # os.chdir('/Users/mah/Downloads/CHEM2070_Iron_Complex_Salt_Post-Lab_Report')
    
    os.chdir('/Users/mah/Downloads/CHEM2070_Unknown_Acid_Molar_Mass_Post-lab_Report')
    files = glob.glob("*.csv") 
    
    columns = ["SID", "Score", "Grader"]
    usecols = lambda x: (x in columns)
    merged = None
    for index, file in enumerate(files):
    
        print(file)
        canvas = pd.read_csv(file,
                             usecols = usecols,
                             skipfooter=4,
                             engine='python'
                             )
        newCol = 'Score' + str(index)
        canvas.rename(columns={'Score': newCol}, inplace=True)
        newCol = 'Grader' + str(index)
        canvas.rename(columns={'Grader': newCol}, inplace=True)
        
        if merged is not None:
            merged = pd.merge(merged, canvas, on='SID', how='left')
        else:
            merged = canvas
   
    merged.to_csv('newAllGrades.csv', index=False)

if __name__ == '__main__':


    main()

