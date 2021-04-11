# Class for accessing Canvas programatically
# Useful resources include:
#   https://canvasapi.readthedocs.io/en/stable/getting-started.html
#   https://github.com/ucfopen/canvasapi
#   https://canvas.instructure.com/doc/api/assignments.html
#   https://github.com/dsavransky/grading

from datetime import datetime, date
from dateutil import parser
import os
import numpy as np              # Install with Anaconda
import pandas as pd             # Install with Anaconda, also installs numpy I think
from canvasapi import Canvas    # pip install canvasapi
import keyring                  # pip install keyring
from bullet import Bullet       # pip install bullet
import getpass

class mahCanvas:
# -----------------------------------------------------------------------------------
#
#           Accessing Canvas
#
# -----------------------------------------------------------------------------------

    def __init__(self):
    # Logs on to Canvas using token stored in system keychain. If this is the first log in
    #     on this computer, you will be prompted to enter your Canvas token. To get this
    #     go to Account > Settings in Canvas, and click on New Access Token. Copy the token
    #     and enter it. Getting a new token invalidates the old token.

        canvas_token_file = None
        canvasURL = "https://canvas.cornell.edu"
        canvasTokenName = 'Cornell_Canvas_Token'
        token = keyring.get_password(canvasTokenName, "canvas")
        if token is None:
            if canvas_token_file is None:
                token = getpass.getpass("Enter canvas token:\n")
            else:
                with open(canvas_token_file, "r") as f:
                    tmp = f.read()
                token = tmp.strip()
            try:
                canvas = Canvas(canvasURL, token)
                canvas.get_current_user()
                keyring.set_password(canvasTokenName, "canvas", token)
                print("Connected.  Token Saved")
            except InvalidAccessToken:
                print("Could not connect. Token not saved.")
        else:
            canvas = Canvas(canvasURL, token)
            canvas.get_current_user()
            print("Connected to Canvas.")
        self.canvas = canvas
            
# -----------------------------------------------------------------------------------
#
#           Accessing Courses and Assignments
#
# -----------------------------------------------------------------------------------

    def listCourses(self, onlyThisTerm = True):
    # Returns a list of courses to which the current user has access. By default, only courses
    #   from the current semester are returned. Pass onlyThisTerm = False to get all courses.

        courses = self.canvas.get_courses(include=["term"])
        present = datetime.now()

        courseStrs = []
        courseNums = []
        curTerm = self.currentTerm()
        for course in courses:
            if not onlyThisTerm or course.term['name'] == curTerm:
                courseStrs.append(str(course))
                courseNums.append(course.id)
 
        return courseStrs, courseNums
    
    def listAssignments(self):
    # Returns a list of assignments from the current course (self.course)

        if not hasattr(self,'course'):
            print('\a')
            print('You need to choose a course before choosing an assignment. Exiting now.')
            return -1
        assigns = self.course.get_assignments()

        assignNames = []
        assignIDs = []
        for assign in assigns:
            assignNames.append(str(assign))
            assignIDs.append(assign.id)

        return assignNames, assignIDs
    
    def chooseCourse(self, onlyThisTerm):
    # Interactively choose a course from Canvas

        strs, ids = self.listCourses(onlyThisTerm)
        cli = Bullet("Choose course", strs, margin=3, return_index=True)
        _, idx = cli.launch()
        return ids[idx]


    def chooseAssignment(self):
    # Interactively choose assignment from current course

        strs, ids = self.listAssignments()
        cli = Bullet("Choose assignment", strs, margin=3, return_index=True)
        _, idx = cli.launch()
        return ids[idx]
        
    def currentTerm(self):
    # Guesses the current semester based on today's date. Bit of a kludge
        today = date.today()
        springEnd = datetime.strptime('May 30', '%b %d').date().replace(year=today.year)
        summerEnd = datetime.strptime('Aug 15', '%b %d').date().replace(year=today.year)
        if today < springEnd:
            term = 'Spring'
        elif today < summerEnd:
            term = 'Summer'
        else:
            term = 'Fall'
        return term + ' ' + str(today.year)
            
