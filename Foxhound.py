import os
import sys
sys.path.insert(0, os.path.abspath('./samples'))

import PySimpleGUI as sg
from application_logic import App


app = App()

while app.iteration():
    pass

app.quit()
