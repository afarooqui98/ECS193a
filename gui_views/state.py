
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *

from graphic_scene import *
from connection import *
from wire import *

import sys, random, os

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
        self.mostRecentSaved = True
        self.zoom = 1
        self.importedSymObjects = {}

        self.object_clicked = 0
    # sets objects in scene as draggable or not draggable based on drag_state
    def setDragState(self):
        for object in self.sym_objects.values():
            object.setFlag(QGraphicsItem.ItemIsMovable, self.drag_state)

    # draws each line in lines using the QPen p
    def drawLines(self, p):
        for object in self.sym_objects.values():
            for name, connection in object.ui_connections.items():
                if name[0] == "parent": #draw line once
                    self.drawConnection(p, connection, name, object.name)


    def drawConnection(self, p, connection, parent_key, parent_name):
        # remove old line if it exists
        if connection.line:
            self.scene.removeItem(connection.line)

        # instantiate a new line with connection coordinates
        line = QLineF(connection.parent_endpoint.x(), \
                connection.parent_endpoint.y(), connection.child_endpoint.x(), \
                    connection.child_endpoint.y())

        # create a new wire object so it can register mouse clicks
        wire = Wire(line, p, self)

        # add the wire to the scene
        self.scene.addItem(wire)

        connection.line = wire

        # set wire parameters that are needed for deletion
        wire.parent_key = parent_key
        wire.child_key = ("child", parent_name, parent_key[3], parent_key[2])

        connection.line.setZValue(1000)

    def removeHighlight(self):
        if len(self.selected_sym_objects):
            for sym_object in self.selected_sym_objects:
                sym_object.rect.setBrush(QColor("White"))
                sym_object.delete_button.hide()

    def addObjectToCatalog(self, object, object_name):
        """add the passed in imported object to the catalog"""
        self.mainWindow.addImportedObjectToCatalog(object, object_name)

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
