#!/usr/bin/python2
# -*- coding: utf-8 -*-

__author__ = "Niklas Fiekas"
__email__ = "niklas.fiekas@tu-clausthal.de"
__version__ = "0.0.1"

from PySide.QtCore import *
from PySide.QtGui import *

import datetime
import sys

MONTH_NAMES = ["Januar", "Februar", u"März", "April", "Mai", "Juni", "Juli",
               "August", "September", "November", "Oktober", "Dezember"]


def is_leap_year(year):
    if year % 4 != 0:
        return False
    elif year % 100 != 0:
        return True
    elif year % 400 != 0:
        return False
    else:
        return True

def days_of_month(month):
    year = 1900 + month // 12
    if month % 12 == 0:
        return 31
    elif month % 12 == 1:
        return 29 if is_leap_year(year) else 28
    elif month % 12 == 2:
        return 31
    elif month % 12 == 3:
        return 30
    elif month % 12 == 4:
        return 31
    elif month % 12 == 5:
        return 30
    elif month % 12 == 6:
        return 31
    elif month % 12 == 7:
        return 31
    elif month % 12 == 8:
        return 30
    elif month % 12 == 9:
        return 31
    elif month % 12 == 10:
        return 30
    else:
        return 31


class Application(QApplication):

    def __init__(self, argv):
        super(Application, self).__init__(argv)

        self.white = QColor(255, 255, 255)
        self.black = QColor(0, 0, 0)
        self.gray = QColor(191, 191, 191)


class MainWindow(QMainWindow):

    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.app = app

        self.initActions()
        self.initMenu()
        self.initWidget()

        self.setWindowTitle("Kalender")

        self.modified = True
        self.path = "test.json"

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

    def initWidget(self):
        self.calendar = CalendarWidget(self.app, self)
        self.setCentralWidget(self.calendar)

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

        if not self.path:
            question = u"Ungespeicherte Änderungen in der neuen Datei gehen verloren. Möchten Sie die Datei vor dem Schließen speichern?"
        else:
            question = u"Ungespeicherte Änderungen in »%s« gehen verloren. Möchten Sie die Datei vor dem Schließen speichern?" % (self.path, )

        result = QMessageBox.question(
            self, u"Ungespeicherte Änderungen", question,
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


class CalendarWidget(QWidget):

    def __init__(self, app, parent=None):
        super(CalendarWidget, self).__init__(parent)
        self.app = app

        self.offset = 0

    def columnWidth(self):
        return min(max(self.width() / 12.0, 40.0), 125.0)

    def rowHeight(self):
        return max((self.height() - 40 - 20 - 10) / 31.0, 10.0)

    def visibleMonths(self):
        start = int(self.offset) - 13
        end = int(self.offset + self.width() / self.columnWidth() + 1)

        for month in xrange(start, end):
            x = (month - self.offset) * self.columnWidth()
            yield x, month

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw white background.
        for x, month in self.visibleMonths():
            painter.fillRect(QRect(x, 40 + 20, self.columnWidth(), days_of_month(month) * self.rowHeight()), QBrush(self.app.white))

        for x, month in self.visibleMonths():
            # Draw year header.
            if month % 12 == 0:
                painter.save()
                opt = QStyleOptionHeader()
                opt.rect = QRect(x, 0, self.columnWidth() * 12, 40)
                self.style().drawControl(QStyle.CE_Header, opt, painter, self)
                painter.restore()

                # Draw title text.
                painter.save()
                painter.setPen(QPen())
                font = self.font()
                font.setPointSizeF(font.pointSizeF() * 1.2)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(QRect(x + 32, 0, self.columnWidth() * 12 - 32 * 2, 40),
                    Qt.AlignVCenter, str(1900 + month // 12))
                painter.restore()

            # Draw month header.
            painter.save()
            opt = QStyleOptionHeader()
            opt.rect = QRect(x, 40, self.columnWidth(), 20)
            opt.textAlignment = Qt.AlignCenter
            if opt.rect.width() < 80:
                opt.text = MONTH_NAMES[month % 12][:3]
            else:
                opt.text = MONTH_NAMES[month % 12]
            self.style().drawControl(QStyle.CE_Header, opt, painter, self)
            painter.restore()

            painter.save()
            painter.setPen(QPen(self.app.gray))
            for day in range(1, days_of_month(month) + 1):
                # Draw horizontal lines.
                yStart = 40 + 20 + (day - 1) * self.rowHeight()
                yEnd = yStart + self.rowHeight()
                painter.drawLine(x, yEnd, x + self.columnWidth(), yEnd)

                # Draw day numbers.
                if self.rowHeight() > 22 or day % 2 == 0:
                    font = self.font()
                    font.setPointSizeF(min(self.rowHeight() * 0.6, font.pointSizeF()))
                    painter.setFont(font)
                    painter.drawText(QRect(x, yStart, min(self.rowHeight() / 20.0, 1.0) * 30, self.rowHeight()),
                        Qt.AlignVCenter | Qt.AlignRight, str(day))
            painter.restore()

            # Draw vertical lines.
            painter.save()
            if month % 12 == 0:
                painter.setPen(QPen(self.app.gray, 2))
            else:
                painter.setPen(QPen(self.app.gray))
            painter.drawLine(x, 40 + 20, x, 40 + 20 + self.rowHeight() * max(days_of_month(month), days_of_month(month - 1)))
            painter.restore()


if __name__ == "__main__":
    app = Application(sys.argv)

    mainWindow = MainWindow(app)
    mainWindow.show()

    app.exec_()
