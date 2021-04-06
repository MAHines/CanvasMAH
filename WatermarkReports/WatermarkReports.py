# Usage: python WatermarkReports gradebook.csv submissionsFolder

# This script prepares lab report submissions downloaded from Canvas for Gradescope upload.
#   – Converts any .docx files to .pdf
#   – Finds the length of the longest pdf
#   – Gets student ID from Canvas filename, matches to student name in gradebook, and adds student name at top of first page
#   – Adds vertical page numbers to both sides of each page to help Gradescope auto-assign pages.
#   – Adjusts all pdf's to the same number of pages to help Gradescope auto-assign pages.
#   – Produces file Outline.pdf which is used for preparing assignment in Gradescope
#
#   This script requires the file 'Watermark.pdf' to be in the working directory. This file consists
#     of a _scanned_ set of pages with numbers running down the right and left hand sides. It is
#     important that this be a _scanned_ file for Gradescope matching. A pdf file with text does not work.
#     I tried just having the numbers run down only the right hand side, but Gradescope would not auto-recognize
#     this type of watermarking.
#
#   This script assumes that the files to be processed are in the directory passed as the argument
#     submissionsFolder. The script will only handle .docx and .pdf files. Any other files will
#     be deleted with no warning.
#
#   Some pdf files do not watermark properly. These files appear to have an opaque white background behind
#     the text. A scanned file would probably not watermark correctly either.

from docx2pdf import convert
from PyPDF2 import PdfFileReader, PdfFileWriter, PdfFileMerger
from fpdf import FPDF
import os
import pandas as pd
import sys
import argparse

