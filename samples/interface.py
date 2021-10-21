import PySimpleGUI as sg
import layout as layout
import os.path
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import scipy.signal as sig
import matplotlib
from dataset import Dataset
from datetime import *
from plots import Plots
import pytz
import webbrowser
import threading
import requests
import constants as cte
import causations as cause
from requests.packages.urllib3.exceptions import InsecureRequestWarning

class Interface():
    """
    Class responsible for all interfaces with the UI,
    managing the opened windows and reading and writting
    to the UI.
    """
    def __init__(self):
        self.windows = []


    def create_window(self, name,layout,**opt):
        """Create window with the given specifications

        Parameters
        ----------
        name : str
            Window name
        layout : List[List[Element]]
            Layout for the window
        **opt : kwargs
            Optional parameters (icon, resizable, maximizer, etc)

        Returns
        -------
        int:
            Window identifier for reading and writting from and to this specific window 
        """
        img = opt.get('icon', None)
        resizable = opt.get('resizable', True)
        maximize = opt.get('maximize', False)

        window = sg.Window(name, layout, resizable=resizable, icon=img).Finalize()
        if(maximize):
            window.Maximize()
        self.windows.append(window)

        return len(self.windows)-1

    def get_window(index=0):
        """ Get window

        Parameters
        ----------
        index : int, optional
            Window identifier (default is 0, meaning the first window created)

        Returns
        -------
        sg.Window
            Window object
        """

        return self.windows[index]

    def create_tree(self, values, index=None):
        """ Create tree structure to display

        Parameters
        ----------
        values : iterable
            iterable with the element for each position on the tree
        index : iterable, optional
            Indexes to use instead of the position of the element in values

        Returns
        -------
        sg.Tree
            Tree with the given data
        """
        new_tree = sg.TreeData()
        
        if(index==None):
            index = range(len(values))

        for i,j in enumerate(index):
            new_tree.Insert("",j,j,values[i])

        return new_tree

    def update_tree(self, data, element,index=0):
        """Updates the tree on the screen

        Parameters
        ----------
        data : iterable
            Data representing the tree
        element : str
            Key for the tree element on the window
        index : int, optional
            Identifier for which window to update
        """
        
        self.windows[index].Element(element).Update(values=self.create_tree(data))

    def update_element(self, data, element, arg_name='value', index=0):
        """Updates the element on the screen

        Parameters
        ----------
        data : Object
            Data to be updated
        element : str
            Key for the element on the window
        arg_name : str, optional
            Name of the argument in the Update method
        index : int, optional
            Identifier for which window to update
        """
        if(arg_name=='value'):
            self.windows[index].Element(element).Update(value=data)
        elif(arg_name==''):
            self.windows[index].Element(element).Update(data)


    def get_selected_row(self, element, index=0):
        """Get selected row from tree

        Parameters
        ----------
        element : str
            Key for the tree element on the window
        index : int, optional
            Identifier for which window to get from
        """

        selected_row = self.windows[index].Element(element).SelectedRows[0]
        selected_row = self.windows[index].Element(element).TreeData.tree_dict[selected_row].values
        selected_row = selected_row[0] if isinstance(selected_row, list) else selected_row

        return selected_row

    def write_event(self, name, params, index=0): 
        """Get selected row from tree

        Parameters
        ----------
        name : str
            Key for the event name
        params : Object
            Parameters to pass to the event
        index : int, optional
            Identifier for which window to create from
        """
        
        self.windows[index].write_event_value(name, params)

    def start_loading(self, timeout=100):
        """ Start displaying loading screen

        Parameters
        ----------
        timeout : int
            Timeout between frames in ms
        """
        sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, background_color='white', transparent_color='white', time_between_frames=timeout)
       
    def popup(self, message):
        """ Display popup with message
        
        Parameters
        ----------
        message : str
            Message to be displayed
        """
        sg.Popup(message)

    def stop_loading(self):
        """Stop loading animation"""
        sg.popup_animated(None)

    def read_events(self, timeout=None, index=0):
        """ Read events and values from window
        
        Parameters
        ----------
        timeout : int, optional
            Timeout to wait for event in ms (default: None)
        index : index
            Identifier for the target window (default: 0)

        Returns
        -------
        (events, values)
            Events and values of the given window
        """
        return self.windows[index].read(timeout=timeout)

    def get_window_size(self, index=0):
        return self.windows[index].size

    def get_canvas(self, element, index=0):
        return self.windows[index][element].TKCanvas

    def close(self, index=0):
        self.windows[index].close()
