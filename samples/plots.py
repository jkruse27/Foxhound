import PySimpleGUI as sg
from matplotlib.backend_bases import MouseButton
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.signal as sig
import matplotlib
from dataset import *
from datetime import *
import pytz
from matplotlib.dates import num2date

"""
Module that encapsulates all operations involving plotting variables and plot interactions
"""

class Plots():
    """
    Class responsible for plotting and displaying the figures on the Canvas.
    Also controls interactions with the plots.
    """

    def __init__(self,canvas,FIGSIZE_X=800,FIGSIZE_Y=800):
        """Instantiate Plots and initialize Canvas
        
        Parameters
        ----------
        canvas : `tkinter.Canvas`
           Canvas in which to plot the figures
        FIGSIZE_X : `int`, optional
            Width of the figure in pixels. Default: 800
        FIGSIZE_Y : `int`, optional
            Height of the figure in pixels. Default: 800

        Returns
        -------
        `Plots`
            Return Plots instance
        """
        self.FIGSIZE_X = FIGSIZE_X
        self.FIGSIZE_Y = FIGSIZE_Y
        self.canvas = canvas
        self.fig, self.axs1 = plt.subplots(figsize=(FIGSIZE_X/100,FIGSIZE_Y/100), dpi=100)
        self.figure = FigureCanvasTkAgg(self.fig, canvas)
        self.fig.canvas.callbacks.connect('button_press_event', self.on_click)
        self.ax3 = None
        self.t_beg = None
        self.t_end = None
        self.beg = None
        self.beg_x = None
        self.end = None
        self.end_x = None
        self.draw_figure(self.canvas, self.figure)
        self.times = None

    def draw_figure(self, canvas, figure_canvas_agg):
        canvas.delete('all')
        figure_canvas_agg.draw()
        figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

    def get_fig(self):
        return self.figure 

    def selected(self):
        return self.beg != None and self.end != None

    def get_times(self):
        """
        Times of the markers
        """
        return num2date(self.beg_x).strftime("%Y-%m-%d %H:%M"), num2date(self.end_x).strftime("%Y-%m-%d %H:%M")

    def clear(self):
        """
        Removes the markers from the plot
        """
        if(self.end != None):
            self.end.remove()
            self.t_end.remove()
        if(self.beg != None):
            self.beg.remove()
            self.t_beg.remove()
        self.beg = None
        self.end = None
        self.fig.canvas.flush_events()
        self.draw_figure(self.canvas, self.figure)

    def on_click(self,event):
        """
        Action to be performed when the plot is clicked. Manages the markers in the plot
        """
        if event.inaxes is not None:
            if(event.button == MouseButton.LEFT and (self.end == None or self.end_x >= event.xdata)):
                if(self.beg == None):
                    self.beg = self.axs1.axvline(x=event.xdata, color='k', linestyle='--')
                    self.t_beg = self.axs1.text(event.xdata,event.ydata,'Begin',rotation=270)
                else:
                    self.beg.set_xdata(event.xdata)
                    self.t_beg.set_position((event.xdata,event.ydata))
                self.beg_x = event.xdata
            elif(event.button == MouseButton.RIGHT and (self.beg_x == None or self.beg_x <= event.xdata)):
                if(self.end == None):
                    self.end = self.axs1.axvline(x=event.xdata, color='k', linestyle='--')
                    self.t_end = self.axs1.text(event.xdata,event.ydata,'End',rotation=270)
                else:
                    self.end.set_xdata(event.xdata)
                    self.t_end.set_position((event.xdata,event.ydata))
                self.end_x = event.xdata
            self.draw_figure(self.canvas, self.figure)

    def clear_axs1(self):
        self.axs1.cla()
        self.beg = None
        self.end = None

    def twinx_canvas(self,x,x_label,y,y_label,colors='r',t=None,t_label='Time'):
        """Plot two variables in different y axis
        
        Parameters
        ----------
        x : `pandas.Series`
           First time series
        x_label : `str`
            Name of the first time series (will appear on axis)
        y : `List[pandas.Series]`
           Secondary time series
        y_label : `List[str]`
            Name of the secondary time series (will appear on axis)
        colors : `List[str], optional
            Names of the colors to use for each variable (same as matplotlib names). Default: 'r'
        t : iterable, optional
            Values for the x axis of the plot. Default: None (uses series index as x)
        t_label : `str`
            Name of the x axis. Default: 'Time'
        """
        self.clear_axs1()

        if(self.ax3 != None):
            self.ax3.remove()

        self.ax3 = self.axs1.twinx()

        self.row = x_label

        if(t==None):
            line, = self.axs1.plot(x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)
        else:
            line, = self.axs1.plot(t,x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)

        self.times = line.get_xdata()

        if(t==None):
            for signal, color in zip(y,colors):
                self.ax3.plot(signal,color=color,label=y_label)
            self.ax3.set_ylabel(y_label, rotation=-90,labelpad=7)
        else:
            for signal, color in zip(y,colors):
                self.ax3.plot(t,signal,color=color,label=y_label)
            self.ax3.set_ylabel(y_label, rotation=-90,labelpad=7)

        k = int(len(self.axs1.xaxis.get_ticklabels())/5)

        self.axs1.yaxis.label.set_color('blue')
        self.ax3.yaxis.label.set_color(colors[0])

        for n, label in enumerate(self.axs1.xaxis.get_ticklabels()):
            if n % k != 0:
                label.set_visible(False)

        self.draw_figure(self.canvas, self.figure)

    def update_canvas(self,x,x_label,t=None,t_label='Time'):
        """Plot variable 
        
        Parameters
        ----------
        x : `pandas.Series`
           Time series
        x_label : `str`
            Name of the first time series (will appear on axis)
        t : iterable, optional
            Values for the x axis of the plot. Default: None (uses series index as x)
        t_label : `str`
            Name of the x axis. Default: 'Time'
        """
        self.row = x_label

        self.clear_axs1()

        if(self.ax3!=None):
            self.ax3.remove()
            self.ax3 = None

        if(t==None):
            line, = self.axs1.plot(x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)
        else:
            line, = self.axs1.plot(t,x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)

        self.times = line.get_xdata()
        k = int(len(self.axs1.xaxis.get_ticklabels())/5)

        for n, label in enumerate(self.axs1.xaxis.get_ticklabels()):
            if n % k != 0:
                label.set_visible(False)

        self.axs1.yaxis.label.set_color('blue')
        self.draw_figure(self.canvas, self.figure)
