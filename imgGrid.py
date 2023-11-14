#!/usr/bin/python3
################################################################################
# 
# Copyright (c) 2022-2023 Dawson Dean
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
################################################################################
#
# pip install requests
################################################################################
from datetime import datetime
import random

# GUI classes
import matplotlib
matplotlib.use('TkAgg')
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
#import matplotlib.pyplot as plt
#import matplotlib.image as mpimg
import tkinter as tk

# Multiprocessing
from torch.multiprocessing import Process
import multiprocessing

random.seed(3)

TIMER_PERIOD_IN_MS  = 1000

NUM_REQUESTS_BETWEEN_INPUT_COMMANDS = 5
NUM_REQUESTS_BETWEEN_STATUS_REPORT  = 10
NUM_REQUESTS_BETWEEN_GC             = 1000


WINDOW_WIDTH            = 700
WINDOW_HEIGHT           = 700
WINDOW_DIMENSION_STR    = "700x700"

# Window coordinates are relative to the top left corner
BUTTON_HEIGHT           = 60
BUTTON_WIDTH            = 150
BUTTON_PADDING          = 30

BUTTON_ROW_Y            = (WINDOW_HEIGHT - (BUTTON_HEIGHT + BUTTON_PADDING))
BUTTON_ROW_COLUMN1_X    = (WINDOW_WIDTH - ((2 * BUTTON_WIDTH) + (2 * BUTTON_PADDING)))
BUTTON_ROW_COLUMN2_X    = (WINDOW_WIDTH - ((1 * BUTTON_WIDTH) + (1 * BUTTON_PADDING)))

VAR_LABEL_X             = 10
VAR_TEXT_X              = 230

MENU1_X                 = 10
MENU2_X                 = 400
TOOLBAR_ROW_Y           = 20

FIRST_ROW_Y             = 100
ROW_HEIGHT              = 70
VAR_COLUMN1_Y           = FIRST_ROW_Y + (0 * ROW_HEIGHT)
VAR_COLUMN2_Y           = FIRST_ROW_Y + (1 * ROW_HEIGHT)
VAR_COLUMN3_Y           = FIRST_ROW_Y + (2 * ROW_HEIGHT)
VAR_COLUMN4_Y           = FIRST_ROW_Y + (3 * ROW_HEIGHT)
VAR_COLUMN5_Y           = FIRST_ROW_Y + (4 * ROW_HEIGHT)
VAR_COLUMN6_Y           = FIRST_ROW_Y + (5 * ROW_HEIGHT)
VAR_COLUMN7_Y           = FIRST_ROW_Y + (6 * ROW_HEIGHT)


# Dropdown menu options
g_ServerTypeOptions = [
    "Local Apache",
    "Amazon Cloud"
]
g_ClientTypeOptions = [
    "CKD Progresion",
    "Fuzz"
]
  


