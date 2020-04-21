from PySide2.QtCore import *
from PySide2.QtWidgets import *
from PySide2.QtGui import *
from graphic_scene import *

import sys, random
import copy
from gui_views import state
import json


class AttributeView(): #table view for parameters, as well as the description
    def __copy__(self):
        return self

    def __deepcopy(self, memo):
        return self

    def __init__(self, layout, state):
        self.state = state
        #attribute table for an object, is editable
        self.attributeLayout = QHBoxLayout()
        self.attributeTable = QTableWidget(0,2)
        self.attributeTable.setObjectName("attributeTable")
        self.attributeTable.verticalHeader().setVisible(False)
        self.attributeTable.horizontalHeader().setVisible(False)
        header = self.attributeTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.attributeLayout.addWidget(self.attributeTable)

        layout.addLayout(self.attributeLayout)

        #description label
        self.label = QLabel()
        self.label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        self.label.setWordWrap(True)
        self.label.setScaledContents(True)
        layout.addWidget(self.label)

        #handlers
        self.attributeTable.itemDoubleClicked.connect(self.makeEditable)


    def makeEditable(self, item):
        """ this function feeds into the next one, after the cell is
        changed it will trigger """
        if len(self.state.selected_sym_objects) != 1 or not item:
             return
        # set item to editable
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.attributeTable.itemChanged.connect(self.modifyFields)


    def modifyParam(self, currentAttribute, updatedValue):
        """Given the current Attribute(param) and a new value entered in the
            gui, update the current symobject's value for the parameter"""
        instance_params = self.state.selected_sym_objects[0].instance_params
        # if the value is name or connected objects, set the param instead of
        # the dict
        if currentAttribute not in instance_params:
            instance_params[currentAttribute] = {}
            #TODO look into this check, it seems like we do not need it
            if "Value" not in instance_params[currentAttribute]:
                catalog = self.state.catalog
                name = self.state.selected_sym_objects[0].component_name
                instance_params[currentAttribute]["Value"] = updatedValue
                instance_params[currentAttribute]["Type"] = \
                    catalog["SimObject"][name]['ports'][currentAttribute]['Type']
        else:
            instance_params[currentAttribute]["Value"] = updatedValue


    def modifyFields(self, item):
        """ this signal disconnects itself after finishing execution,
         since we only want to trigger it AFTER a double press """

        # get attributes
        currentColumn = self.attributeTable.column(item)
        currentRow = self.attributeTable.row(item)
        currentAttribute = self.attributeTable.item(currentRow,
                                                    currentColumn - 1).text()
        currentValue = item.text()

        # if the value is name or connected objects, set the param instead of
        # the dict
        if currentAttribute == "Name":
            self.state.selected_sym_objects[0].updateName(currentValue)
            current_x = self.state.selected_sym_objects[0].x
            current_y = self.state.selected_sym_objects[0].y
            current_name = self.state.selected_sym_objects[0].name

            self.state.sym_objects[current_name] = self.state.selected_sym_objects[0]
        elif currentAttribute == "Child Objects":
            self.state.selected_sym_objects[0].connected_objects = currentValue
            self.state.line_drawer.connectSubObject(self.state.selected_sym_objects[0].name,
                                                currentValue)
        else:
            self.modifyParam(currentAttribute, currentValue)


        # item no longer editable, disconnect
        self.attributeTable.itemChanged.disconnect(self.modifyFields)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        if currentValue:
            item.setBackground(QColor("white"))

        self.state.mostRecentSaved = False
