import sys
import os
import main

from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)
    
class Oridesk(QtWidgets.QDialog):

    def __init__(self, title, ui_file, parent=maya_main_window()):
        super(Oridesk, self).__init__(parent)

        self.setWindowTitle(title)
        self.init_ui(ui_file)
        self.create_layout()
        self.create_connections()

    def init_ui(self, ui_file):
        file = QtCore.QFile(os.path.join(os.path.dirname(__file__), ui_file))
        file.open(QtCore.QFile.ReadOnly)
        loader = QtUiTools.QUiLoader()
        self.ui = loader.load(file, parentWidget=None)
        file.close()

    def create_layout(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.ui)

    def remove_widget(self):
        self.hide()


if __name__ == "__main__":
    designer_ui = Oridesk(title="SMT", ui_file="SMT.ui")
    designer_ui.show()
    try:
        designer_ui.close() # pylint: disable=E0601
        designer_ui.deleteLater()
    except:
        pass
