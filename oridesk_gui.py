import sys
import re
import os
import itertools
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
        self.current_widget = self.ui.frame

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

        self.ui.verticalLayout_3.replaceWidget(self.current_widget, self.pattern_widget)
        self.current_widget = self.pattern_widget

        self.ui.actionCreate_Paper.setEnabled(True)
        self.ui.tabWidget.setTabText(self.ui.tabWidget.currentIndex(), self.file_name)
        self.ui.lines_label.setText(str(len(self.pattern_widget.lines)))
        self.ui.points_label.setText(str(len(self.pattern_widget.points)))

    def set_crease_pattern_file(self):
        file = self.open_file_search()[0]
        self.file_name = os.path.basename(os.path.normpath(file))
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
        self.orig_start_point, self.orig_end_point = self.get_coordinates()
        self.normalize_line_vertices()

    def __lt__(self, other):
        return self.idx < other.idx
    
    def __gt__(self, other):
        return self.idx > other.idx
    
    def __hash__(self):
        return hash(self.idx)

    def get_coordinates(self):
        line_data = self.line.get("line")
        coordinates = shapely.get_coordinates(line_data).tolist()
        return (coordinates[0][0], coordinates[0][1]), (coordinates[1][0], coordinates[1][1])

    def get_stroke_color(self):
        if self.line.get("stroke") == "black":
            return (0.0, 0.0, 0.0), True
        if self.line.get("stroke") == "blue":
            return (0.0, 0.0, 1.0), False
        if self.line.get("stroke") == "red":
            return (1.0, 0.0, 0.0), False
        
    def normalize_line_vertices(self):

        start_point_x = self.normalize_value(value=self.orig_start_point[0], min_points=min(self.points_x), max_points=max(self.points_x))
        start_point_y = self.normalize_value(value=self.orig_start_point[1], min_points=min(self.points_y), max_points=max(self.points_y))

        end_point_x = self.normalize_value(value=self.orig_end_point[0], min_points=min(self.points_x), max_points=max(self.points_x))
        end_point_y = self.normalize_value(value=self.orig_end_point[1], min_points=min(self.points_y), max_points=max(self.points_y))

        self.start_point = (round(start_point_x, 10), round(start_point_y*-1, 10))
        self.end_point = (round(end_point_x, 10), round(end_point_y*-1, 10))
    
    def normalize_value(self, value, min_points, max_points):
        return (self.size[1] - self.size[0]) * ((value - min_points)/(max_points - min_points)) + self.size[0]

