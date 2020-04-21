from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from graphic_scene import *
from dialogs import *

import sys, random
import copy
from gui_views import state
import json
import logging


from m5_calls import *

class ButtonView(): #export, draw line, save and load self.stateuration buttons
    def __init__(self, layout, state, window):
        self.state = state

        # set up main menu - add tabs and connect each button to handler
        self.mainMenu = window.menuBar()
        self.buildMenuBar(self.mainMenu, window)


    def buildMenuBar(self, mainMenu, window):
        """build the main menu bar"""
        self.buildFileTab(mainMenu, window)
        self.buildEditTab(mainMenu, window)
        self.buildRunTab(mainMenu, window)
        self.buildToolsTab(mainMenu, window)
        self.buildDebugTab(mainMenu, window)


    def buildFileTab(self, mainMenu, window):
        """build the file tab"""
        newAction = QAction("New File", window)
        newAction.setShortcut("Ctrl+N")
        newAction.triggered.connect(self.new_button_pressed)
        saveAction = QAction("Save", window)
        saveAction.setShortcut("Ctrl+S")
        saveAction.triggered.connect(self.save_button_pressed)
        saveAsAction = QAction("Save As", window)
        saveAsAction.setShortcut("Ctrl+D")
        saveAsAction.triggered.connect(self.save_as_UI_button_pressed)
        openAction = QAction("Open", window)
        openAction.setShortcut("Ctrl+O")
        openAction.triggered.connect(self.openUI_button_pressed)

        fileMenu = mainMenu.addMenu('File')
        fileMenu.addAction(newAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(openAction)

    def buildEditTab(self, mainMenu, window):
        """build the edit tab"""
        copyAction = QAction("Copy", window)
        copyAction.setShortcut("Ctrl+C")
        copyAction.triggered.connect(self.copy_button_pressed)
        pasteAction = QAction("Paste", window)
        pasteAction.setShortcut("Ctrl+V")
        pasteAction.triggered.connect(self.paste_button_pressed)
        undoAction = QAction("Undo", window)
        undoAction.setShortcut("Ctrl+U")
        undoAction.triggered.connect(self.undo_button_pressed)

        editMenu = mainMenu.addMenu('Edit')
        editMenu.addAction(copyAction)
        editMenu.addAction(pasteAction)
        editMenu.addAction(undoAction)

    def buildRunTab(self, mainMenu, window):
        """build the run tab"""
        instantiateAction = QAction("Instantiate", window)
        instantiateAction.setShortcut("Ctrl+I")
        instantiateAction.triggered.connect(self.export_button_pressed)
        simulateAction = QAction("Simulate", window)
        simulateAction.setShortcut("Ctrl+R")
        simulateAction.triggered.connect(self.simulate_button_pressed)

        runMenu = mainMenu.addMenu('Run')
        runMenu.addAction(instantiateAction)
        runMenu.addAction(simulateAction)
        # Grey out the actions until we can actually instantiate or simulate
        self.instantiate = instantiateAction
        self.instantiate.setEnabled(False)
        self.simulate = simulateAction
        self.simulate.setEnabled(False)


    def buildToolsTab(self, mainMenu, window):
        """build the tools tab"""
        wireAction = QAction("Enable Wire", window)
        wireAction.setShortcut("Ctrl+W")
        wireAction.triggered.connect(self.wire_button_pressed)

        toolsMenu = mainMenu.addMenu('Tools')
        toolsMenu.addAction(wireAction)

    def buildDebugTab(self, mainMenu, window):
        """build the debug tab"""
        toggleAction = QAction("Show Debug Window", window)
        toggleAction.triggered.connect(self.toggleDebugWindow)

        debugMenu = mainMenu.addMenu('Debug')
        debugMenu.addAction(toggleAction)


    def toggleDebugWindow(self):
        """ Event handler which proxies toggling the debug widget"""
        self.state.mainWindow.toggleDebug()

    def wire_button_pressed(self):
        """changes gui state to allow for wire drawing and
            disable object dragging"""
        self.state.drag_state = not self.state.drag_state
        self.state.draw_wire_state = not self.state.draw_wire_state
        self.state.setDragState()
        self.state.line_drawer.update()

    def new_button_pressed(self):
        # check if any changes have been made - to save before closing
        if not self.state.mostRecentSaved:
            dialog = saveChangesDialog("opening a new file")
            if dialog.exec_():
                self.save_button_pressed()

        # clear out existing objects and wires
        for object in self.state.sym_objects.values():
            for name, connection in object.ui_connections.items():
                if connection.line:
                    self.state.scene.removeItem(connection.line)

            self.state.scene.removeItem(object)
            object.ui_connections.clear()

        # clear out backend sym object dictionary
        self.state.sym_objects.clear()

    def copy_button_pressed(self):
        logging.debug("copy button pressed")
        if not len(self.state.selected_sym_objects):
            return

        self.state.copyState = True
        self.state.copied_objects = list(self.state.selected_sym_objects)
        self.addChildObjects()
        #copy objects from "oldest" to "youngest"
        self.state.copied_objects.sort(key=lambda x: x.z)

    def addChildObjects(self):
        for selectedObject in self.state.copied_objects:
            self.addChildren(selectedObject)

    def addChildren(self, object):
        for child_name in object.connected_objects:
            child = self.state.sym_objects[child_name]
            if not child in self.state.copied_objects:
                self.state.copied_objects.append(child)
                self.addChildren(child)

    def paste_button_pressed(self):
        if not self.state.copyState:
            return

        for selectedObject in self.state.copied_objects:
            self.copy_sym_object(selectedObject)
        for selectedObject in self.state.copied_objects:
            self.copyConnection(selectedObject)
        self.state.copyState = False
        self.state.removeHighlight()
        del self.state.copied_objects[:]
        self.state.line_drawer.update()

    def copy_sym_object(self, selectedObject):
        object_name = selectedObject.name + "_copy"
        new_object = self.state.scene.addObjectToScene("component",
                                selectedObject.component_name, object_name)
        #copy over parent - child relationship info
        if selectedObject.parent_name:
            parent_name = selectedObject.parent_name + "_copy"
            if parent_name in self.state.sym_objects:
                parent = self.state.sym_objects[parent_name]
                parent.addSubObject(new_object)
                new_object.parent_name = parent_name
                parent.connected_objects.append(new_object.name)

        #copy backend info
        new_object.instance_ports = copy.deepcopy(selectedObject.instance_ports)
        new_object.instance_params = \
            copy.deepcopy(selectedObject.instance_params)
        new_object.SimObject = \
            copy.deepcopy(self.state.instances[new_object.component_name])

        #calculate z value
        current_object_name = selectedObject.name
        new_object.z = 0
        while self.state.sym_objects[current_object_name].parent_name:
            current_object_name = \
                self.state.sym_objects[current_object_name].parent_name
            new_object.z += 1
        new_object.initPorts()

        new_object.instantiateSimObject()
        self.state.sym_objects[object_name] = new_object

    def copyConnection(self, selectedObject):
        object_name = selectedObject.name + "_copy"
        new_object = self.state.sym_objects[object_name]
        delete_button_height = new_object.delete_button.boundingRect().height()
        num_ports = len(new_object.instance_ports)
        y_offset = (new_object.height - delete_button_height) / num_ports
        new_x = new_object.scenePos().x() + new_object.width * 7 / 8
        for name, connection in selectedObject.ui_connections.items():
            if self.state.sym_objects[name[1]] not in self.state.copied_objects:
                continue
            new_y = delete_button_height

            object_name2 = self.state.sym_objects[name[1]].name + "_copy"
            object2 = self.state.sym_objects[object_name2]
            delete_button_height2 = object2.delete_button.boundingRect().height()
            num_ports2 = len(object2.instance_ports)
            y_offset2 = (object2.height - delete_button_height2) / num_ports2
            new_x2 = object2.scenePos().x() + object2.width * 7 / 8
            new_y2 = delete_button_height2
            if name[0] == "parent":
                new_y += new_object.scenePos().y() + connection.parent_port_num\
                    * y_offset + y_offset / 4
                new_y2 += object2.scenePos().y() + connection.child_port_num\
                    * y_offset2 + y_offset2 / 4
                new_coords = QPointF(new_x, new_y)
                new_coords2 = QPointF(new_x2, new_y2)

                key = ("parent", object_name2, name[2], name[3])
                new_object.ui_connections[key] = Connection(new_coords, new_coords2,
                    connection.parent_port_num, connection.child_port_num)
                new_object.instance_ports[name[2]]['Value'] = str(object_name2) + "." + \
                    str(name[3])
            else:
                new_y += new_object.scenePos().y() + connection.child_port_num \
                    * y_offset + y_offset / 4
                new_y2 += object2.scenePos().y() + connection.parent_port_num\
                    * y_offset2 + y_offset2 / 4
                new_coords = QPointF(new_x, new_y)
                new_coords2 = QPointF(new_x2, new_y2)
                key = ("child", object_name2, name[2], name[3])
                new_object.ui_connections[key] = Connection(new_coords, new_coords2,
                    connection.parent_port_num, connection.child_port_num)


    #TODO
    def undo_button_pressed(self):
        logging.debug("undo button pressed")
        last_update = self.state.history.pop()
        if last_update:
            if last_update.operation == "create" or last_update.operation == "copy":
                last_update.sym_object.delete()
            elif last_update.operation == "delete":
                last_update.sym_object
            elif last_update.operation == "move_any":
                pass
            elif last_update.operation == "move_child":
                pass
            elif last_update.operation == "change_attr":
                for object in self.state.sym_objects:
                    if last_update.sym_object.name == object.name:
                        object = last_update.sym_object
            else:
                logging.debug("history: operation not found")
        else:
            logging.debug("undo returned null")

    # creates a python file that can be run with gem5
    def export_button_pressed(self):
        dlg = instantiateDialog()
        if dlg.exec_():
            logging.debug("Export Success!")
            self.instantiate.setEnabled(False)
            self.simulate.setEnabled(True)
            self.save_button_pressed() #want to save before instantiation
            for object in self.state.sym_objects.values():
                if object.component_name == "Root":
                    root_name , root = traverse_hierarchy_root(\
                                                self.state.sym_objects, object)
                    instantiate_model() #actual m5 instatiation

    def simulate_button_pressed(self):
        """creates a python file that can be run with gem5"""
        simulate()

    def openUI_button_pressed(self):
        """loads .ui file into gui"""
        # check if any changes have been made - to save before closing
        if not self.state.mostRecentSaved:
            dialog = saveChangesDialog("opening a new file")
            if dialog.exec_():
                self.save_button_pressed()

        # show dialog box for user to select a file to open
        filename = QFileDialog.getOpenFileName(None, 'Open file',
       '',"gem5 UI Files (*.ui)")[0]

       # stop if cancel is pressed or there is an error
        if not filename:
            return

        # set state filename to file that was loaded
        self.state.fileName = filename

        # get file name from path and add to window title
        tokens = filename.split('/')
        self.state.mainWindow.setWindowTitle("gem5 GUI | " + tokens[-1])

        # clear out existing objects and wires before loading from file
        for object in self.state.sym_objects.values():
            for name, connection in object.ui_connections.items():
                if connection.line:
                    self.state.scene.removeItem(connection.line)

            self.state.scene.removeItem(object)
            object.ui_connections.clear()

        self.state.sym_objects.clear()

        # read data in from the file and load each object
        with open(filename) as json_file:
            data = json.load(json_file)
            z_score = 0
            while str(z_score) in data:
                cur_z_array = data[str(z_score)]
                for object in cur_z_array:
                    self.state.scene.loadSavedObject("component",
                                                    object["name"], object)

                z_score += 1

            self.state.line_drawer.update()

        self.state.mostRecentSaved = True

    def getOutputData(self):
        """build dictionary to export to file"""
        savedObjects = {}

        # iterate through the current objects on the scene and create a new JSON
        # object for each one
        for object in self.state.sym_objects.values():
            newObject = {}
            newObject["x"] = object.scenePos().x()
            newObject["y"] = object.scenePos().y()
            newObject["z"] = object.z
            newObject["width"] = object.width
            newObject["height"] = object.height
            newObject["component_name"] = object.component_name
            newObject["name"] = object.name
            newObject["parent_name"] = object.parent_name

            params = {}
            #Storing the parameters
            for param in object.instance_params:
                params[str(param)] = {}

                # TODO: Insert err message here if a parameter has not been set
                if object.instance_params[param]["Value"] is None:
                    logging.error("Error must set required parameter")
                    params[str(param)]["Value"] = None

                #Only need to store the values of parameters changed for now
                if object.instance_params[param]["Default"] != \
                    object.instance_params[param]["Value"]:
                    param_type = type(object.instance_params[param]["Value"])
                    if (param_type == str or param_type == int or \
                            param_type == bool or param_type == unicode or \
                            param_type == list):
                        params[str(param)]["Value"] = \
                            object.instance_params[param]["Value"]
                    else:
                        # weird case if a value is a class but shouldn't really
                        #   hit this case since all user inputs are strings
                        params[str(param)]["Value"] = \
                            object.instance_params[param]["Value"].__dict__

            newObject["parameters"] = params

            ports = {}
            for port in object.instance_ports.keys():
                ports[port] = {}
                if isinstance(object.instance_ports[port]["Value"], str):
                    ports[port]["Value"] = \
                        str(object.instance_ports[port]["Value"])
                else:
                    ports[port]["Value"] = None

            newObject["ports"] = ports
            newObject["connected_objects"] = object.connected_objects

            connections = []

            for c in object.ui_connections:
                newConnection = {}
                newConnection["key"] = c
                newConnection["parent_endpoint_x"] = \
                        object.ui_connections[c].parent_endpoint.x()
                newConnection["parent_endpoint_y"] = \
                        object.ui_connections[c].parent_endpoint.y()
                newConnection["child_endpoint_x"] = \
                        object.ui_connections[c].child_endpoint.x()
                newConnection["child_endpoint_y"] = \
                        object.ui_connections[c].child_endpoint.y()
                newConnection["parent_port_num"] = \
                        object.ui_connections[c].parent_port_num
                newConnection["child_port_num"] = \
                        object.ui_connections[c].child_port_num
                connections.append(newConnection)

            newObject["connections"] = connections

            if object.z not in savedObjects:
                savedObjects[object.z] = []

            savedObjects[object.z].append(newObject)

        return savedObjects

    def save_button_pressed(self):
        """saves current state to open file if it exists, otherwise use dialog
        to select new file to save to"""
        # check if file is already open
        if self.state.fileName:
            filename = self.state.fileName
        else:             # show dialog box to let user create output file
            filename = QFileDialog.getSaveFileName(None, "",
                                           "",
                                           "gem5 UI Files (*.ui)")[0]

        # stop if cancel is pressed
        if not filename:
            return

        savedObjects = self.getOutputData()

        # with the selected file write our JSON object
        with open(filename, 'w') as outfile:
            json.dump(savedObjects, outfile, indent=4)
        # get file name from path
        tokens = filename.split('/')
        self.state.mainWindow.setWindowTitle("gem5 GUI | " + tokens[-1])

        self.state.mostRecentSaved = True

    def save_as_UI_button_pressed(self):
        """saves gui state to a .ui file, shows dialog to select output file
        regardless of whether file exists in the state"""
        # show dialog box to let user create output file
        filename = QFileDialog.getSaveFileName(None, "",
                                           "",
                                           "gem5 UI Files (*.ui)")[0]
        # stop if cancel is pressed
        if not filename:
            return

        self.state.fileName = filename

        savedObjects = self.getOutputData()

        # with the selected file write our JSON object
        with open(filename, 'w') as outfile:
            json.dump(savedObjects, outfile, indent=4)

        # get file name from path
        tokens = filename.split('/')
        self.state.mainWindow.setWindowTitle("gem5 GUI | " + tokens[-1])

        self.state.mostRecentSaved = True
