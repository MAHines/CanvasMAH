# CanvasMAH – Scripts for working with Canvas, Gradescope, and Pearson's Mastering Chemistry

This is a work in progress.

### analyzeGradescopeFolder.py

Usage: streamlit run analyzeGradescopeFolder.py

Streamlit package that is designed  to analyze grading in a folder of Gradescope
scores for an assignment. To get the folder, open the assignment in Gradescope and select
"Export Evaluations" at the bottom of the page.

Drag the folder onto "Drag and drop files here." Give the analysis a name in the modal dialog.
An analysis of all problems will appear. To analyze a single problem, use the dropdown menu
in the sidebar to select it.

### combineGradescopeAndPearsonPSs.py

Usage: python CombineGradescopeAndPearsonPSs.py 

This script reads in 3 csv's: one each from Canvas, Gradescope, and Pearson. The script
combines all PS-related columns (identified by names starting with 'PS ' in Gradescope
and 'PS Mastering ' from Pearson) into a single
dataframe, then calculates a final score based on 30% of Gradescope score and 70% of
Pearson score (normalized to 100). This calculation is placed in the Canvas column
UNLESS there is an 'EX' entry (which is preserved). The script cleans up the excess columns
and outputs allGrades.csv that is almost ready for upload to Canvas.

Note that the bizarre 2nd and 3rd rows of the Canvas gradebook.csv are not really necessary,
so the allGrades.csv file can be used as is.

### combinePreAndPostLabs.py

Usage: python combinePreAndPostLabs.py 

This script reads in 3 csv's:
                   Canvas gradebook
                   Canvas Late Report, generated from Late Assignments in Course Analytics
                   Gradescope gradebook
 The script assumes that:
       – The names of the pre- and post-lab assignments in Gradebook start with the same word as in canvas
       – That word is unique to the lab
       – The pre- and post-lab assignments have "pre-lab" and "post-lab" in the assignment names
The script gives a 10 min grace period as per Cynthia
The script use the late penalty rubric in place for Fall 2025

Note that the bizarre 2nd and 3rd rows of the Canvas gradebook.csv are not really necessary,
  so the allGrades.csv file can be used as is.

### transferExtraCredit.py

Usage: python transferExtraCredit.py 

This script reads in 2 csv's:
                  Canvas gradebook
                  Gradescope gradebook for pre-semester math test
The script fills in two Canvas assignments that contain 'pre-test' in their name:
      – A column with 'credit' in its name gets either a 10 or 0 depending on the existence of the pre-test
      – A column with 'math' in its name gets the actual pre-test score
      – The pre- and post-lab assignments have "pre-lab" and "post-lab" in the assignment names
The script outputs a csv called 'PreTestGrades.csv' that is ready for Canvas upload

### mahCanvas.py
Class for accessing Canvas using the CanvasAPI from UCFopen

### WatermarkReports.py
Usage: python WatermarkReports gradebook.csv submissionsFolder

This script has been superseded by CMToolkit

This script prepares lab report submissions downloaded from Canvas for Gradescope upload.
  – Converts any .docx files to .pdf
  – Finds the length of the longest pdf
  – Gets student ID from Canvas filename, matches to student name in gradebook, and adds student name at top of first page
  – Adds vertical page numbers to both sides of each page to help Gradescope auto-assign pages.
  – Adjusts all pdf's to the same number of pages to help Gradescope auto-assign pages.
  – Produces file Outline.pdf which is used for preparing assignment in Gradescope

  This script requires the file 'Watermark.pdf' to be in the working directory. This file consists
    of a _scanned_ set of pages with numbers running down the right and left hand sides. It is
    important that this be a _scanned_ file for Gradescope matching. A pdf file with text does not work.
    I tried just having the numbers run down only the right hand side, but Gradescope would not auto-recognize
    this type of watermarking.

  This script assumes that the files to be processed are in the directory passed as the argument
    submissionsFolder. The script will only handle .docx and .pdf files. Any other files will
    be deleted with no warning.

  Some pdf files do not watermark properly. These files appear to have an opaque white background behind
    the text. A scanned file would probably not watermark correctly either.

### CombineGradescopeCSVs.py
Usage: python CombineGradescopeCSVs.py

This script reads in all of the Gradescope data from all of the csv's in the cwd except 'allGrades.csv,'
  then combines these data into a single csv containing all of the grades, 'allGrades.csv' The script 
  also calculates a total grade for each experiment that has a graded report. The processing is done in pandas.
