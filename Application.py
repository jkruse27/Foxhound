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
            CORRELATE='Correlate', PLOT='Plot', CORRELATION_SEL='-CORR-', PVS='-PVS-',
            IN='-IN-', DATE_BEG='-DATE_BEG-', DATE_END='-DATE_END-', SELECT='Select'):
        self.window = sg.Window(name, layout).Finalize()
        self.window.Maximize()
        self.CANVAS_NAME = CANVAS_NAME
        self.DATASET = DATASET
        self.MAIN_VAR = MAIN_VAR
        self.OTHER_VARS = OTHER_VAR
        self.CORRELATE=CORRELATE
        self.PLOT = PLOT
        self.CORR = CORRELATION_SEL
        self.DATE_BEG = DATE_BEG
        self.DATE_END = DATE_END
        self.PVS = PVS
        self.IN = IN
        self.SELECT = SELECT


    def init_canvas(self, FIGSIZE_X=8,FIGSIZE_Y=8):
        self.fig, self.axs1 = plt.subplots(1,figsize=(FIGSIZE_X,FIGSIZE_Y))
        self.ax3 = self.axs1.twinx()
        self.figure_canvas_agg = FigureCanvasTkAgg(self.fig, self.window[self.CANVAS_NAME].TKCanvas)
        self.figure_canvas_agg.draw()
        self.figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)


    def twinx_canvas(self,y,y_label,t=None,t_label='Time'):
        self.ax3.cla()

        if(t==None):
            plt2,= self.ax3.plot(y,color='r',label=x_label)
            self.ax3.set_ylabel(y_label, rotation=-90)
        else:
            plt2,= self.ax3.plot(t,y,color='r',label=x_label)
            self.ax3.set_ylabel(y_label, rotation=-90)

        self.fig.tight_layout(pad=3.0)
        self.window[self.CANVAS_NAME].TKCanvas.delete('all')
        self.figure_canvas_agg.draw()


    def update_canvas(self,x,x_label,t=None,t_label='Time'):
        self.row = x_label
        self.axs1.cla()

        if(t==None):
            plt1,= self.axs1.plot(x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)
        else:
            plt1,= self.axs1.plot(t,x,label=x_label)
            self.axs1.set_ylabel(x_label)
            self.axs1.set_xlabel(t_label)

        self.fig.tight_layout(pad=3.0)
        self.window[self.CANVAS_NAME].TKCanvas.delete('all')
        self.figure_canvas_agg.draw()


    def create_tree(self, values, index=None):
        new_tree = sg.TreeData()
        
        if(index==None):
            index = range(len(values))

        for i,j in enumerate(index):
            new_tree.Insert("",j,j,values[i])

        return new_tree


    def iteration(self):

        event, values = self.window.read()
        
        if event == sg.WIN_CLOSED:
            return 0

        if event == self.DATASET:
            self.dataset = Correlations(values[self.DATASET])    
            self.window.Element(self.PVS).Update(values=self.create_tree(self.dataset.get_columns()))

        elif event == self.IN:
            self.window.Element(self.PVS).Update(
                    values=self.create_tree(self.dataset.get_columns(
                        regex=".*"+values[self.IN]+".*")
                        )
                    )

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
            x_label = self.main_variable
            x = self.dataset.get_series(x_label)
            y_label = self.window.Element(self.CORR).SelectedRows[0]
            y = self.dataset.get_series(y_label)

            self.update_canvas(x,x_label,t=None,t_label='Time')
            self.twinx_canvas(y,y_label,t=None,t_label='Time')

        elif event==self.PVS:
            selected_row = self.window.Element(self.PVS).SelectedRows[0]
            x_label = self.window.Element(self.PVS).TreeData.tree_dict[selected_row].values
            x = self.dataset.get_series(x_label)
            self.update_canvas(x,x_label,t=None,t_label='Time')
            self.main_variable = x_label

        elif event==self.SELECT:
            pass

        return 1

    def quit(self):
        self.window.close()
