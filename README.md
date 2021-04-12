# CanvasMAH – Scripts for working with Canvas and Gradescope

This is a work in progress.

### mahCanvas.py
Class for accessing Canvas using the CanvasAPI from UCFopen

### WatermarkReports.py
Usage: python WatermarkReports gradebook.csv submissionsFolder

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
