import sys
import subprocess 
import os
import numpy as np
from tkinter import ttk
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import math
import os
from pathlib import Path
from preprocessing import pipeline
import pandas as pd
from sys import platform



def main(files):
    ls = ["groovyScript", "shellScript", "tilesDir", "OUTPUT_DIR", "WSIs_DIR", "WSIs_List", "QUPATH_PROJ"] 
    for i in ls:
        if i not in list(files.keys()):
            files[i] = None
    LOWER_PERCENTILE = int(files["low_perc"].get())
    UPPER_PERCENTILE = int(files["upper_perc"].get())
    jpgNormTiles = files["jpgNormTiles"].get()

    if jpgNormTiles == 1:
        jpgNormTiles = True
    else:
        jpgNormTiles = False

    if files['OUTPUT_DIR'] is None:
        dirname = os.path.dirname(files['QUPATH_PROJ'])
        files['OUTPUT_DIR'] = os.path.join(dirname, "results")
    

    # determine if application is a script file or frozen exe
    if getattr(sys, 'frozen', False):
        cwd = os.path.dirname(sys.executable)
    elif __file__:
        cwd = os.path.dirname(__file__)

    if files["groovyScript"] is None:
        files["groovyScript"] = os.path.join(cwd,'src','generateTiles.groovy')
    if files["shellScript"] is None:
        files["shellScript"] = os.path.join(cwd,'src','runQupath.sh')

        # Set the default value of both tiles and results directory to the QuPath project directory
    if files['tilesDir'] is None:
        dirname = os.path.dirname(files['QUPATH_PROJ'])
        files['tilesDir'] = os.path.join(dirname,"tiles")
    elif files['tilesDir'] is not None:
        if "tiles" != os.path.basename(os.path.normpath(files['tilesDir'])):
            files['tilesDir'] = os.path.join(files['tilesDir'], "tiles")
    

    if not str(files['WSI'].get()):
        wsiList = None
        files['WSI'] = None

    if files['WSIs_DIR'] == None and files['WSIs_List'] == None and files['WSI']==None:
        if platform == "win32":
            files['OUTPUT_DIR'] = files['OUTPUT_DIR'].replace(os.sep,"/")
        print("\n\n", "No information was provided on the WSIs to process. The entire QuPath project will be processed.")
        wsiList = files['WSIs_DIR']
        os.makedirs(f"{files['OUTPUT_DIR']}/preprocessingRes", exist_ok=True)
        logfile = os.path.join(f"{files['OUTPUT_DIR']}/preprocessingRes", "logfile.log")

    elif files['WSIs_DIR'] != None:
        print('\n\n' "The following absolute path to the file <slidesToProcess.csv> was provided in input: {}".format(files['WSIs_DIR']))
        wsiDir = files['WSIs_DIR']
        wsiDf = pd.read_csv(os.path.join(wsiDir, "slidesToProcess.csv"))
        wsiList = wsiDf['Slide'].tolist()


    elif files['WSIs_List'] != None:
        with open(files['WSIs_List'], 'r') as fn:
            data = fn.readlines()
            wsiList = [i.rstrip('\n') for i in data]
            fn.close()
        print('\n\n' "The following WSI(s) will be processed: {}".format(files['WSIs_List']))
        
    elif files['WSI'] !=None:
        wsiList = [files['WSI'].get()]
        print('\n\n' "The following WSI will be processed: {}".format(wsiList))

    else:
        print('You provided inconsistent arguments. Please check again.')
        exit()

    if platform == "win32":
        for i in ['QUPATH_PROJ','groovyScript','shellScript','tilesDir','OUTPUT_DIR','WSIs_DIR']:
            if files[i] != None:
                files[i] = files[i].replace("/",os.sep)
    
    if platform == "win32":
        files['tilesDir'] = files['tilesDir'].replace(os.sep,"/")
    with open(f"{files['groovyScript']}",'r') as fn:
        ln = fn.readlines()
    for idx, i in enumerate(ln):
        if i.startswith("def pathOutput = buildFilePath"):
            ln[idx] = f"def pathOutput = buildFilePath('{files['tilesDir']}', name_n)\n"
        elif i.startswith("File logfile") and 'logfile' in locals():
            ln[idx] = f'File logfile = new File("{logfile}")\n'
    with open(f"{files['groovyScript']}",'w') as fn:
        fn.writelines(ln)
        fn.close()

    print('\n\n\n\n', "================================================================ TILES PRE-PROCESSING PIPELINE ================================================================")

    print('\n',       "===============================================================================================================================================================")

    print('\n\n' "The following absolute paths will be used for tiles pre-processing:", "\n\n", "QUPATH_PROJ: {}".format(files['QUPATH_PROJ']), "\n\n", "GROOVY_SCRIPT_DIR: {}".format(files['groovyScript']), "\n\n", "shellScript: {}".format(files['shellScript']))

    print('\n\n' "The tiles to pre-process are stored under: {}".format(files['tilesDir']))  
    # Check if the results directory exists, otherwise create it
    outputDir = files['OUTPUT_DIR']
    check_outputDir = os.path.isdir(outputDir)
    if not check_outputDir:
        os.makedirs(outputDir)
        print('\n\n', "OUTPUT_DIR", "\n", "The folder {} has been created.".format(files['OUTPUT_DIR']), "Results from tiles pre-processing will be stored here.")
    else:
        print('\n\n' "Results from tiles pre-processing will be stored under:", "\n\n", "OUTPUT_DIR: {}".format(files['OUTPUT_DIR']))

    tilesPreprocessing = pipeline(files['QUPATH_PROJ'], files['groovyScript'], files['shellScript'], files['tilesDir'], files['OUTPUT_DIR'], files['WSIs_DIR'], wsiList = wsiList, lowerPerc = LOWER_PERCENTILE, upperPerc = UPPER_PERCENTILE, jpgNormTiles=jpgNormTiles)

    tilesPreprocessing.initialize()
        
    


