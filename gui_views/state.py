
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

from graphic_scene import *
from connection import *
import sys, random, os

"""operations and their inverse:
    #create -> delete
    #delete -> create
    #copy -> delete
    #draw -> erase
    move -> move back
        TODO: move out of object (hard?) #move_child
        TODO: move general (easy?) #move_any
    TODO: change attribute -> undo change (hard?) #move_attr"""

class History():
    def __init__(self):
        self.head = None

    def push(self, sym_object, operation):
        new_node = HistoryNode(sym_object, operation)
        new_node.next = self.head
        self.head = new_node

    def pop(self):
        popped_node = self.head
        self.head = popped_node.next
        return popped_node

class HistoryNode():
    def __init__(self, sym_object, operation):
        self.sym_object = sym_object
        self.operation = operation
        self.next = None

class State():
    def __init__(self, instances, catalog):
        self.drag_state = True
        self.draw_wire_state = False
        self.sym_objects = {} # Map name to actual symobject (has coords)
        self.selected_sym_objects = []
        self.line_drawer = None
        self.scene = None
        self.mainWindow = None
        self.instances = instances
        self.catalog = catalog
        self.buttonView = None
        self.fileName = None
        self.copyState = False
        self.copied_objects = []
        self.history = History()
        self.mostRecentSaved = True

    # sets objects in scene as draggable or not draggable based on drag_state
    def setDragState(self):
        for object in self.sym_objects.values():
            object.setFlag(QGraphicsItem.ItemIsMovable, self.drag_state)

    # draws each line in lines using the QPen p
    def drawLines(self, p):
        for object in self.sym_objects.values():
            for name, connection in object.ui_connections.items():
                if name[0] == "parent": #draw line once
                    self.drawConnection(p, connection)


    def drawConnection(self, p, connection):
        if connection.line:
            self.scene.removeItem(connection.line)
        connection.line = self.scene.addLine(connection.parent_endpoint.x(), \
        connection.parent_endpoint.y(), connection.child_endpoint.x(), \
        connection.child_endpoint.y(), p)

        connection.line.setZValue(1000)

    def removeHighlight(self):
        if len(self.selected_sym_objects):
            for sym_object in self.selected_sym_objects:
                sym_object.rect.setBrush(QColor("White"))
                sym_object.delete_button.hide()


#finds the gem5 path
def get_path():
    gem5_parent_dir = os.getenv("GEM5_HOME")
    #if parent dir not explicitly set, procure it from executable path
    if not gem5_parent_dir:
        gem5_parent_dir = sys.executable.split("gem5")[0]
    for root, dirs, files in os.walk(gem5_parent_dir, topdown=False):
        for name in dirs:
            abs_path = os.path.join(root, name)
            if abs_path.endswith("gem5/configs"):
                os.environ['gem5_path'] = abs_path