class CreasePattern(QtWidgets.QOpenGLWidget):
    def __init__(self, crease_pattern, parent=None):
        self.parent = parent
        self.threshold = 0
        self.crease_pattern = crease_pattern
        self.pattern_margin_lines = []
        self.points, self.points_x, self.points_y = self.get_all_vertices()
        self.lines = self.get_line_data()
        
        QtWidgets.QOpenGLWidget.__init__(self, parent)
        
    def check_line_intersection(self, first_line, other_line):
        if first_line.intersects(other_line):
            return True
        else:
            return False

    def find_points_connected_with(self, point, line_list):
        points_connected = []
        for line in line_list:
            if point == line.orig_end_point:
                points_connected.append(line.orig_start_point)
            if point == line.orig_start_point:
                points_connected.append(line.orig_end_point)
        return points_connected
    
    def find_line_by_points(self, first_point, second_point):
        for line in self.lines:
            if line.orig_start_point == first_point:
                if line.orig_end_point == second_point:
                    return line
            elif line.orig_end_point == first_point:
                if line.orig_start_point == second_point:
                    return line
        return False
    
    def get_normalized_polygon_vertices(self, lines):
        points = set()
        for line in lines:
            points.add(line.start_point)
            points.add(line.end_point)
        return list(points)

    def find_tris(self):
        polygons = []
        all_combinations = []
        false_combinations = []
        true_combinations = []
        for point in self.points:
            points_connected = self.find_points_connected_with(point, self.lines)
            combinations = list(itertools.combinations(points_connected, 2))
            all_combinations += combinations
            for line in self.lines:
                if (line.orig_start_point, line.orig_end_point) in combinations or (line.orig_end_point, line.orig_start_point) in combinations:
                    if (line.orig_start_point, line.orig_end_point) in combinations:
                        true_combinations.append((line.orig_start_point, line.orig_end_point))

                    if (line.orig_end_point, line.orig_start_point) in combinations:
                        true_combinations.append((line.orig_end_point, line.orig_start_point))

                    first_line = self.find_line_by_points(point, line.orig_start_point)
                    second_line = self.find_line_by_points(point, line.orig_end_point)
                    third_line = self.find_line_by_points(line.orig_start_point, line.orig_end_point)
                    lines = sorted([first_line, second_line, third_line])
                    if lines not in polygons:
                        polygons.append(lines)

        for true_line in true_combinations:
            if true_line in all_combinations:
                coincidences = [all_combinations.index(line) for line in all_combinations if line == true_line]
                for idx in coincidences:
                    del all_combinations[idx]
        print(len(set(all_combinations)))
        return polygons, all_combinations
                    
    def create_polygon_plane(self, size=1, name=""):
        origami_paper = om.MFnMesh()
        self.polygons = set()
        polygon_vertices = []
        polygon_connects = []
        polygon_count = []

        tris, false_combinations = self.find_tris()
        for tri in tris:
            tri_vertices = self.get_normalized_polygon_vertices(tri)
            for vertex in tri_vertices:
                if vertex not in polygon_vertices:
                    polygon_vertices.append(vertex)
                polygon_connects.append(polygon_vertices.index(vertex))

            polygon_count.append(3)
        
        polygon_points = []
        for vertex in polygon_vertices:
            point = om.MPoint(vertex)
            polygon_points.append(point)

        origami_paper.create(polygon_points, polygon_count, polygon_connects)

            # other_lines = [shapely.LineString(shapely.get_coordinates(line.line.get("line")).tolist()) for line in self.lines]

            # for other_line in other_lines:
            #     intersections.append(self.check_line_intersection(first_line, other_line))
            
            # if True not in intersections:
            #     polygon_edges.add(false_line)

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
        gl.glEnd()# Ends draw
        gl.glPointSize(4)
        gl.glBegin(gl.GL_POINTS) # Begins draw
        self.draw_points()
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
        points = set()
        for line in self.crease_pattern:
            shapely_line = line.get("line")
            point = shapely.get_coordinates(shapely_line).tolist()
            points_x.extend((point[0][0], point[1][0]))
            points_y.extend((point[0][1], point[1][1]))
            for vtx in point:
                points.add((vtx[0], vtx[1]))

        return points, points_x, points_y

    def draw_pattern(self):
        for line in self.lines:
            gl.glColor3f(line.color[0], line.color[1], line.color[2])
            gl.glVertex2f(line.start_point[0], line.start_point[1])
            gl.glVertex2f(line.end_point[0], line.end_point[1])

        tris, false_combinations = self.find_tris()
        for tri in tris:
            gl.glColor3f(1.0, 0.0, 1.0)
            ##first line

            gl.glVertex2f(tri[0].start_point[0], tri[0].start_point[1])
            gl.glVertex2f(tri[0].end_point[0], tri[0].end_point[1])
            ##second line
            gl.glVertex2f(tri[1].start_point[0], tri[1].start_point[1])
            gl.glVertex2f(tri[1].end_point[0], tri[1].end_point[1])
            # ##third line
            gl.glVertex2f(tri[2].start_point[0], tri[2].start_point[1])
            gl.glVertex2f(tri[2].end_point[0], tri[2].end_point[1])
        
        for line in false_combinations:
            new_line = {"line":shapely.geometry.LineString([line[0], line[1]]),"stroke":"black"}
            new_line = Line(idx=0, line=new_line, points_x=self.points_x, points_y=self.points_y)
            gl.glColor3f(0.4, 0.0, 1.0)
            gl.glVertex2f(new_line.start_point[0], new_line.start_point[1])
            gl.glVertex2f(new_line.end_point[0], new_line.end_point[1])
    
    def draw_points(self):
        for line in self.lines:
            gl.glColor3f(0.2, 1.0, 0.2)
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