# -----------------------------------------------------------------------------------
#
#           Setting Due Dates (Assignment Overrides) for Sections and/or Individual Students
#
# -----------------------------------------------------------------------------------

    def downloadStudentList(self, onlyThisTerm = True):
    # Downloads a list of students and their Canvas IDs for a specific course and outputs to csv
        courseNum = self.chooseCourse(onlyThisTerm)
        self.course = self.canvas.get_course(courseNum)
        baseName = self.course.course_code
        students = self.course.get_users(enrollment_type=['student'], include=["enrollments"])
        studentList = []
        for student in students:
            data = {'Name' : student.sortable_name,
                    'studentID' : student.id}
            studentList.append(data)
        if len(studentList) > 0:
            fileName = baseName + 'students.csv'
            studentList = pd.DataFrame(studentList)
            studentList.to_csv(fileName, index=False)
        
    
    def downloadAssignmentOverrides(self, onlyThisTerm = True):
    # Downloads the "override" due dates from an assignment in a course
    #   Separate csv's are output for section overrides and student overrides
    
        courseNum = self.chooseCourse(onlyThisTerm)
        self.course = self.canvas.get_course(courseNum)
        assignmentNum = self.chooseAssignment()
        assignment = self.course.get_assignment(assignmentNum)
        overrides = assignment.get_overrides()
        baseName = self.course.course_code
        studentList = []
        sectionList = []
        for override in overrides:
            if hasattr(override, 'student_ids'):    # Student override?
                for id in override.student_ids:
                    student = self.course.get_user(id)
                    due_at = datetime.strptime(override.due_at,"%Y-%m-%dT%H:%M:%SZ")
                    data = {'Name' : student.sortable_name,
                            'studentID' : id,
                            'due_date' : due_at.strftime('%m/%d/%Y'),
                            'due_time' : due_at.strftime('%H:%M') }
                    studentList.append(data)
                print('Student override for ', override)
            elif hasattr(override,'course_section_id'): # Section override?
                due_at = datetime.strptime(override.due_at,"%Y-%m-%dT%H:%M:%SZ")
                data = {'Section' : override.title,
                        'course_section_id' : override.course_section_id,
                        'due_date' : due_at.strftime('%m/%d/%Y'),
                        'due_time' : due_at.strftime('%H:%M') }
                sectionList.append(data)
                
        if len(sectionList) > 0:
            fileName = baseName + 'sectionOverrides.csv'
            sectionList = pd.DataFrame(sectionList)
            sectionList.to_csv(fileName, index=False)
        
        if len(studentList) > 0:
            fileName = baseName + 'studentOverrides.csv'
            studentList = pd.DataFrame(studentList)
            studentList.to_csv(fileName, index=False)
        
    def uploadAssignmentOverrides(self, overwrite = False, onlyThisTerm = True):
    # Uploads the "override" due dates for an assignment in a course from one or two csv's
        
        # Use interactive lists to get course and assignment
        courseNum = self.chooseCourse(onlyThisTerm)
        self.course = self.canvas.get_course(courseNum)
        assignmentNum = self.chooseAssignment()
        assignment = self.course.get_assignment(assignmentNum)
        
        baseName = self.course.course_code
        
        # If overwriting, erase existing overrides
        if overwrite:
            overrides = assignment.get_overrides()
            for override in overrides:
                override.delete()

        # Process student overrides
        fileName = baseName + 'studentOverrides.csv'
        if os.path.isfile(fileName):
            
            # Process student overrides by building a dictionary of all of the exceptions
            #   Use the due_at as the key for the dictionary
            print(f'Processing student overrides from {fileName}.')
            studentOverrides = {}
            df = pd.read_csv(fileName)
            for row in df.itertuples(index=True, name='Pandas'):
                print(row.Name, row.studentID, row.due_date, row.due_time)
                
                # Make sure student number and name match
                try:
                    student = self.course.get_user(row.studentID)
                except:
                    print('\a')
                    print(f'Error in file {fileName}! Student with the id {row.studentID} is not enrolled in course.')
                    print('Exiting now. You need to fix the file before proceeding.')
                    return -1
                
                if student.sortable_name != row.Name:
                    print('\a')
                    print(f'Error in file {fileName}! {row.Name} does not match {student.sortable_name}.')
                    print('Check that the ID number matches the name.')
                    return -1
                    
                # Use the due date and time as the key to the dictionary
                d = parser.parse(row.due_date + ' ' + row.due_time)
                studentOverrides.setdefault(d,[]).append(row.studentID)
            
            # Now create all of the student exceptions and upload
            for key, value in studentOverrides.items():
                override = {'student_ids' : value,                
                            'due_at': key}
                try:
                    assignment.create_override(assignment_override = override)
                except:
                    print('\a')
                    print("Request failed: Overwriteing an existing student override? Use overwrite = True.")
                    return -1
            
        # Process section overrides
        fileName = baseName + 'sectionOverrides.csv'
        if os.path.isfile(fileName):
            print(f'Processing section overrides from {fileName}.')
            df = pd.read_csv(fileName)
            
            # Get the lab sections for use in validation
            labSections = {}
            for section in self.course.get_sections():
                if section.name.startswith('LAB'):
                    labSections[section.id] = section.name

            for row in df.itertuples(index=True, name='Pandas'):
                print(row.Section, row.course_section_id, row.due_date, row.due_time)
                
                # Make sure section number and name match
                if row.course_section_id in labSections:
                    if labSections[row.course_section_id] != row.Section:
                        print('\a')
                        print(f'Error in file {fileName}! Section with the id {row.course_section_id} is not named {row.Section}.')
                        print('Exiting now. You need to fix the file before proceeding.')
                        return -1
                else:
                    print('\a')
                    print(f'Error in file {fileName}! No section with ID {row.course_section_id} in course.')
                    print('Exiting now. You need to fix the file before proceeding.')
                    return -1
               
                
                d = parser.parse(row.due_date + ' ' + row.due_time)
                override = {'course_section_id' : row.course_section_id,
                            'due_at' : d}

                try:
                    assignment.create_override(assignment_override = override)
                except:
                    print('\a')
                    print("Request failed: Overwriteing an existing section override? Use overwrite = True.")
                    return -1


