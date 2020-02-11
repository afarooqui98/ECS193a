try:
    from PyQt4.QtGui import QLabel, QPixmap, QDrag
    from PyQt4.QtCore import *
except:
    from PyQt5.QtWidgets import QLabel
    from PyQt5.QtGui import QPixmap, QDrag
    from PyQt5.QtCore import *


class QDragLabel(QLabel):
    """this class provides an image label that can be dragged and dropped"""

    #constructor
    def __init__(self,text):
        super().__init__()
        #self.setPixmap(picture.scaledToWidth(35,1))
        self.setText(text)

    def mouseMoveEvent(self,event):
        #if the left mouse button is used
        if event.buttons() == Qt.LeftButton:
            data = QByteArray()
            mime_data = QMimeData()
            mime_data.setData(self.mimetext,data)
            mime_data.setText(self.mimetext)
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.setHotSpot(self.rect().topLeft()) #where do we drag from
            if QT_VERSION_STR < '5':
                drop_action = drag.start(Qt.MoveAction) #drag starts
            else:
                drop_action = drag.exec(Qt.MoveAction) #drag starts

class ComponentLabel(QDragLabel):
    """this class provides an wheat label that can be dragged and dropped"""
    def __init__(self, name):
        super().__init__(name)
        self.mimetext = name


class SystemLabel(QDragLabel):
    """this class provides an sheep label that can be dragged and dropped"""
    def __init__(self):
        super().__init__("System")
        self.mimetext = "application/x-system"