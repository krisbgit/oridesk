import sys
import re
import os
import shapely
import shapely.geometry
from PySide2 import QtCore
from PySide2 import QtUiTools
from PySide2 import QtWidgets
from PySide2 import QtGui
from shiboken2 import wrapInstance
import maya.cmds as cmds
import maya.api.OpenMaya as om
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

class Oridesk(QtWidgets.QDialog):
    def __init__(self, title, ui_file, parent=maya_main_window()):
        super(Oridesk, self).__init__(parent)
        
        self.setFixedSize(600, 650)
        self.setWindowTitle(title)
        self.init_ui(ui_file)
        self.create_layout()
        self.create_connections()

    def create_connections(self):
        self.ui.actionOpen_Pattern.triggered.connect(self.load_pattern_in_tab)
        self.ui.actionCreate_Paper.triggered.connect(self.create_plane_paper_menu)

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

    def load_pattern_in_tab(self):
        self.set_crease_pattern_file()
        self.pattern_widget = CreasePattern(crease_pattern=self.crease_pattern)
        self.ui.tabWidget.insertTab(0, self.pattern_widget, "2D Pattern")
        self.ui.actionCreate_Paper.setEnabled(True)

    def set_crease_pattern_file(self):
        file = self.open_file_search()[0] 
        self.crease_pattern = self.get_pattern_from_file(file=file)

    def get_pattern_from_file(self, file):
        opened_file = open(file, "r")
        file_lines = opened_file.readlines()

        svg_lines = []
        for line in file_lines:
            if line.startswith("<line"):
                line_data = re.findall('".*?"', line)
                new_line = {
                    "line":shapely.geometry.LineString(
                        [(float(re.sub('"', '', line_data[0])), float(re.sub('"', '', line_data[1]))),
                        (float(re.sub('"', '', line_data[2])), float(re.sub('"', '', line_data[3]))),
                        ]),
                    "stroke":re.sub('"', '', line_data[4])
                }
                svg_lines.append(new_line)
        return svg_lines

    def open_file_search(self):
        file_dialog = QtWidgets.QFileDialog(self)
        file = file_dialog.getOpenFileName(
            caption="Open Crease Pattern File",
            directory="",
            filter="SVG Files (*.svg)",
            initial_filter="SVG Files (*.svg)"
        )
        return file

    def create_plane_paper_menu(self):
        paper_menu = PaperMenu("paper_options.ui", ui_parent=self)

    def create_plane_paper(self, size, name):
        self.paper_object = self.pattern_widget.create_polygon_plane(size, name)
        # self.paper_object = cmds.polyPlane(name=name, sy=1, sx=1, w=size, h=size)

class PaperMenu(QtWidgets.QDialog):
    def __init__(self, ui_file, ui_parent, parent=maya_main_window()):
        super().__init__(parent)

        self.setFixedSize(300, 120)
        self.parent = ui_parent
        self.init_ui(ui_file)
        self.create_layout()
        self.create_connections()
        self.setModal(True)
        self.show()

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

    def create_connections(self):
        self.ui.createButton.clicked.connect(self.create_paper)
    
    def create_paper(self):
        self.parent.create_plane_paper(size=self.ui.sizeBox.value(), name=self.ui.name.text())
        self.close()

class Polygon():
    def __init__(self, first_line, second_line, third_line):
        self.first_line = first_line
        self.second_line = second_line
        self.third_line = third_line
    
    def __hash__(self):
        return hash((self.first_line, self.second_line, self.third_line))
    
    def __eq__(self, other):
        return self.__hash__() == other.__hash__()

