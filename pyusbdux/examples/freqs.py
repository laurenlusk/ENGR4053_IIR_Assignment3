#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 13 15:24:27 2018

@author: labuser
"""
import numpy as np
import matplotlib.pylab as plt

emg = np.loadtxt('unfiltData.dat')
fs = 250

x = abs(np.fft.fft(emg))

resp = np.zeros(len(emg))
half = int(len(emg)/2)
resp[0:half] = x[half:len(emg)]
resp[half:len(emg)] = x[0:half]

faxis = np.linspace(-fs,fs,len(emg))

plt.plot(faxis,resp)
