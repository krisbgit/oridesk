# import maya.cmds as cmds
import re
import xml.etree.ElementTree as etree

def get_svg_text(file):
    opened_file = open(file, "r")
    file_lines = opened_file.readlines()

    svg_lines = []
    for line in file_lines:
        if line.startswith("<line"):
            line_data = re.findall('".*?"', line)
            new_line = {
                "start_point":(float(re.sub('"', '', line_data[0])), 
                               float(re.sub('"', '', line_data[1]))),
                "end_point":(float(re.sub('"', '', line_data[2])), 
                            float(re.sub('"', '', line_data[3]))),
                "stroke":re.sub('"', '', line_data[4])
            }
            svg_lines.append(new_line)
    return svg_lines