class Line():
    def __init__(self, idx, line, points_x, points_y):
        self.idx = idx
        self.line = line
        self.color, self.is_margin = self.get_stroke_color()
        self.points_x, self.points_y = points_x, points_y
        self.size = (-1, 1)
        self.normalize_line_vertices()

    def __lt__(self, other):
        return self.idx < other.idx
    
    def __gt__(self, other):
        return self.idx > other.idx
    
    def __hash__(self):
        return hash(self.idx)

    def get_stroke_color(self):
        if self.line.get("stroke") == "black":
            return (0.0, 0.0, 0.0), True
        if self.line.get("stroke") == "blue":
            return (0.0, 0.0, 1.0), False
        if self.line.get("stroke") == "red":
            return (1.0, 0.0, 0.0), False
        
    def normalize_line_vertices(self):
        line_data = self.line.get("line")
        coordinates = shapely.get_coordinates(line_data).tolist()
        start_point_x = self.normalize_value(value=coordinates[0][0], min_points=min(self.points_x), max_points=max(self.points_x))
        start_point_y = self.normalize_value(value=coordinates[0][1], min_points=min(self.points_y), max_points=max(self.points_y))

        end_point_x = self.normalize_value(value=coordinates[1][0], min_points=min(self.points_x), max_points=max(self.points_x))
        end_point_y = self.normalize_value(value=coordinates[1][1], min_points=min(self.points_y), max_points=max(self.points_y))

        self.start_point = (start_point_x, start_point_y)
        self.end_point = (end_point_x, end_point_y)
    
    def normalize_value(self, value, min_points, max_points):
        return (self.size[1] - self.size[0]) * ((value - min_points)/(max_points - min_points)) + self.size[0]

