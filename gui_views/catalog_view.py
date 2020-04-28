from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from graphic_scene import *

import sys, random
import copy
from gui_views import state
import json

class CatalogView(): #dropdown and search bar
    def __init__(self, layout, catalog, state):
        self.state = state
        self.catalog = catalog
        #search bar
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Search for an object here!")

        #adding fix width on one of the widgets in the catalog area will
        #implicitly set a fixed width on the rest of the widgets
        #we do this so that the catalog retains its original dimensions while
        #resizing the window
        self.edit.setFixedWidth(250)

        layout.addWidget(self.edit)

        #dropdown for SimObjects
        self.treeWidget = QTreeWidget()
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "Name")
        self.treeWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.treeWidget)

        #handlers
        self.edit.textChanged.connect(self.searchItem)
        self.treeWidget.itemClicked.connect(self.state.removeHighlight)
        self.treeWidget.itemDoubleClicked.connect(self.createSymObject)

    #this creates a new symobject at some point in the CanvasView
    def createSymObject(self, item):
        if item.parent() is None:
            return

        # if selecting an imported object from catalog
        if item.text(0) in self.state.importedSymObjects:
            filename = self.state.importedSymObjects[item.text(0)]["file"]
            self.state.mainWindow.buttonView.importFromFile(filename)
            return

        name, ok = QInputDialog.getText(self.state.mainWindow, "Alert", \
                                        "New SimObject name:")
        if not ok:
            return

        new_parent = None

        if len(self.state.selected_sym_objects) == 1:
            new_parent = self.state.selected_sym_objects[0]
        self.state.removeHighlight()
        del self.state.selected_sym_objects[:]
        #modify state to accomodate the new object
        new_object = \
            self.state.scene.addObjectToScene("component", item.text(0), name)
        new_object.instance_params = \
            copy.deepcopy(self.catalog[item.parent().text(0)][item.text(0)]['params'])
        new_object.instance_ports = \
            copy.deepcopy(self.catalog[item.parent().text(0)][item.text(0)]['ports'])
        new_object.initPorts()

        #eager instantiation
        new_object.instantiateSimObject()

        # if sub object is being added through catalog
        if new_parent:
            child = self.state.selected_sym_objects[0]

            # need to set initial position of new object to force resize and
            # make sure there is enough space to fit object
            hasChildren = False
            if new_parent.connected_objects:
                hasChildren = True
                lastChild = self.state.sym_objects[new_parent.connected_objects[-1]]
                child.setPos(lastChild.scenePos().x() + 10, lastChild.scenePos().y() + 10)

            # configure child as a UI subobject of parent
            new_parent.addSubObject(child)

            # if parent already has child subobjects, set the new child's
            # position to the right bottom corner as it is guaranteed to be
            # empty
            if hasChildren:
                pos_x = new_parent.scenePos().x() + new_parent.width \
                                                                - child.width
                pos_y = new_parent.scenePos().y() + new_parent.height \
                                                                - child.height
                child.setPos(pos_x, pos_y)

            child.x = child.scenePos().x()
            child.y = child.scenePos().y()

            self.state.removeHighlight()
            child.rect.setBrush(QColor("Green"))
            self.state.selected_sym_objects.append(child)
            self.state.mainWindow.populateAttributes(None, child.component_name,
                                                    False)

        self.state.mostRecentSaved = False
        #allow instantiation ONLY when root is on the canvas
        #if self.state.selected_sym_objects.component_name == "Root":
        #    self.state.mainWindow.buttonView.exportButton.setEnabled(True)

    # make tree view searchable
    def searchItem(self):
        """
        Searches treeview whenever a user types something in the search bar
        """
        # Get string in the search bar and use treeview's search fn
        search_string = self.edit.text()
        match_items = self.treeWidget.findItems(search_string, Qt.MatchContains
                                                | Qt.MatchRecursive)

        root = self.treeWidget.invisibleRootItem()
        child_count = root.childCount()

        # Iterate through top-level items
        for i in range(child_count):
            item = root.child(i)
            if len(match_items) == 0: # Hide all items if no matches
                item.setHidden(True)

            elif search_string == "": # if empty string don't hide or expand
                item.setHidden(False)
                item.setExpanded(False)

            else:
                # Go through sub items for each top-level item
                gchild_count = item.childCount()
                # see if any sub item is a match
                not_found = False
                for j in range(gchild_count):
                    grand_item = item.child(j)
                    not_found = not_found or (grand_item in set(match_items))
                    grand_item.setHidden(grand_item not in set(match_items))
                # hide and expand top-level item based on if sub-level item
                #   is a match
                item.setHidden(not not_found)
                item.setExpanded(not_found)
