import mahCanvas

def main():
    
    c = mahCanvas.mahCanvas()
    c.downloadStudentList(onlyThisTerm = True)
    
if __name__ == '__main__':
    main()
