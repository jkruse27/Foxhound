import PySimpleGUI as sg
from Application_Logic import *
from Layout import *

FIGSIZE_X=16
FIGSIZE_Y=4

layout = Layout()

# Create the window
app = App(layout.get_layout(),FIGSIZE_X,FIGSIZE_Y)

# Create an event loop
while app.iteration():
    pass

app.quit()
