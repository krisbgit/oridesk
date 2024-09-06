import sys
import os
import svg_reader

from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui
from shiboken2 import wrapInstance

import maya.cmds as cmds
import maya.OpenMayaUI as omui

import OpenGL.GL as gl
from OpenGL import GLU 

def maya_main_window():
    """
    Return the Maya main window widget as a Python object
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if sys.version_info.major >= 3:
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    else:
        return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

class CreasePattern(QtWidgets.QOpenGLWidget):

    def __init__(self, crease_pattern, parent=None):
        self.parent = parent
        self.crease_pattern = crease_pattern
        self.points = self.get_point_data()
        self.ratio, self.shift = self.get_point_range()
        QtWidgets.QOpenGLWidget.__init__(self, parent)

    def get_line_data(self):
        for line in self.crease_pattern:
            color = self.get_stroke_color(line)
            start_point = (self.get_normalized_value(line.get("start_point")[0]), 
                           self.get_normalized_value(line.get("start_point")[1]))
            end_point = (self.get_normalized_value(line.get("end_point")[0]), 
                           self.get_normalized_value(line.get("end_point")[1]))
            try:
                gl.glColor3f(color[0], color[1], color[2])
            except:
                pass
            gl.glVertex2f(start_point[0], start_point[1])
            gl.glVertex2f(end_point[0], end_point[1])

    def get_stroke_color(self, line):
        if line.get("stroke") == "black":
            return (0.0, 0.0, 0.0)
        if line.get("stroke") == "blue":
            return (0.0, 0.0, 1.0)
        if line.get("stroke") == "red":
            return (1.0, 0.0, 0.0)

    def get_point_data(self):
        points = []
        for line in self.crease_pattern:
            start_point = line.get("start_point")
            end_point = line.get("end_point")
            points.extend((start_point[0], start_point[1], end_point[0], end_point[1]))
        return points
    
    def get_point_range(self):
        ratio = 2/(max(self.points) - min(self.points))
        shift = (max(self.points) + min(self.points))/2
        return ratio, shift

    def get_normalized_value(self, value):
        return (value - self.shift)*self.ratio

    def paintGL(self):
        vertices = ((10.0, 10.0), (50.0, 40.0), (30.0, 35.0))
        gl.glClearColor(1, 1, 1, 0.5)
        gl.glBegin(gl.GL_LINES) # Begins draw
        gl.glLineWidth(5)
        # gl.glVertex2f(-1.0, -1.0)
        # gl.glVertex2f(1.0, 1.0)
        self.get_line_data()
        gl.glEnd() # Ends draw

class Oridesk(QtWidgets.QDialog):

    def __init__(self, title, ui_file, parent=maya_main_window()):
        super(Oridesk, self).__init__(parent)

        self.setWindowTitle(title)
        self.init_ui(ui_file)
        self.create_layout()
        self.create_connections()

    def create_connections(self):
        self.ui.file_button.clicked.connect(self.set_crease_pattern_file)
        

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
    
    def set_crease_pattern_file(self):
        self.crease_pattern_file = self.open_file_search()[0]
        self.pattern_widget = CreasePattern(crease_pattern=
                                            svg_reader.get_svg_text(
                                                self.crease_pattern_file))
        self.ui.tabWidget.addTab(self.pattern_widget, "2D Pattern")
        self.ui.tabWidget.addTab(QtWidgets.QWidget(), "3D Result")

    def open_file_search(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file = file_dialog.getOpenFileName(
            caption="Open Crease Pattern File",
            directory="",
            filter="SVG Files (*.svg)",
            initial_filter="SVG Files (*.svg)"
        )
        return file
        
if __name__ == "__main__":
    oridesk_ui = Oridesk(title="Oridesk", ui_file="main.ui")
    oridesk_ui.show()
    try:
        oridesk_ui.close() # pylint: disable=E0601
        oridesk_ui.deleteLater()
    except:
        pass
