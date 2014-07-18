def bar(progress,barlength=30):
    barLength = barlength # Modify this to change the length of the progress bar
    status = ""
    progress = float(progress)
    
    if progress < 0:
        progress = 0
        status = " [ Halt. ]\r\n"
    if progress >= 1:
        progress = 1
        status = " [ Done. ]\r\n" 

    block = int(round(barLength*progress))
    text = "\rProgress: [{0}] {1}%".format( "."*block + " "*(barLength-block), progress*100)
    sys.stdout.write(text)
    sys.stdout.flush()