# --------------------------------- Code below this line is not currently used -------------------------------------------- #

    def loadCourseAndLabs(self, courseNum):
        assert isinstance(courseNum, int), "courseNum must be an int"

        # Get the course
        course = self.canvas.get_course(courseNum)
        
        # Make a dictionary to hold the lab sections
        labIDs = {}
        labSections = {}
        discIDs = {}
        discSections = {}
        for section in course.get_sections():
            if section.name.startswith('LAB'):
                labIDs[section.name] = section.id
                labSections[section.id] = section.name
            elif section.name.startswith('DIS'):
                discIDs[section.name] = section.id
                discSections[section.id] = section.name
                
        print(f'Found {len(labSections)} lab sections.')
        
        # Now add missing cases
        labIDs['None'] = -1
        labSections[-1] = 'None'
        discIDs['None'] = -1
        discSections[-1] = 'None'
 
        students = course.get_users(enrollment_type=['student'], include=["enrollments", "test_student"])
        names = []
        IDs = []
        netIDs = []
        labs = []
        discs = []
        for student in students:
            names.append(student.sortable_name)
            IDs.append(student.id)
            netIDs.append(student.login_id)
            
            # Each student will be enrolled in a lecture, section, and at least one lab.
            # We will discard the online lab section in an in-person exists
            tempLab = -1
            tempDisc = -1
            for i in range(len(student.enrollments)):
                if student.enrollments[i].get('course_section_id') in labSections:
                    if tempLab > 0:
                        if tempLab == 34798:    # Online lab
                            tempLab = student.enrollments[i].get('course_section_id')
                    else:
                        tempLab = student.enrollments[i].get('course_section_id')
                elif student.enrollments[i].get('course_section_id') in discSections:
                    tempDisc = student.enrollments[i].get('course_section_id')
            labs.append(tempLab)
            discs.append(tempDisc)

        names = np.array(names)
        IDs = np.array(IDs)
        netIDs = np.array(netIDs)
        labs = np.array(labs)
        discs = np.array(discs)

        # One entry for every student
        self.course = course
        self.names = names
        self.IDs = IDs
        self.netIDs = netIDs
        self.labs = labs
        self.discs = discs

        # Used to translate between Canvas names and IDs
        self.labIDs = labIDs
        self.labSections = labSections
        self.discIDs = discIDs
        self.discSections = discSections

        self.courseName = course.name
        self.courseNum = courseNum
        
    def outputSpreadsheet(self, courseNum):
        self.loadCourseAndLabs(courseNum)
        df = pd.DataFrame({"Name" : self.names, "ID" : self.IDs, 'netID' : self.netIDs, 'Lab' : self.labs, 'Disc' : self.discs})
        df.to_csv("course.csv", index=False)
        
    def loadCourse(self, courseNum):
        assert isinstance(courseNum, int), "courseNum must be an int"

        # get the course
        course = self.canvas.get_course(courseNum)
        tmp = course.get_users(include=["enrollments", "test_student"])
        theNames = []
        IDs = []
        netIDs = []
        for t in tmp:
            isstudent = False
            for e in t.enrollments:
                if e["course_id"] == courseNum:
                    isstudent = e["role"] == "StudentEnrollment"

            if isstudent:
                theNames.append(t.sortable_name)
                IDs.append(t.id)
                netIDs.append(t.login_id)

        theNames = np.array(theNames)
        IDs = np.array(IDs)
        netIDs = np.array(netIDs)

        self.course = course
        self.theNames = theNames
        self.IDs = IDs
        self.netIDs = netIDs

        self.coursename = course.name

    def studentName(self, studentID):
    
        assert isinstance(studentID, int), "studentID must be an int"
        loc = np.where(self.IDs == studentID)[0]
        if loc.size == 0:
            return None 
        else:
            return self.names[loc[0]]

        
        