#!/usr/bin/python2
# -*- coding: utf-8 -*-

__author__ = "Niklas Fiekas"
__email__ = "niklas.fiekas@googlemail.com"
__version__ = "0.0.1"

from PySide.QtCore import *
from PySide.QtGui import *

import sys


class Application(QApplication):

    def __init__(self, argv):
        super(Application, self).__init__(argv)


class MainWindow(QMainWindow):

    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.app = app

        self.initActions()
        self.initMenu()

        self.setWindowTitle("Kalender")

        self.modified = True
        self.path = None

    def initActions(self):
        self.newAction = QAction("Neu", self)

        self.openAction = QAction(u"Öffnen ...", self)

        self.saveAction = QAction("Speichern", self)
        self.saveAction.triggered.connect(self.onSaveAction)
        self.saveAction.setShortcut("Ctrl+S")

        self.saveAsAction = QAction("Speichern unter ...", self)
        self.saveAsAction.triggered.connect(self.onSaveAsAction)

        self.closeAction = QAction(u"Schließen", self)
        self.closeAction.triggered.connect(self.onCloseAction)

        self.aboutAction = QAction(u"Über ...", self)
        self.aboutAction.triggered.connect(self.onAboutAction)
        self.aboutAction.setShortcut("F1")

        self.aboutQtAction = QAction(u"Über Qt ...", self)
        self.aboutQtAction.triggered.connect(self.onAboutQtAction)

    def initMenu(self):
        fileMenu = self.menuBar().addMenu("Datei")
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.closeAction)

        infoMenu = self.menuBar().addMenu("Info")
        infoMenu.addAction(self.aboutAction)
        infoMenu.addAction(self.aboutQtAction)

    def onAboutAction(self):
        QMessageBox.about(
            self,
            "Kalender %s" % (__version__, ),
            "<h1>Kalender %s</h1>%s &lt;<a href=\"mailto:%s\">%s</a>&gt;" % (
                __version__, __author__, __email__, __email__))

    def onAboutQtAction(self):
        QMessageBox.aboutQt(self, "Kalender")

    def onCloseAction(self):
        self.close()

    def onSaveAction(self):
        if not self.path:
            return self.onSaveAsAction()

        return True

    def onSaveAsAction(self):
        return True

    def askClose(self):
        if not self.modified:
            return True

        result = QMessageBox.question(
            self,
            u"Ungespeicherte Änderungen",
            u"Ungespeicherte Änderungen gehen verloren. Möchten Sie die Datei vor dem Schließen speichern?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

        if result == QMessageBox.Save:
            if not self.onSaveAction():
                return False

        if result == QMessageBox.Cancel:
            return False

        return True

    def closeEvent(self, event):
        if self.askClose():
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    app = Application(sys.argv)

    mainWindow = MainWindow(app)
    mainWindow.show()

    app.exec_()