class CreasePattern(QtWidgets.QOpenGLWidget):
    def __init__(self, crease_pattern, parent=None):
        self.parent = parent
        self.threshold = 0
        self.crease_pattern = crease_pattern
        self.pattern_margin_lines = []
        self.points_x, self.points_y = self.get_all_vertices()
        self.lines = self.get_line_data()
        
        QtWidgets.QOpenGLWidget.__init__(self, parent)

    def check_shared_value(self, line, edge):
        if edge.start_point == line:
            return "start"
        elif edge.end_point == line:
            return "end"

    def create_polygon_plane(self, size=1, name=""):
        origami_paper = om.MFnMesh()
        self.polygons = set()
        polygon_vertices = []
        polygon_connects = []

        for line in self.lines:
            # line.start_point / line.end_point
            # 1. Get lines that share the start point
            lines_from_start = [edge for edge in self.lines if line.start_point in (edge.start_point, edge.end_point)]
            lines_from_end = [edge for edge in self.lines if line.end_point in (edge.start_point, edge.end_point)]
            lines_from_start.remove(line)
            lines_from_end.remove(line)

            for first_connection in lines_from_start:
                shared_value = self.check_shared_value(line.start_point, first_connection)
                if shared_value == "start":
                    second_connections = [edge for edge in lines_from_end if first_connection.end_point in (edge.start_point, edge.end_point)]
                    lines_from_start.remove(first_connection)
                    second_connections += [edge for edge in lines_from_start if first_connection.end_point in (edge.start_point, edge.end_point)]
                    lines_from_start.append(first_connection)
                    if second_connections:
                        print(len(second_connections), second_connections[0])
                    first_point = first_connection.end_point

                elif shared_value == "end":
                    second_connections = [edge for edge in lines_from_end if first_connection.start_point in (edge.start_point, edge.end_point)]
                    lines_from_start.remove(first_connection)
                    second_connections += [edge for edge in lines_from_start if first_connection.start_point in (edge.start_point, edge.end_point)]
                    lines_from_start.append(first_connection)
                    if second_connections:
                        print(len(second_connections), second_connections[0])
                    first_point = first_connection.start_point

                if second_connections:
                    for second_connection in second_connections:
                        polygon = sorted([line, first_connection, second_connection])
                        poly = Polygon(polygon[0], polygon[1], polygon[2])
                        if poly not in self.polygons:
                            
                            self.polygons.add(poly)
                            vertices = [(line.start_point[0], line.start_point[1]),
                                        (first_point[0], first_point[1]),
                                        (line.end_point[0], line.end_point[1])
                                        ]
                            print(vertices)
                            for vertex in vertices:
                                if vertex in polygon_vertices:
                                    #print("Found at ", polygon_vertices.index(vertex))
                                    polygon_connects.append(polygon_vertices.index(vertex))
                                else:
                                    polygon_vertices.append(vertex)
                                    polygon_connects.append(polygon_vertices.index(vertex))
            
            for first_connection in lines_from_end:
                shared_value = self.check_shared_value(line.end_point, first_connection)
                if shared_value == "start":
                    second_connections = [edge for edge in lines_from_start if first_connection.end_point in (edge.start_point, edge.end_point)]
                    lines_from_end.remove(first_connection)
                    second_connections += [edge for edge in lines_from_end if first_connection.end_point in (edge.start_point, edge.end_point)]
                    lines_from_end.append(first_connection)
                    if second_connections:
                        print(len(second_connections), second_connections[0])
                    first_point = first_connection.end_point

                elif shared_value == "end":
                    second_connections = [edge for edge in lines_from_start if first_connection.start_point in (edge.start_point, edge.end_point)]
                    lines_from_end.remove(first_connection)
                    second_connections += [edge for edge in lines_from_end if first_connection.start_point in (edge.start_point, edge.end_point)]
                    lines_from_end.append(first_connection)
                    if second_connections:
                        print(len(second_connections), second_connections[0])
                    first_point = first_connection.start_point

                if second_connections:
                    for second_connection in second_connections:
                        polygon = sorted([line, first_connection, second_connection])
                        poly = Polygon(polygon[0], polygon[1], polygon[2])
                        if poly not in self.polygons:
                            
                            self.polygons.add(poly)
                            vertices = [(line.end_point[0], line.end_point[1]),
                                        (first_point[0], first_point[1]),
                                        (line.start_point[0], line.start_point[1])
                                        ]
                            print(vertices)
                            for vertex in vertices:
                                if vertex in polygon_vertices:
                                    #print("Found at ", polygon_vertices.index(vertex))
                                    polygon_connects.append(polygon_vertices.index(vertex))
                                else:
                                    polygon_vertices.append(vertex)
                                    polygon_connects.append(polygon_vertices.index(vertex))

        polygon_count = [3 for polygon in self.polygons]
        polygon_points = []
        for vertex in polygon_vertices:
            point = om.MPoint(vertex)
            polygon_points.append(point)

        origami_paper.create(polygon_points, polygon_count, polygon_connects)

        return origami_paper

    def wheelEvent(self, event):
        super(CreasePattern, self).wheelEvent(event)
        zoom_value = 1 if event.angleDelta().y() > 0 else -1
        self.zoom_pattern(zoom_value*0.05)
        self.update()

    def zoom_pattern(self, zoom_value):
        for line in self.lines:
            line.size = (line.size[0] - zoom_value, line.size[1] + zoom_value)
            line.normalize_line_vertices()

    def initializeGL(self):
        gl.glClearColor(1, 1, 1, 1)

    def paintGL(self):
        gl.glLineWidth(3)
        gl.glBegin(gl.GL_LINES) # Begins draw
        self.draw_pattern()
        gl.glEnd() # Ends draw
    
    def get_line_data(self):
        line_objects = []
        for idx, line in enumerate(self.crease_pattern):
            line_object = Line(idx=idx, line=line, points_x=self.points_x, points_y=self.points_y)
            if line_object.is_margin:
                self.pattern_margin_lines.append(line_object)
            line_objects.append(line_object)
        return line_objects

    def get_all_vertices(self):
        points_x = []
        points_y = []
        for line in self.crease_pattern:
            shapely_line = line.get("line")
            points = shapely.get_coordinates(shapely_line).tolist()
            print(points)
            points_x.extend((points[0][0], points[1][0]))
            points_y.extend((points[0][1], points[1][1]))
        return points_x, points_y

    def draw_pattern(self):
        for line in self.lines:
            gl.glColor3f(line.color[0], line.color[1], line.color[2])
            gl.glVertex2f(line.start_point[0], line.start_point[1])
            gl.glVertex2f(line.end_point[0], line.end_point[1])

if __name__ == "__main__":
    oridesk_ui = Oridesk(title="Oridesk", ui_file="mainwindow.ui")
    oridesk_ui.show()
    try:
        oridesk_ui.close() # pylint: disable=E0601
        oridesk_ui.deleteLater()
    except:
        pass
