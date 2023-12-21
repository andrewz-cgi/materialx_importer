from .ui.matx_main_ui import MaterialxImporterUI
import hou

def run():

    win = MaterialxImporterUI(parent=hou.qt.mainWindow())
    win.show()
