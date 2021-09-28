import PySimpleGUI as sg
from Application_Logic import *
from Layout import *


layout = Layout()

FIGSIZE_X, FIGSIZE_Y = layout.get_fig_size()

# Create the window
app = App(layout.get_layout(),FIGSIZE_X,FIGSIZE_Y)

# Create an event loop
while app.iteration():
    pass

app.quit()
