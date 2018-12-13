#!/usr/bin/python3
"""
Plots channels zero and 7 of the USB-DUX in two different windows. Requires pyqtgraph.

"""

import threading
from time import sleep
import sys

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

import numpy as np

import pyusbdux as c

import scipy.signal as sig

class IIR2Filter:
    scale = 2**10
    fs = 250
    
    def __init__(self,num,sos):
        self.dFormI(num,sos)

    def dFormI(self,num,sos):
        sos = sos[num]
        self.b0 = sos[0]
        self.b1 = sos[1]
        self.b2 = sos[2]
        self.a1 = sos[4]
        self.a2 = sos[5]
        
        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0
        
    def filter(self,x):
        
        out = x*self.b0 + self.x1*self.b1 + self.x2*self.b2 - self.y1*self.a1 - self.y2*self.a2
        
        out = np.round(out/self.scale)
        
        self.x2 = self.x1
        self.y2 = self.y1
        self.x1 = x
        self.y1 = out
        
        return out
    

class IIRFilter:
    scale = 2**10
    
    def __init__(self,sos):
        self.getInstances(sos)
    
    def getInstances(self,sos):
        sos = np.round(sos*self.scale)
        self.first = IIR2Filter(0,sos)
        self.second = IIR2Filter(1,sos)
    
    def filter(self,x):
        x2 = self.first.filter(x)
        y = self.second.filter(x2)
        
        return y

# create a global QT application object
app = QtGui.QApplication(sys.argv)

# signals to all threads in endless loops that we'd like to run these
running = True

channel = 0

class QtPanningPlot:
    scale = 1000

    def __init__(self,title):
        self.win = pg.GraphicsLayoutWidget()
        self.win.setWindowTitle(title)
        self.plt = self.win.addPlot()
        self.plt.setYRange(-self.scale,self.scale)
        self.plt.setXRange(0,500)
        self.curve = self.plt.plot()
        self.data = []
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)
        self.layout = QtGui.QGridLayout()
        self.win.setLayout(self.layout)
        self.win.show()
        
    def update(self):
        self.data=self.data[-500:]
        if self.data:
            self.curve.setData(np.hstack(self.data))

    def addData(self,d):
        self.data.append(d)


def getDataThread(qtPanningPlot1,qtPanningPlot2):
    # create stopband filter for 50Hz
    scale = 2**11
    fs = 250
    fc = 50
    sos = sig.butter(2,[(fc-5)/fs*2,(fc+5)/fs*2],'stop',output='sos')
    filt = IIRFilter(sos)
    global data
    #detect = []
    i=0
    last = 0
    # endless loop with sleeps not for timing but for multitasking
    while running:
        # loop as fast as we can to empty the kernel buffer
        while c.hasSampleAvailable():
            sample = c.getSampleFromBuffer()
            sample = sample[channel]*scale
            sample2 = filt.filter(int(np.round(sample)))
            qtPanningPlot1.addData(sample)
            qtPanningPlot2.addData(sample2)
            data.append(sample)
            
         
            #detect.append(sample2)
            if sample2 >= 200 and i>=last:
                print('PULL')
                last = i+200  
            elif sample2 <= -100 and i>=last:
                print('PUSH')
                last = i+150        
            i+=1
            
        # let Python do other stuff and sleep a bit
        sleep(0.1)

# open comedi
c.open()

# info about the board
print("ADC board:",c.get_board_name())

data = []

# Let's create two instances of plot windows
qtPanningPlot1 = QtPanningPlot("Unfiltered")
qtPanningPlot2 = QtPanningPlot("Filtered")

# create a thread which gets the data from the USB-DUX
t = threading.Thread(target=getDataThread,args=(qtPanningPlot1,qtPanningPlot2,))

# start data acquisition
c.start(8,250)

# start the thread getting the data
t.start()

# showing all the windows
app.exec_()

# no more data from the USB-DUX
c.stop()

# Signal the Thread to stop
running = False

# Waiting for the thread to stop
t.join()

c.close()

np.savetxt('unfiltData.dat',data)

print("finished")