def app():
    def browseFiles(name, label_file_explorer, dir= False):
        if dir == False:
            filename = filedialog.askopenfilename(initialdir = "/home/",
                                                title = "Select a File",
            )
        else:
            filename = filedialog.askdirectory()
        label_file_explorer.configure(text=f"File Opened: {filename}")
        files[name]=str(filename)

    def hide(widget_dict, exc, variable):
        if variable == 0:
            keys = list(widget_dict.keys())
            for i in exc:
                keys.remove(i)
            for widget in keys:
                widget_dict[widget].pack_forget()
            window.geometry("800x300")
        elif variable == 1:
            keys = list(widget_dict.keys())
            for i in exc:
                keys.remove(i)
            for widget in keys:
                widget_dict[widget].pack(side=TOP, anchor=N, expand = True)
            window.geometry("800x700")        
  
        
    def close():
        window.destroy() 
       
    window = Tk()
    window.title('Tiles Generation and Pre-processing Pipeline')
    
    window.geometry("800x300")
    
    window.config(background = "white")
    button_dict = {}
    button_dict["label_file_explorer_1"] = Label(window,text = "Groovy script file explorer",width = 100, height = 1,fg = "blue")
    button_dict["button_dict_1"] =Button(window, text="groovyScript", width=25, command=lambda*args: browseFiles("groovyScript", button_dict["label_file_explorer_1"]))
    button_dict["label_file_explorer_2"] = Label(window,text = "Shell script file explorer",width = 100, height = 1,fg = "blue")
    button_dict["button_dict_2"] =Button(window, text="shellScript", width=25, command=lambda*args: browseFiles("shellScript", button_dict["label_file_explorer_2"]))
    button_dict["label_file_explorer_3"] = Label(window,text = "Tiles file explorer",width = 100, height = 1,fg = "blue")
    button_dict["button_dict_3"] =Button(window, text="tilesDir", width=25, command=lambda*args: browseFiles("tilesDir", button_dict["label_file_explorer_3"], dir = True))
    button_dict["label_file_explorer_4"] = Label(window,text = "Pre-processing results file explorer",width = 100, height = 1,fg = "blue")
    button_dict["button_dict_4"] =Button(window, text="OUTPUT_DIR", width=25, command=lambda*args: browseFiles("OUTPUT_DIR", button_dict["label_file_explorer_4"], dir = True))
    button_dict["label_file_explorer_5"] = Label(window,text = "Path to the file 'slideToProcess.csv'",width = 100, height = 1,fg = "blue")
    button_dict["button_dict_5"] =Button(window, text="WSIs_DIR", width=25, command=lambda*args: browseFiles("WSIs_DIR", button_dict["label_file_explorer_5"], dir = True))
    label = ttk.Label(window,  text='Name of the WSIs to process:')
    var_1 = StringVar(window)
    button_dict["label"] = label
    txtfld=Entry(window, text="Name of the WSIs to process", bd=10,textvariable=var_1)
    button_dict["txtfld"] = txtfld
    button_dict["label_file_explorer_6"] = Label(window,text = "List of WSIs to process",width = 100, height = 1,fg = "blue")
    button_dict["button_dict_6"] =Button(window, text="WSIs_List", width=25, command=lambda*args: browseFiles("WSIs_List", button_dict["label_file_explorer_6"]))
    button_dict["label_file_explorer_7"] = Label(window,text = "QuPath Project",width = 100, height = 1,fg = "blue")
    button_dict["button_dict_7"] =Button(window, text="QUPATH_PROJ", width=25, command=lambda*args: browseFiles("QUPATH_PROJ", button_dict["label_file_explorer_7"]))
    button_dict["label_file_explorer_7"].pack()
    button_dict["button_dict_7"].pack()

    jpgNormTiles = IntVar()
    Checkbutton(window, text="jpgNormTiles", variable=jpgNormTiles).pack(expand=True)
    files["jpgNormTiles"] = jpgNormTiles


    label = ttk.Label(window,  text='Select the lower percentile for tiles filtering:')
    var= StringVar(window)
    var.set(int(10))
    low_perc = Spinbox(window, from_=0, to=100, width=10,textvariable=var)
    label.pack()
    low_perc.pack(expand=True)
    label = ttk.Label(window,  text='Select the upper percentile for tiles filtering:')
    var= StringVar(window)
    var.set(int(90))
    upper_perc = Spinbox(window, from_=0, to=100, width=10,textvariable=var)
    label.pack()
    upper_perc.pack(expand=True)
    var1 = IntVar()
    Checkbutton(window, text="Advanced Options", variable=var1, command=lambda*args: hide(widget_dict=button_dict, exc=["label_file_explorer_7","button_dict_7"], variable=var1.get())).pack(expand=True)
    files["upper_perc"] = upper_perc
    files["low_perc"] = low_perc
    files["WSI"] =  var_1
    button_dict_7 = Button(window, text = "Run preprocessing pipeline",command = lambda *args: main(files))
    button_dict_7.pack(expand=True)

    button_dict_8 = Button(window, text = "Exit",command = close)
    button_dict_8.pack(expand=True)
    window.mainloop()
    
if __name__ == "__main__":
    global files
    files = {}
    app()
    del files
