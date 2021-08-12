import PySimpleGUI as sg
import os.path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.signal as sig
import matplotlib
from Correlation import *

matplotlib.use('TkAgg')

class App():

    def __init__(self, layout, name="Correlations", CANVAS_NAME='-CANVAS-',
            DATASET='-DATASET-', MAIN_VAR='-MAIN VAR-', OTHER_VAR='-OTHER VARS-',
            CORRELATE='Correlate', PLOT='Plot', CORRELATION_SEL='-CORR-'):
        self.window = sg.Window(name, layout).Finalize()
        self.window.Maximize()
        self.CANVAS_NAME = CANVAS_NAME
        self.DATASET = DATASET
        self.MAIN_VAR = MAIN_VAR
        self.OTHER_VARS = OTHER_VAR
        self.CORRELATE=CORRELATE
        self.PLOT = PLOT
        self.CORR = CORRELATION_SEL

    def init_canvas(self, FIGSIZE_X=8,FIGSIZE_Y=8):
        self.fig, (self.axs1,self.axs2) = plt.subplots(2,figsize=(FIGSIZE_X,FIGSIZE_Y))
        self.ax3 = self.axs2.twinx()
        self.figure_canvas_agg = FigureCanvasTkAgg(self.fig, self.window[self.CANVAS_NAME].TKCanvas)
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

    def update_canvas(self, x,y,x_label,y_label,t=None,t_label='Time'):
        self.row = x_label
        self.axs1.cla()
        self.axs2.cla()
        self.ax3.cla()

        self.axs1.scatter(x,y)
        self.axs1.set_xlabel(x_label)
        self.axs1.set_ylabel(y_label)
        self.axs1.set_title(x_label+" X "+ y_label)

        if(t==None):
            self.ax3 = self.axs2.twinx()
            plt1,= self.axs2.plot(x)
            plt2,= self.ax3.plot(y,color='r')
            self.ax3.set_ylabel(y_label, rotation=-90)
            self.axs2.set_ylabel(x_label)
            self.axs2.set_xlabel(t_label)
            self.axs2.legend([plt1,plt2],[x_label,y_label])
            self.axs2.set_title(x_label+" and "+y_label+" X "+t_label)
        else:
            plt1,= self.axs2.plot(t,x)
            self.ax3 = self.axs2.twinx()
            plt2,= self.ax3.plot(t,y,color='r')
            self.ax3.set_ylabel(y_label, rotation=-90)
            self.axs2.set_ylabel(x_label)
            self.axs2.set_xlabel(t_label)
            self.axs2.legend([plt1,plt2],[x_label,y_label])
            self.axs2.set_title(x_label+ " and "+ y_label+" X " +t_label)

        self.fig.tight_layout(pad=3.0)
        self.window[self.CANVAS_NAME].TKCanvas.delete('all')
        self.figure_canvas_agg.draw()

    def iteration(self):

        event, values = self.window.read()
        
        if event == sg.WIN_CLOSED:
            return 0

        if event == self.DATASET:
            self.dataset = Correlations(values[self.DATASET])

            self.window.Element(self.MAIN_VAR).Update(values=self.dataset.get_columns())
            self.window.Element(self.OTHER_VARS).Update(values=self.dataset.get_columns())

        elif event == self.CORRELATE:
            try:
                idxs = self.window[self.OTHER_VARS].get_indexes()
                all_items = self.window[self.OTHER_VARS].get_list_values()
                self.other_variables = [all_items[index] for index in idxs]

                idxs = self.window[self.MAIN_VAR].get_indexes()
                all_items = self.window[self.MAIN_VAR].get_list_values()
                self.main_variable = all_items[idxs[0]]
               
                delays, corrs = self.dataset.correlate(self.main_variable, self.other_variables)
                corrs, delays, names = zip(*sorted(zip(corrs, delays, self.other_variables),reverse=True))

                new_tree = sg.TreeData()

                for i,j in enumerate(names):
                    new_tree.Insert("",j,j,[corrs[i],delays[i]])

                self.window.Element(self.CORR).Update(values=new_tree)
            except:
                pass

        elif event == self.PLOT:
            #try:
            x_label = self.main_variable
            x = self.dataset.get_series(x_label)
            y_label = self.window.Element(self.CORR).SelectedRows[0]
            y = self.dataset.get_series(y_label)

            self.update_canvas(x,y,x_label,y_label,t=None,t_label='Time')
            #except:
            #    pass

        return 1

    def quit(self):
        self.window.close()
