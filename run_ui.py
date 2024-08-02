from .ui.main_window import MaterialxImporterUI
import hou

win = None

def run():

    global win
    if not win:
        win = MaterialxImporterUI(parent=hou.qt.mainWindow())
        win.show()
