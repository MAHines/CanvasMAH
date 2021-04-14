import mahCanvas
from datetime import datetime, date
import argparse

def main():
    
    # Read in the arguments and validate
    parser = argparse.ArgumentParser(description="Set due dates for multiple sections/students in Canvas assignment")
    parser.add_argument('firstDate', type = str, help = 'Earliest due date for assignment. (e.g., 4/1/2021)')
    args = parser.parse_args()
    firstDate = args.firstDate

    c = mahCanvas.mahCanvas()
    c.uploadAssignmentOverrides(firstDate, overwrite = True, onlyThisTerm = True)
    
if __name__ == '__main__':
    main()