def main():
    
    # Read in the arguments and validate
    parser = argparse.ArgumentParser(description="Prepare a folder of downloads from Canvas for upload to Gradescope")
    parser.add_argument('gradesCSV', type = str, help = 'Path to gradebook in csv format')
    parser.add_argument('subFolder', type = str, help = 'Path to folder of Canvas submissions')
    args = parser.parse_args()
    gradesCSV = args.gradesCSV
    subFolder = args.subFolder

    if not os.path.isfile(gradesCSV):
        print(f'ERROR: The gradebook file {gradesCSV} does not exist.')
        exit()
    
    gradebookName, gradebookExtension = os.path.splitext(gradesCSV)
    if not gradebookExtension == '.csv':
        print(f'ERROR: The gradebook file {gradesCSV} should be a .csv file.')
        exit()
    
    if not os.path.isdir(subFolder):
        print(f'ERROR: {subFolder} is not a valid directory.')
        exit()

    if not os.path.isfile('Watermark.pdf'):
        print(f'ERROR: The file Watermark.pdf is not in the current directory.')
        exit()

    # Read in the info in the gradebook so we can get names from IDs. Should probably add error checking
    df = pd.read_csv(gradesCSV, usecols=[0,1], header=2)
    df.columns = ['Name', 'ID']

    # Comment out the next line if you don't want .docx --> .pdf
    convert(subFolder)
    
    # Open the Watermark file. This pdf file contains 30 pages with numbers running down both sides.
    wm_file = open('Watermark.pdf', 'rb')

    cwd = os.getcwd()
    os.chdir(subFolder)

    # Find the maximum number of pages across all files and delete non pdf
    maxPages = 0
    for fn in os.listdir():
        if not fn.endswith('.pdf'):
            os.remove(fn)
        else:
            with open(fn, "rb") as origReport_file:
                origReport_reader = PdfFileReader(origReport_file, strict = False)
                numPages = origReport_reader.getNumPages() 
                if numPages > maxPages:
                    maxPages = numPages

    # Now make the Outline.pdf, which consists of watermarked pages. We are going to have a problem
    #   with files that are longer than the watermark file. My solution is just not to watermark
    #   the excess pages. This may cause Gradescope to get confused, but I doubt it.
    wm_reader = PdfFileReader(wm_file)
    if maxPages >  wm_reader.getNumPages():
        maxPages = wm_reader.getNumPages()
    if maxPages > 24:   # For unknown reasons, Gradescope does not like more than 24 pages using this approach
        maxPages = 24
            
    print(f'All reports will be lengthened to {maxPages} pages.')

    os.chdir(cwd)
    with open('Outline.pdf', 'wb') as outline_file:
        outline_writer = PdfFileWriter()
        for i in range(maxPages):
            outline_writer.addPage(wm_reader.getPage(i))
        outline_writer.write(outline_file)
        outline_file.close()
    os.chdir(subFolder)

    # Loop through every file in the submissionsFolder directory, processing each
    for fn in os.listdir():
        if fn.endswith('.pdf'):
    
            # Find student ID from Canvas filename
            fnParts = fn.split('_')
            i = 0
            while not fnParts[i].isnumeric():
                i += 1
            studentID = int(fnParts[i])
    
            # Extract name from database
            if len(df.loc[df['ID']==studentID]) > 0:           
                nameParts = df.iloc[df.loc[df['ID']==studentID].index.values[0],0].split(',')
                fullName = nameParts[1] + ' ' + nameParts[0]
                print('Processing ' + fullName + '…')
    
                # Make cover page 'cover.pdf' with students name in upper left hand corner
                # Arial bold seemed to have the best OCR of the fonts readily available to FPDF
                coverPDF = FPDF('P', 'mm', 'Letter')
                coverPDF.add_page()            
                coverPDF.set_font("Arial", style = 'B',size = 16)
                coverPDF.cell(0, 0, fullName,ln = 1, align = 'L')
                coverPDF.output('cover.pdf')
    
                # Open the output file 'Output.pdf' then start processing
                with open('Output.pdf', 'wb') as output_file:
                    outReport_writer = PdfFileWriter()
                    wm_reader = PdfFileReader(wm_file)
            
                    # Open the watermark pdf, then merge the report and the cover page (for page 1)
                    #    If the report is longer than the watermark pdf, just tack the excess pages
                    #    on the end. The output is put into Output.pdf
                    with open('cover.pdf', 'rb') as cover_file:
                        cover_reader = PdfFileReader(cover_file)
                        with open(fn, 'rb') as origReport_file:
                            origReport_reader = PdfFileReader(origReport_file, strict = False)
                            origPages = origReport_reader.getNumPages()
                            for i in range(maxPages):
                                pdf_page = wm_reader.getPage(i)
                                if i + 1 < origPages:
                                    pdf_page.mergePage(origReport_reader.getPage(i))
                                if i == 0:                            
                                    pdf_page.mergePage(cover_reader.getPage(0))
                                outReport_writer.addPage(pdf_page)            
                            if origPages > maxPages:    # Handle the extra long reports here
                                for i in range(maxPages, origPages):
                                    outReport_writer.addPage(origReport_reader.getPage(i))
                            outReport_writer.write(output_file)
                            output_file.close() 
                            origReport_file.close()
                        cover_file.close()
                    # Remove the cover page, which is no longer needed.
                    os.remove('cover.pdf')
                
                    # Rename Output.pdf to the original filename.
                    os.rename('Output.pdf', fn)
            else:
                print(f'The student ID {studentID} does not exist.')

    wm_file.close()

# The following function merges all PDFs in the current directory into some number of merged PDFs
#    with names Merge0.pdf, Merge1.pdf, etc. The variable numPerFile determines how many files
#    are included in each merged file. This function is not currently used.
#    Unfortunately, merged files confuse Gradescope's processing engine for reasons that I do
#    understand
def MergePDFsInDirectory():
    cnt = 0
    mergeNum = 0
    numPerFile = 200
    mergeName = 'Merge_' + str(mergeNum) + '.pdf'
    merger = PdfFileMerger()
    for fn in os.listdir():
        if fn.endswith('.pdf'):
            merger.append(fn)
            cnt += 1
            if cnt > numPerFile:
                merger.write(mergeName)
                merger.close()
                merger = PdfFileMerger()
                mergeNum += 1
                mergeName = 'Merge_' + str(mergeNum) + '.pdf'
                cnt = 0

    merger.write(mergeName)
    merger.close()
        
if __name__ == '__main__':
    main()