################################################################################
################################################################################
class ImageGridUIClass:
    ########################################
    ########################################
    def __init__(self,  window):
        self.window = window

        self.RunningJobs = False
        self.ProcessInfo = None
        self.CommandQueue = None
        self.ReportQueue = None

        self.window.title("Image Grid")
        self.window.geometry(WINDOW_DIMENSION_STR)

        ###################################
        # Create the controls
        #self.inputTextBox = Entry(self.window)
        self.startButton = tk.Button(master=self.window, text="Start", command=self.OnStart)
        self.stopButton = tk.Button(master=self.window, text="Stop", command=self.OnStop)

        self.StatusLabel = tk.Label(master=self.window)

        self.StartTimeLabel = tk.Label(master=self.window)
        self.NumTestsLabel = tk.Label(master=self.window)
        self.NumSuccessLabel = tk.Label(master=self.window)
        self.NumErrorssLabel = tk.Label(master=self.window)

        self.StartTimeValue = tk.Label(master=window)
        self.NumTestsValue = tk.Label(master=window)
        self.NumSuccessValue = tk.Label(master=self.window)
        self.NumErrorssValue = tk.Label(master=self.window)

        self.ImageCanvas = tk.Canvas(self.window, width=700, height=700)

        # Create Dropdown menus
        self.ClientTypeVar = tk.StringVar(self.window)
        self.ClientTypeVar.set("CKD Progresion")
        self.ClientTypeMenu = tk.OptionMenu(self.window, self.ClientTypeVar, *g_ClientTypeOptions)

        self.ServerTypeVar = tk.StringVar(self.window)
        self.ServerTypeVar.set("Local Apache")
        self.ServerAddressMenu = tk.OptionMenu(self.window, self.ServerTypeVar, *g_ServerTypeOptions)
        

        ###################################
        # Layout the controls in the windows
        self.startButton.place(x=BUTTON_ROW_COLUMN1_X, y=BUTTON_ROW_Y, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)
        self.stopButton.place(x=BUTTON_ROW_COLUMN2_X, y=BUTTON_ROW_Y, height=BUTTON_HEIGHT, width=BUTTON_WIDTH)

        self.ServerAddressMenu.place(x=MENU1_X, y=TOOLBAR_ROW_Y)
        self.ClientTypeMenu.place(x=MENU2_X, y=TOOLBAR_ROW_Y)

        self.StatusLabel.place(x=VAR_LABEL_X, y=VAR_COLUMN1_Y)

        self.StartTimeLabel.place(x=VAR_LABEL_X, y=VAR_COLUMN2_Y)
        self.StartTimeValue.place(x=VAR_TEXT_X, y=VAR_COLUMN2_Y)

        self.NumTestsLabel.place(x=VAR_LABEL_X, y=VAR_COLUMN3_Y)
        self.NumTestsValue.place(x=VAR_TEXT_X, y=VAR_COLUMN3_Y)

        self.NumSuccessLabel.place(x=VAR_LABEL_X, y=VAR_COLUMN4_Y)
        self.NumSuccessValue.place(x=VAR_TEXT_X, y=VAR_COLUMN4_Y)

        self.NumErrorssLabel.place(x=VAR_LABEL_X, y=VAR_COLUMN5_Y)
        self.NumErrorssValue.place(x=VAR_TEXT_X, y=VAR_COLUMN5_Y)
        #self.ImageCanvas.place(x=0, y=0)


        # Initialize the state
        self.StatusLabel.config(text="IDLE")

        self.StartTimeLabel.config(text="Start Time: ")
        self.NumTestsLabel.config(text="Num Tests: ")
        self.NumSuccessLabel.config(text="Num Success: ")
        self.NumErrorssLabel.config(text="Num Errorss: ")

        self.StartTimeValue.config(text="")
        self.NumTestsValue.config(text="0")
        self.NumSuccessValue.config(text="0")
        self.NumErrorssValue.config(text="0")

        self.OnStop()
        self.OnTimer()
    # End - __init__




    ########################################
    ########################################
    def OnTimer(self):
        # Check if the process stopped.
        if (self.RunningJobs):
            if (not (self.ProcessInfo.is_alive())):
                print("Process Stopped")
                self.OnStop()
            else:
                #print("Process Still Running")
                pass
        # End - if (self.RunningJobs)


        ###########################
        if ((self.RunningJobs) and (self.ReportQueue != None)):
            #print("Process Still Running")
            try:
                reportStr = self.ReportQueue.get(False)
            except Exception:
                reportStr = None
            if (reportStr != None):
                #print("Valid Report: " + reportStr)
                statusDict = eval(reportStr)
                self.NumTestsValue.config(text=statusDict['numRequests'])
                self.NumSuccessValue.config(text=statusDict['numSuccess'])
                self.NumErrorssValue.config(text=statusDict['numErrors'])
        # End - if ((self.RunningJobs) and (self.ReportQueue != None)):


        # Schedule the next timer callback
        self.window.after(TIMER_PERIOD_IN_MS, self.OnTimer)
    # End - OnTimer





    ########################################
    ########################################
    def OnStart(self):
        paramDict = {}

        serverType = self.ServerTypeVar.get()
        #print(">>> serverType= " + serverType)
        if (serverType == "Local Apache"):
            paramDict['serverName'] = "http://127.0.0.1/cgi-bin/predictor.py"
        else:
            paramDict['serverName'] = "http://www.dawsondean.com/cgi-bin/predictor.py"

        clientType = self.ClientTypeVar.get()
        #print(">>> clientType= " + clientType)
        if (clientType == "CKD Progresion"):
            paramDict['opName'] = "CKDProgression"
        else:
            paramDict['opName'] = "CKDProgression"

        # Make a pipe that will be used to send commands and return status updates
        recvPipe, sendPipeEnd = multiprocessing.Pipe(False)
        self.CommandQueue = multiprocessing.Queue()
        self.ReportQueue = multiprocessing.Queue()

        # clear the canvas
        #self.ImageCanvas.delete('all')
        # Save the filename object as a member - it cannot be garbage collected.
        #filePathName = '/home/ddean/ddRoot/tools/Busy.png'
        #self.filename = PhotoImage(file=filePathName)
        #image = self.ImageCanvas.create_image(100, 100, image=self.filename)
        #self.ImageCanvas.pack()

        # Fork the job process.
        #self.ProcessInfo = Process(target=jobRunnerProcessMain, args=(self.CommandQueue, self.ReportQueue, sendPipeEnd, "param1"))
        self.ProcessInfo = Process(target=serverClientProcessMain, args=(self.CommandQueue, self.ReportQueue, sendPipeEnd, str(paramDict)))
        self.ProcessInfo.start()
        self.RunningJobs = True

        # Update the GUI to show we started the job.
        now = datetime.now()
        timeStr = now.strftime("%m-%d %H:%M:%S")
        self.StatusLabel.config(text="RUNNING")
        self.StartTimeValue.config(text=timeStr)
        self.NumTestsValue.config(text="0")
        self.NumSuccessValue.config(text="0")
        self.NumErrorssValue.config(text="0")
    # End - OnStart





    ########################################
    ########################################
    def OnStop(self):
        self.SendCommandToWorker("Quit")
        self.RunningJobs = False

        # clear the canvas
        #self.ImageCanvas.delete('all')
        # Save the filename object as a member - it cannot be garbage collected.
        #filePathName = '/home/ddean/ddRoot/tools/Idle.png'
        #self.filename = PhotoImage(file = filePathName)
        #image = self.ImageCanvas.create_image(100, 100, image=self.filename)
        #self.ImageCanvas.pack()

        self.StatusLabel.config(text="IDLE")
    # End - OnStop





    ########################################
    # "Quit"
    ########################################
    def SendCommandToWorker(self, commandStr):
        if ((self.RunningJobs) and (self.CommandQueue is not None)):
            #print("Process Still Running")
            try:
                self.CommandQueue.put(commandStr)                
            except Exception:
                pass
        # End - if ((self.RunningJobs) and (self.ReportQueue != None)):
    # End - SendCommandToWorker




    ########################################
    ########################################
    def OnPlot(self):
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        v = np.array([16, 16.31925, 17.6394, 16.003, 17.2861, 17.3131, 19.1259, 18.9694, 22.0003, 22.81226])
        p = np.array([16.23697, 17.31653, 17.22094, 17.68631, 17.73641,  18.6368, 19.32125, 19.31756 , 21.20247, 22.41444, 22.11718, 22.12453])

        fig = Figure(figsize=(16, 16))
        a = fig.add_subplot(111)
        a.scatter(v, x, color='red')
        a.plot(p, range(2 + max(x)), color='blue')
        a.invert_yaxis()

        a.set_title("Estimation Grid", fontsize=16)
        a.set_ylabel("Y", fontsize=14)
        a.set_xlabel("X", fontsize=14)

        canvas = FigureCanvasTkAgg(fig, master=self.window)
        canvas.get_tk_widget().pack()
        canvas.draw()
    # End - OnPlot

# End - class ImageGridUIClass:







################################################################################
# MAIN
################################################################################

# The main tkinter window
window = tk.Tk()
window.title('TDF Widget')
window.geometry("800x800")

# Make the gui class which is attached to this window.
tdfGui = ImageGridUIClass(window)

# Run the gui
window.mainloop()



#plt.title("Sheep Image")
#plt.xlabel("X pixel scaling")
#plt.ylabel("Y pixels scaling")
#image = mpimg.imread("sheep.png")
#plt.imshow(image)
#plt.show()


