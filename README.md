# ENGR4053_IIR_Assignment3
Bicep EMG detector (pushing and pulling) coded by Lauren Lusk (2417560L) and Milad Sharifikheirabadi (2420875S) 

## Digital Signal Processing 4 – Prof. Brend Porr
Report of Assignment 2 (IIR Filter) – 17th December 2018

Lauren Lusk & Milad Sharifikheirabadi


### Introduction:
In this assignment, we investigated the EMG response of the bicep when one is pushing or pulling an object. 
We wrote a program that printed “PULL” and “PUSH” when it detected the appropriate motion.

### The Project:

#### The Set-up:
The experiment set-up was simple.
Two electrodes were connected to the right bicep of Lauren Lusk, and a third, grounding, electrode was attached to her elbow.
The EMG signal was fed through a sigma board, then an amplifier, and finally the computer.

![[alt text](https://github.com/laurenlusk/ENGR4053_IIR_Assignment3/blob/master/22LNnVj9TBeNIjCpVsMOdw.jpg)

We used a backpack weighing approximately 10kg as the object that we pushed and pulled across the bench.
In order to simplify the results, we moved the backpack 30cm back and forth across the bench. 
This way we were better able to detect whether the backpack was pushed or pulled.

#### The Software
In order to collect and filter the data, the program realtime_two_channel_plot.py from Bernd Porr's pyusbdux was hacked to plot both the filtered and unfiltered data. 
First, we created an IIR filter, which used to filter out the 50~Hz noise and make the signal cleaner.
The IIRFilter class broke down the sos coefficients generated by python (scipy.signal.butter) into two instances of IIR second order coefficients.
The data flow for one of the direct form 1 instances is displayed below:

![alt text](https://github.com/laurenlusk/ENGR4053_IIR_Assignment3/blob/master/dForm1.png)

Next, we manipulated the plotting windows, so the unfiltered and filtered data were displayed instead of data from two different channels.
Once the windows were plotting correctly, we observed the EMG response when the backpack was pushed and pulled.
When the backpack was pushed, the magnitude rose over 200 (scaled magnitude).
When the backpack was pulled, the magnitude was less than -100 (scaled magnitude).
Examples of both responses are below:

![alt text](https://github.com/laurenlusk/ENGR4053_IIR_Assignment3/blob/master/pull.svg)

![alt text](https://github.com/laurenlusk/ENGR4053_IIR_Assignment3/blob/master/push.svg)

Finally, we created the code that detected which action was performed and prints the appropriate word.
The detection thresholds were established from observing the responses above.


#### Results and Analysis
One of the difficulties was initially setting up the IIR filter.
The filter worked properly, but because the magnitude of the input was between -1 and 1, the input had to be scaled up.
Based on past samples from ECG, we scaled the magnitude by 2^11.
Once the scale was appropriately set, the data could be properly filtered.

An unanticipated difficulty was noise induced by the wires.
Whenever the backpack was moved, the wires connected to the bicep also moved.
The resultant noise consistently made the program glitch when the backpack was pulled.
Instead of simply printing "PULL", the program would print "PULL" then immediately after "PRINT".
In order to correct for this, a delay was created, so nothing was printed for 200 samples after "PULL".
In addition, we also held the cables still in order to reduce their movement.
Overall, we were mostly successful in our endeavour.
We successfully detected when the backpack was pushed and pulled, but due to the unpredictability of the noise from the EMG wires, the program occasionally prints when it should not.

### Appendix 1:
#### [realtime_two_channel_plot.py](https://github.com/laurenlusk/ENGR4053_IIR_Assignment3/blob/master/pyusbdux/examples/realtime_two_channel_plot.py)
```
import threading
from time import sleep
import sys

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui

import numpy as np

import pyusbdux as c

import scipy.signal as sig

class IIR2Filter:
    """
    Implements a 2nd order IIR filter."
    """
    scale = 2**10   # scale for the filter coefficients
    fs = 250        # sampling frequency of the incoming data
    
    def __init__(self,num,sos):
        """
        Initializes class.
        """
        self.dFormI(num,sos)

    def dFormI(self,num,sos):
        """
        Creates a Direct Form I from sos coefficients,
        where num is the index of the array with the coefficients.
        """
        #gets coefficients 
        sos = sos[num]
        self.b0 = sos[0]
        self.b1 = sos[1]
        self.b2 = sos[2]
        self.a1 = sos[4]
        self.a2 = sos[5]
        
        # initializes buffer to zero
        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0
        
    def filter(self,x):
        """
        Filters the data in real time.
        """
        out = x*self.b0 + self.x1*self.b1 + self.x2*self.b2 - self.y1*self.a1 - self.y2*self.a2
        out = np.round(out/self.scale)  #removes scale factor
        
        # updates buffer
        self.x2 = self.x1
        self.y2 = self.y1
        self.x1 = x
        self.y1 = out
        
        return out
    

class IIRFilter:
    """
    This class creates a chain of 2nd order filter instances of IIR2Filter.
    """
    scale = 2**10   # scale for the filter coefficients
    
    def __init__(self,sos):
        """
        Initializes instances.
        """
        self.getInstances(sos)
    
    def getInstances(self,sos):
        """
        Creates IIR2Filter objects.
        """
        sos = np.round(sos*self.scale)  #scales the coefficients
        self.first = IIR2Filter(0,sos)
        self.second = IIR2Filter(1,sos)
    
    def filter(self,x):
        """
        Filters data in real time.
        """
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
    """
    Takes unfiltered data from input and filters out the noise.
    """
    # creates stopband filter for 50Hz
    scale = 2**11   # scale for input (raw data between -1 and 1)
    fs = 250
    fc = 50
    sos = sig.butter(2,[(fc-5)/fs*2,(fc+5)/fs*2],'stop',output='sos')
    filt = IIRFilter(sos)
   
    global data # data collected for future figures
    # i and last used to create a time buffer
    # used to reduce the number of times each word is printed
    # and reduce the influence of the wire noise
    i=0      
    last = 0
    # endless loop with sleeps not for timing but for multitasking
    # collects data from input
    while running:
        # loop as fast as we can to empty the kernel buffer
        while c.hasSampleAvailable():
            sample = c.getSampleFromBuffer()
            sample = sample[channel]*scale  # scales input
            # filters out 50Hz
            sample2 = filt.filter(int(np.round(sample)))
            # adds samples to real time graphs
            qtPanningPlot1.addData(sample)
            qtPanningPlot2.addData(sample2)
            # saves unfiltered data for figures later
            data.append(sample)
         
            # detects whether the object was pushed or pulled
            if sample2 >= 200 and i>=last:
                print('PULL')
                last = i+200
            elif sample2 <= -100 and i>=last:
                print('PUSH')
                last = i+150 
            else:
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
```
