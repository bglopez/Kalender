#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = "Niklas Fiekas"
__email__ = "niklas.fiekas@backscattering.de"
__version__ = "0.1.0"

from PySide.QtCore import *
from PySide.QtGui import *

import datetime
import sys
import os
import json
import itertools
import random


MONTH_NAMES = ["Januar", "Februar", u"März", "April", "Mai", "Juni", "Juli",
               "August", "September", "Oktober", "November", "Dezember"]

WEEKDAY_NAMES = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag",
                 "Freitag", "Samstag", "Sonntag"]


SOLARIZED_ACCENT_COLORS = [
    QColor("#b58900"), # Yellow
    QColor("#cb4b16"), # Orange
    QColor("#dc322f"), # Red
    QColor("#d33682"), # Magenta
    QColor("#6c71c4"), # Violet
    QColor("#268bd2"), # Blue
    QColor("#2aa198"), # Cyan
    QColor("#859900"), # Green
]

SOLARIZED_BASE_COLOR = QColor(7, 54, 66)

SHADOW_COLOR = QColor(0, 0, 0, 50)
LIGHT_COLOR = QColor(255, 255, 255, 100)

BLUE_LIGHT_COLOR = QColor(146, 197, 233, 100)
GREEN_LIGHT_COLOR = QColor(100, 219, 100, 50)
RED_LIGHT_COLOR = QColor(242, 219, 219, 100)
YELLOW_LIGHT_COLOR = QColor(255, 255, 0, 50)


GOLDEN_RATIO_CONJUGATE = 0.618033988749895


def days_of_month(month):
    date = qdate(month, 1)
    return date.daysInMonth()

def qdate(month, day):
    return QDate(1900 + month // 12, month % 12 + 1, day)

def easter_sunday(year):
    g = year % 19
    c = year / 100
    h = (c - (c / 4) - ((9 * c + 13) / 25) + 19 * g + 15) % 30
    i = h - (h / 28) * (1 - (h / 28) * (29 / (h + 1)) * ((21 - g) / 11))
    day = i - ((year + (year / 4) + i + 2 - c + (c / 4)) % 7) + 28
    if day > 31:
        return (year - 1900) * 12 + 3, day - 31
    else:
        return (year - 1900) * 12 + 2, day


HOLIDAY_NONE = 0
HOLIDAY_NEWYEAR = 1
HOLIDAY_GOOD_FRIDAY = 2
HOLIDAY_EASTER_MONDAY = 4
HOLIDAY_MAY_1 = 8
HOLIDAY_ASCENSION = 16
HOLIDAY_PENTECOST = 32
HOLIDAY_TAG_DER_DEUTSCHEN_EINHEIT = 64
HOLIDAY_CHRISTMAS = 128
HOLIDAY_SUNDAY = 256
HOLIDAY_REFORMATIONSTAG = 512

def is_holiday(month, day):
    holiday = HOLIDAY_NONE

    easter_month, easter_day = easter_sunday(1900 + month // 12)
    easter = qdate(easter_month, easter_day)
    date = qdate(month, day)

    if date.dayOfWeek() == 7:
        holiday |= HOLIDAY_SUNDAY

    if date.addDays(2) == easter:
        holiday |= HOLIDAY_GOOD_FRIDAY
    elif date.addDays(-1) == easter:
        holiday |= HOLIDAY_EASTER_MONDAY
    elif date.addDays(-39) == easter:
        holiday |= HOLIDAY_ASCENSION
    elif date.addDays(-49) == easter:
        holiday |= HOLIDAY_PENTECOST

    if date.dayOfYear() == 1:
        holiday |= HOLIDAY_NEWYEAR
    elif date.month() == 5 and date.day() == 1:
        holiday |= HOLIDAY_MAY_1
    elif date.month() == 10 and date.day() == 3:
        holiday |= HOLIDAY_TAG_DER_DEUTSCHEN_EINHEIT
    elif date.month() == 10 and date.day() == 31:
        holiday |= HOLIDAY_REFORMATIONSTAG
    elif date.month() == 12 and date.day() in (25, 26):
        holiday |= HOLIDAY_CHRISTMAS

    return holiday


class Range(object):
    def __init__(self):
        self.index = None
        self.deleted = False
        self.title = ""
        self.notes = ""
        self.start = QDate()
        self.end = QDate()
        self.color = QColor()

    def copy(self):
        r = Range()
        r.index = self.index
        r.deleted = self.deleted
        r.title = self.title
        r.notes = self.notes
        r.start = self.start
        r.end = self.end
        r.color = self.color
        return r


class Model(QObject):

    modelChanged = Signal()

    def __init__(self):
        super(Model, self).__init__()
        self.ranges = { }
        self.modified = False

        self.undoStack = [ ]
        self.redoStack = [ ]

    def nextId(self):
        return max(itertools.chain(self.ranges.keys(), [0])) + 1

    def commit(self, r):
        i = r.index if r.index else self.nextId()

        if i in self.ranges:
            restoreAction = self.ranges[i]
            self.undoStack.append(restoreAction)
        else:
            deleteAction = Range()
            deleteAction.index = i
            deleteAction.deleted = True
            self.undoStack.append(deleteAction)

        self.ranges[i] = r.copy()
        self.ranges[i].index = i
        self.redoStack = []

        self.modified = True

        self.modelChanged.emit()

    def undo(self):
        if not self.undoStack:
            return

        action = self.undoStack.pop()

        restoreAction = self.ranges[action.index]
        self.redoStack.append(restoreAction)

        self.ranges[action.index] = action.copy()

        self.modelChanged.emit()

    def redo(self):
        if not self.redoStack:
            return

        action = self.redoStack.pop()

        restoreAction = self.ranges[action.index]
        self.undoStack.append(restoreAction)

        self.ranges[action.index] = action.copy()

        self.modelChanged.emit()

    def save(self, path):
        document = { }
        for key in self.ranges:
            r = self.ranges[key]
            if not r.deleted:
                document[r.index] = {
                    "title": r.title,
                    "notes": r.notes,
                    "start": r.start.toString(Qt.ISODate),
                    "end": r.end.toString(Qt.ISODate),
                    "color": r.color.name(),
                }

        with open(path, "w") as handle:
            json.dump(document, handle)

        self.modified = False

    @classmethod
    def load(cls, path):
        model = cls()

        with open(path, "r") as handle:
            document = json.load(handle)

            for key in document:
                r = Range()
                r.index = int(key)
                r.title = document[key]["title"]
                r.notes = document[key]["notes"]
                r.start = QDate.fromString(document[key]["start"], Qt.ISODate)
                r.end = QDate.fromString(document[key]["end"], Qt.ISODate)
                r.color = QColor(document[key]["color"])
                model.ranges[r.index] = r

        return model


class Application(QApplication):

    def __init__(self, argv):
        super(Application, self).__init__(argv)

        self.initResources()
        self.initSettings()

    def initResources(self):
        self.calendarIcon = QIcon(os.path.join(os.path.dirname(__file__), "resources", "kalender.ico"))

        self.leftPixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "left.png"))
        self.leftDownPixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "left-down.png"))
        self.rightPixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "right.png"))
        self.rightDownPixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "right-down.png"))
        self.todayPixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "today.png"))
        self.todayDownPixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "today-down.png"))

        self.newPixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "new.png"))
        self.newDownPixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "new-down.png"))

        self.deletePixmap = QPixmap(os.path.join(os.path.dirname(__file__), "resources", "delete.png"))

    def initSettings(self):
        self.settings = QSettings("Injoy Osterode", "Kalender")


class ColorButton(QPushButton):

    def __init__(self, color=QColor(), parent=None):
        super(ColorButton, self).__init__(parent)
        self.clicked.connect(self.onClicked)
        self.setDialogTitle(u"Farbe wählen")
        self.setColor(color)

    def setColor(self, color):
        self._color = QColor(color)
        self.setText(color.name())

        pixmap = QPixmap(24, 24)
        painter = QPainter(pixmap)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawRect(0, 0, 24, 24)
        painter.end()
        self.setIcon(QIcon(pixmap))

    def color(self):
        return self._color

    def dialogTitle(self):
        return self._dialogTitle

    def setDialogTitle(self, dialogTitle):
        self._dialogTitle = dialogTitle

    def onClicked(self):
        color = QColorDialog.getColor(self.color(), self, self.dialogTitle())
        if color.isValid():
            self.setColor(color)


class RangeDialog(QDialog):

    dialogs = [ ]

    def __init__(self, app, r, parent):
        super(RangeDialog, self).__init__(parent)
        self.app = app
        self.r = r
        self.parent = parent

        self.dialogs.append(self)

        if r.title:
            self.setWindowTitle(r.title)
        elif r.index:
            self.setWindowTitle("Eintrag %d" % r.index)
        else:
            self.setWindowTitle("Neuer Eintrag")

        self.setWindowFlags(self.windowFlags() &~ Qt.WindowContextHelpButtonHint)

        self.colorExplicit = bool(r.index)

        layout = QGridLayout(self)

        layout.addWidget(QLabel("Titel:"), 0, 0)
        self.titleBox = QLineEdit()
        self.titleBox.setText(r.title)
        self.titleBox.textChanged.connect(self.onTitleChanged)
        layout.addWidget(self.titleBox, 0, 1)

        layout.addWidget(QLabel("Farbe:"), 1, 0)
        self.colorBox = ColorButton()
        self.colorBox.setColor(r.color)
        self.colorBox.clicked.connect(self.onColorClicked)
        layout.addWidget(self.colorBox, 1, 1, Qt.AlignLeft)

        layout.addWidget(QLabel("Von:"), 2, 0)
        self.startBox = QDateEdit()
        self.startBox.setDisplayFormat("dd.MM.yyyy")
        self.startBox.setDate(r.start)
        layout.addWidget(self.startBox, 2, 1, Qt.AlignLeft)

        layout.addWidget(QLabel("Bis:"), 3, 0)
        self.endBox = QDateEdit()
        self.endBox.setDisplayFormat("dd.MM.yyyy")
        self.endBox.setDate(r.end)
        layout.addWidget(self.endBox, 3, 1, Qt.AlignLeft)

        layout.addWidget(QLabel("Notizen:"), 4, 0)
        self.notesBox = QTextEdit()
        self.notesBox.setText(r.notes)
        layout.addWidget(self.notesBox, 4, 1)

        deleteButton = QPushButton()
        deleteButton.setIcon(QIcon(self.app.deletePixmap))
        deleteButton.clicked.connect(self.onDelete)
        layout.addWidget(deleteButton, 5, 0, Qt.AlignLeft)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.onSave)
        layout.addWidget(buttons, 5, 1)

    def onTitleChanged(self, title):
        if self.colorExplicit:
            return

        normalized = title.strip().lower()
        if len(normalized) <= 3:
            return

        for key in self.parent.model.ranges:
            r = self.parent.model.ranges[key]
            if r.title.lower().startswith(normalized):
                self.colorBox.setColor(r.color)
                break

    def onColorClicked(self):
        self.colorExplicit = True

    def onSave(self):
        self.parent.model.commit(self.range())
        self.accept()

    def onDelete(self):
        r = self.range()
        if r.index:
            r.deleted = True
            self.parent.model.commit(r)
        self.reject()

    def range(self):
        r = Range()
        r.index = self.r.index
        r.color = self.colorBox.color()
        r.title = self.titleBox.text().strip()
        r.start = min(self.startBox.date(), self.endBox.date())
        r.end = max(self.startBox.date(), self.endBox.date())
        r.notes = self.notesBox.toPlainText()
        return r

    def closeEvent(self, event):
        if self in self.dialogs:
            self.dialogs.remove(self)
        return super(RangeDialog, self).closeEvent(event)


class MainWindow(QMainWindow):

    def __init__(self, app):
        super(MainWindow, self).__init__()
        self.app = app

        self.initWidget()
        self.initOverlays()
        self.initActions()
        self.initMenu()

        self.model = None
        self.setModel(Model())
        self.path = None

        self.restoreSettings()

        self.setWindowTitle("Kalender")
        self.setWindowIcon(self.app.calendarIcon)

    def setModel(self, model):
        if self.model:
            self.model.modelChanged.disconnect(self.onModelChanged)
        self.model = model
        self.model.modelChanged.connect(self.onModelChanged)
        self.calendar.setModel(model)
        self.onModelChanged()

    def initOverlays(self):
        self.ferienNiedersachsenOverlay = FerienNiedersachsen(self.app)
        self.calendar.overlays.append(self.ferienNiedersachsenOverlay)

        self.holidayOverlay = HolidayOverlay(self.app)
        self.calendar.overlays.append(self.holidayOverlay)

    def initActions(self):
        self.newAction = QAction("Neu", self)
        self.newAction.triggered.connect(self.onNewAction)

        self.openAction = QAction(u"Öffnen ...", self)
        self.openAction.triggered.connect(self.onOpenAction)

        self.saveAction = QAction("Speichern", self)
        self.saveAction.triggered.connect(self.onSaveAction)
        self.saveAction.setShortcut("Ctrl+S")

        self.saveAsAction = QAction("Speichern unter ...", self)
        self.saveAsAction.triggered.connect(self.onSaveAsAction)

        self.closeAction = QAction(u"Schließen", self)
        self.closeAction.triggered.connect(self.onCloseAction)

        self.undoAction = QAction(u"Rückgängig", self)
        self.undoAction.setShortcut("Ctrl+Z")
        self.undoAction.triggered.connect(self.onUndoAction)

        self.redoAction = QAction("Wiederholen", self)
        self.redoAction.setShortcut("Ctrl+Y")
        self.redoAction.triggered.connect(self.onRedoAction)

        self.createAction = QAction("Eintrag erstellen", self)
        self.createAction.setShortcut("Ctrl+N")
        self.createAction.triggered.connect(self.onCreateAction)

        self.leftAction = QAction(u"Jahr zurück", self)
        self.leftAction.triggered.connect(self.calendar.onLeftClicked)

        self.todayAction = QAction("Heute", self)
        self.todayAction.triggered.connect(self.calendar.onTodayClicked)

        self.rightAction = QAction("Jahr vor", self)
        self.rightAction.triggered.connect(self.calendar.onRightClicked)

        self.holidayAction = QAction("Feiertage", self)
        self.holidayAction.setIcon(self.holidayOverlay.icon())
        self.holidayAction.setCheckable(True)
        self.holidayAction.toggled.connect(self.onHolidaysToggled)

        self.ferienNiedersachsenAction = QAction("Schulferien Niedersachsen", self)
        self.ferienNiedersachsenAction.setIcon(self.ferienNiedersachsenOverlay.icon())
        self.ferienNiedersachsenAction.setCheckable(True)
        self.ferienNiedersachsenAction.toggled.connect(self.onFerienNiedersachsenToggled)

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

        editMenu = self.menuBar().addMenu("Bearbeiten")
        editMenu.addAction(self.undoAction)
        editMenu.addAction(self.redoAction)
        editMenu.addSeparator()
        editMenu.addAction(self.createAction)

        viewMenu = self.menuBar().addMenu("Ansicht")
        viewMenu.addAction(self.leftAction)
        viewMenu.addAction(self.todayAction)
        viewMenu.addAction(self.rightAction)
        viewMenu.addSeparator()
        viewMenu.addAction(self.holidayAction)
        viewMenu.addAction(self.ferienNiedersachsenAction)

        infoMenu = self.menuBar().addMenu("Info")
        infoMenu.addAction(self.aboutAction)
        infoMenu.addAction(self.aboutQtAction)

    def initWidget(self):
        self.calendar = CalendarWidget(self.app, self)
        self.calendar.createClicked.connect(self.onCreateAction)
        self.calendar.actions.triggered.connect(self.onCalendarAction)
        self.setCentralWidget(self.calendar)

    def restoreSettings(self):
        # Restore window.
        self.restoreGeometry(self.app.settings.value("geometry"))
        self.restoreState(self.app.settings.value("state"))

        # Restore holidays.
        self.holidayOverlay.enabled = bool(int(self.app.settings.value("holidays", "1")))
        self.holidayAction.setChecked(self.holidayOverlay.enabled)

        # Restore Schulferien Niedersachsen.
        self.ferienNiedersachsenOverlay.enabled = bool(int(self.app.settings.value("ferienNiedersachsen", "1")))
        self.ferienNiedersachsenAction.setChecked(self.ferienNiedersachsenOverlay.enabled)

        # Load most recent file.
        if self.app.settings.value("path"):
            try:
                self.setModel(Model.load(self.app.settings.value("path")))
                self.path = self.app.settings.value("path")
            except Exception as err:
                print(err)

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
        else:
            try:
                self.model.save(self.path)
                return True
            except Exception as err:
                QMessageBox.critical(self, "Fehler", "Speichern fehlgeschlagen.")
                print(err)
                return False

    def onSaveAsAction(self):
        path, _ = QFileDialog.getSaveFileName(self, "Kalender speichern", self.path, "Jahreskalender (*.json)")
        if path:
            if not path.endswith(".json"):
                path += ".json"

            self.path = path
            try:
                self.model.save(self.path)
                return True
            except Exception as err:
                QMessageBox.critical(self, "Fehler", "Speichern fehlgeschlagen.")
                print(err)
                return False
        else:
            return False

    def onNewAction(self):
        if self.askClose():
            self.path = None
            self.setModel(Model())

    def onOpenAction(self):
        if self.askClose():
            path, _ = QFileDialog.getOpenFileName(self, u"Kalender öffnen", self.path, "Jahrekalender (*.json)")
            if path:
                try:
                    self.setModel(Model.load(path))
                    self.path = path
                except Exception as err:
                    QMessageBox.critical(self, "Fehler", u"Öffnen fehlgeschlagen.")
                    print(err)
                    return False

    def onHolidaysToggled(self, checked):
        self.holidayOverlay.enabled = checked
        self.calendar.repaint()

    def onFerienNiedersachsenToggled(self, checked):
        self.ferienNiedersachsenOverlay.enabled = checked
        self.calendar.repaint()

    def onUndoAction(self):
        self.calendar.model.undo()

    def onRedoAction(self):
        self.calendar.model.redo()

    def onModelChanged(self):
        self.undoAction.setEnabled(bool(self.calendar.model.undoStack))
        self.redoAction.setEnabled(bool(self.calendar.model.redoStack))

    def onCreateAction(self):
        r = Range()
        r.start = self.calendar.selectionStart()
        r.end = self.calendar.selectionEnd()
        r.color = random.choice(SOLARIZED_ACCENT_COLORS)

        dialog = RangeDialog(self.app, r, self)
        dialog.show()

    def onCalendarAction(self, action):
        index = action.data()
        r = self.model.ranges[index]

        dialog = RangeDialog(self.app, r, self)
        dialog.show()

    def askClose(self):
        while RangeDialog.dialogs:
            dialog = RangeDialog.dialogs.pop()
            dialog.close()

        if not self.model.modified:
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
            self.app.settings.setValue("geometry", self.saveGeometry())
            self.app.settings.setValue("windowState", self.saveState())
            self.app.settings.setValue("holidays", str(int(self.holidayOverlay.enabled)))
            self.app.settings.setValue("ferienNiedersachsen", str(int(self.ferienNiedersachsenOverlay.enabled)))

            if self.path:
                self.app.settings.setValue("path", self.path)
            else:
                self.app.settings.remove("path")

            event.accept()
        else:
            event.ignore()


class HolidayOverlay(object):
    def __init__(self, app):
        self.brush = QBrush(RED_LIGHT_COLOR)
        self.enabled = True

    def matches(self, month, day):
        return self.enabled and is_holiday(month, day)

    def draw(self, painter, rect):
        painter.fillRect(rect, self.brush)

    def icon(self):
        pixmap = QPixmap(16, 16)
        painter = QPainter(pixmap)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        painter.drawRect(0, 0, 16, 16)
        painter.setBrush(self.brush)
        painter.drawRect(0, 0, 16, 16)
        painter.end()
        return QIcon(pixmap)


class FerienNiedersachsen(HolidayOverlay):
    def __init__(self, app):
        self.brush = QBrush(GREEN_LIGHT_COLOR)
        self.enabled = True

    def matches(self, month, day):
        if not self.enabled:
            return False

        year = 1900 + month // 12
        date = qdate(month, day)
        match = False

        if year in (2013, 2014):
            match |= QDate(2013, 1, 31) <= date <= QDate(2013, 2, 1) # Winter
            match |= QDate(2013, 3, 16) <= date <= QDate(2013, 4, 2) # Ostern
            match |= (date == QDate(2013, 5, 10)) or (date == QDate(2013, 5, 21)) # Pfingsten
            match |= QDate(2013, 6, 27) <= date <= QDate(2013, 8, 7) # Sommer
            match |= QDate(2013, 10, 4) <= date <= QDate(2013, 10, 18) # Herbst
            match |= QDate(2013, 12, 23) <= date <= QDate(2014, 1, 3) # Weihnachten

        if year in (2014, 2015):
            match |= QDate(2014, 1, 30) <= date <= QDate(2014, 1, 31) # Winter
            match |= (QDate(2014, 4, 3) <= date <= QDate(2014, 4, 22)) or (date == QDate(2014, 5, 2)) # Ostern
            match |= (date == QDate(2014, 5, 30)) or (date == QDate(2014, 6, 10)) # Pfingsten
            match |= QDate(2014, 7, 31) <= date <= QDate(2014, 9, 10) # Sommer
            match |= QDate(2014, 10, 27) <= date <= QDate(2014, 11, 8) # Herbst
            match |= QDate(2014, 12, 22) <= date <= QDate(2015, 1, 5) # Weihnachten

        if year in (2015, 2016):
            match |= QDate(2015, 2, 2) <= date <= QDate(2015, 2, 3) # Winter
            match |= QDate(2015, 3, 25) <= date <= QDate(2014, 4, 10) # Ostern
            match |= (date == QDate(2015, 5, 15)) or (date == QDate(2015, 5, 26)) # Pfingsten
            match |= QDate(2015, 7, 23) <= date <= QDate(2015, 9, 2) # Sommer
            match |= QDate(2015, 10, 19) <= date <= QDate(2015, 10, 31) # Herbst
            match |= QDate(2015, 12, 23) <= date <= QDate(2016, 1, 6) # Weihnachten

        if year in (2016, 2017):
            match |= QDate(2016, 1, 28) <= date <= QDate(2016, 1, 29) # Winter
            match |= QDate(2016, 3, 18) <= date <= QDate(2016, 4, 2) # Ostern
            match |= (date == QDate(2016, 5, 6)) or (date == QDate(2016, 5, 17)) # Pfingsten
            match |= QDate(2016, 6, 23) <= date <= QDate(2016, 8, 3) # Sommer
            match |= QDate(2016, 10, 3) <= date <= QDate(2016, 10, 15) # Herbst
            match |= QDate(2016, 12, 21) <= date <= QDate(2017, 1, 6) # Weihnachten

        if year in (2017, 2018):
            match |= QDate(2017, 1, 30) <= date <= QDate(2017, 1, 31) # Winter
            match |= QDate(2017, 4, 10) <= date <= QDate(2017, 4, 22) # Ostern
            match |= (date == QDate(2017, 5, 26)) or (date == QDate(2017, 6, 6)) # Pfingsten
            match |= QDate(2017, 6, 22) <= date <= QDate(2017, 8, 2) # Sommer
            match |= QDate(2017, 10, 2) <= date <= QDate(2017, 10, 13) # Herbst
            match |= date == QDate(2017, 10, 30) # Brückentag
            match |= date == QDate(2017, 10, 31) # Reformationstag
            match |= QDate(2017, 12, 22) <= date <= QDate(2018, 1, 5) # Weihnachten

        if year in (2018, 2019):
            match |= QDate(2018, 2, 1) <= date <= QDate(2018, 2, 2) # Winter
            match |= QDate(2018, 3, 19) <= date <= QDate(2018, 4, 3) # Ostern
            match |= date in [QDate(2018, 4, 30), QDate(2018, 5, 11), QDate(2018, 5, 22)] # Pfingsten
            match |= QDate(2018, 6, 28) <= date <= QDate(2018, 8, 8) # Sommer
            match |= QDate(2018, 10, 1) <= date <= QDate(2018, 10, 12) # Herbst
            match |= QDate(2018, 12, 24) <= date <= QDate(2019, 1, 4) # Weihnachten

        if year in (2019, 2020):
            match |= QDate(2019, 1, 31) <= date <= QDate(2019, 2, 1) # Winter
            match |= QDate(2019, 4, 8) <= date <= QDate(2019, 4, 23) # Ostern
            match |= date in [QDate(2019, 5, 31), QDate(2019, 6, 11)] # Pfingsten
            match |= QDate(2019, 7, 4) <= date <= QDate(2019, 8, 14) # Sommer
            match |= QDate(2019, 10, 4) <= date <= QDate(2019, 10, 18) # Herbst
            match |= QDate(2019, 12, 13) <= date <= QDate(2020, 1, 7) # Weihnachten

        return match


class VariantAnimation(QVariantAnimation):
    def updateCurrentValue(self, value):
        pass


MOUSE_DOWN_NONE = 0
MOUSE_DOWN_MONTH = 1
MOUSE_DOWN_DAY = 2
MOUSE_DOWN_LEFT = 3
MOUSE_DOWN_RIGHT = 4
MOUSE_DOWN_TODAY = 5
MOUSE_DOWN_NEW = 6

class CalendarWidget(QWidget):

    createClicked = Signal()

    def __init__(self, app, parent=None):
        super(CalendarWidget, self).__init__(parent)
        self.app = app

        self.setFocusPolicy(Qt.StrongFocus)

        self.targetOffset = float(QDate.currentDate().year() - 1900) * 12
        self.offset = self.targetOffset

        self.overlays = [ ]
        self.model = None
        self.setModel(Model())

        self.selection_end = QDate.currentDate()
        self.selection_start = self.selection_end
        self.mouse_down = MOUSE_DOWN_NONE

        self.animation = VariantAnimation(self)
        self.animation.setEasingCurve(QEasingCurve(QEasingCurve.InOutQuad))
        self.animation.valueChanged.connect(self.onAnimate)
        self.animation.setDuration(1000)
        self.animationEnabled = False

        self.actions = QActionGroup(self)

    def setModel(self, model):
        if self.model:
            self.model.modelChanged.disconnect(self.update)
        self.model = model
        self.model.modelChanged.connect(self.update)
        self.update()

    def onLeftClicked(self):
        self.animationEnabled = False

        self.targetOffset -= 12

        self.animation.setStartValue(self.offset)
        self.animation.setEndValue(self.targetOffset)
        self.animation.start()

        self.animationEnabled = True

    def onRightClicked(self):
        self.animationEnabled = False

        self.targetOffset += 12

        self.animation.setStartValue(self.offset)
        self.animation.setEndValue(self.targetOffset)
        self.animation.start()

        self.animationEnabled = True

    def onTodayClicked(self):
        self.animationEnabled = False

        self.targetOffset = float((QDate.currentDate().year() - 1900) * 12)

        self.animation.setStartValue(self.offset)
        self.animation.setEndValue(self.targetOffset)
        self.animation.start()

        self.animationEnabled = True

    def onNewClicked(self):
        self.createClicked.emit()

    def onAnimate(self, value):
        if not self.animationEnabled:
            return

        self.offset = value
        self.repaint()

    def inSelection(self, date):
        return self.selectionStart() <= date <= self.selectionEnd()

    def selectionStart(self):
        return min(self.selection_start, self.selection_end)

    def selectionEnd(self):
        return max(self.selection_start, self.selection_end)

    def calculateColumnWidth(self):
        return min(max(self.width() / 12.0, 40.0), 125.0)

    def calculateRowHeight(self):
        return max((self.height() - 40 - 20 - 10) / 31.0, 10.0)

    def visibleMonths(self):
        start = int(self.offset) - 13
        end = int(self.offset + self.width() / self.columnWidth + 1)

        for month in range(start, end):
            x = (month - self.offset) * self.columnWidth
            yield x, month

    def resizeEvent(self, event):
        self.rowHeight = self.calculateRowHeight()
        self.columnWidth = self.calculateColumnWidth()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        # Draw white background.
        for x, month in self.visibleMonths():
            painter.fillRect(QRect(x, 40 + 20, self.columnWidth, days_of_month(month) * self.rowHeight), QBrush(Qt.white))

        for x, month in self.visibleMonths():
            # Draw year header.
            if month % 12 == 0:
                painter.save()
                opt = QStyleOptionHeader()
                opt.rect = QRect(x, 0, self.columnWidth * 12, 40)
                self.style().drawControl(QStyle.CE_Header, opt, painter, self)
                painter.restore()

                # Draw left button.
                if self.mouse_down == MOUSE_DOWN_LEFT:
                    painter.drawPixmap(QRect(x + 5, 5, 30, 30), self.app.leftDownPixmap, QRect(0, 0, 30, 30))
                else:
                    painter.drawPixmap(QRect(x + 5, 5, 30, 30), self.app.leftPixmap, QRect(0, 0, 30, 30))

                # Draw today button.
                if self.mouse_down == MOUSE_DOWN_TODAY:
                    painter.drawPixmap(QRect(x + 40, 5, 30, 30), self.app.todayDownPixmap, QRect(0, 0, 30, 30))
                else:
                    painter.drawPixmap(QRect(x + 40, 5, 30, 30), self.app.todayPixmap, QRect(0, 0, 30, 30))

                # Draw right button.
                if self.mouse_down == MOUSE_DOWN_RIGHT:
                    painter.drawPixmap(QRect(x + 75, 5, 30, 30), self.app.rightDownPixmap, QRect(0, 0, 30, 30))
                else:
                    painter.drawPixmap(QRect(x + 75, 5, 30, 30), self.app.rightPixmap, QRect(0, 0, 30, 30))

                # Draw title text.
                painter.save()
                painter.setPen(QPen())
                font = self.font()
                font.setPointSizeF(font.pointSizeF() * 1.2)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(QRect(x + 120, 0, self.columnWidth * 12 - 32 * 2, 40),
                    Qt.AlignVCenter, str(1900 + month // 12))
                painter.restore()

                # Draw new pixmap.
                if self.mouse_down == MOUSE_DOWN_NEW:
                    painter.drawPixmap(QRect(x + 200, 5, 146, 30), self.app.newDownPixmap, QRect(0, 0, 146, 30))
                else:
                    painter.drawPixmap(QRect(x + 200, 5, 146, 30), self.app.newPixmap, QRect(0, 0, 146, 30))

            # Draw month header.
            painter.save()
            opt = QStyleOptionHeader()
            opt.rect = QRect(x, 40, self.columnWidth, 20)
            opt.textAlignment = Qt.AlignCenter
            if opt.rect.width() < 80:
                opt.text = MONTH_NAMES[month % 12][:3]
            else:
                opt.text = MONTH_NAMES[month % 12]
            self.style().drawControl(QStyle.CE_Header, opt, painter, self)
            painter.restore()

            painter.save()

            for day in range(1, days_of_month(month) + 1):
                date = qdate(month, day)

                # Draw horizontal lines.
                yStart = 40 + 20 + (day - 1) * self.rowHeight
                yEnd = yStart + self.rowHeight
                if date.dayOfWeek() == 7:
                    painter.setPen(QPen(Qt.gray, 2))
                else:
                    painter.setPen(QPen(Qt.gray))
                painter.drawLine(x + 1, yEnd, x + self.columnWidth, yEnd)

                # Draw overlays.
                for overlay in self.overlays:
                    if overlay.matches(month, day):
                        overlay.draw(painter, QRect(x, yStart, self.columnWidth + 1, self.rowHeight + 1))

                # Draw selection.
                if self.inSelection(date):
                    painter.fillRect(QRect(x, yStart, self.columnWidth + 1, self.rowHeight + 1), BLUE_LIGHT_COLOR)

                # Draw selection end.
                if date == self.selection_end:
                    painter.setPen(QPen(SOLARIZED_BASE_COLOR, 2))
                    painter.drawRect(QRect(x + 2, yStart + 2, self.columnWidth - 4, self.rowHeight - 4))

                # Draw day numbers.
                if self.rowHeight > 22 or day % 2 == 0:
                    font = self.font()
                    font.setPointSizeF(min(self.rowHeight * 0.6, font.pointSizeF()))
                    painter.setFont(font)
                    xAlign = min(self.rowHeight / 20.0, 1.0) * 25
                    painter.drawText(QRect(x, yStart, xAlign, self.rowHeight), Qt.AlignVCenter | Qt.AlignRight, str(day))

                    # Draw weekday names.
                    if self.columnWidth > 120:
                        painter.drawText(QRect(x + xAlign + 10, yStart, self.columnWidth - xAlign - 10, self.rowHeight), Qt.AlignVCenter, WEEKDAY_NAMES[date.dayOfWeek()])
                    elif self.columnWidth > 70:
                        painter.drawText(QRect(x + xAlign + 10, yStart, self.columnWidth - xAlign - 10, self.rowHeight), Qt.AlignVCenter, WEEKDAY_NAMES[date.dayOfWeek()][:2])

            painter.restore()

            # Draw vertical lines.
            painter.save()
            if month % 12 == 0:
                painter.setPen(QPen(Qt.gray))
                painter.drawLine(x - 2, 0, x - 2, 40 + 20 + self.rowHeight * max(days_of_month(month), days_of_month(month - 1)) - 1)
                painter.setPen(QPen(self.palette().window().color(), 2))
                painter.drawLine(x, 0, x, 40 + 20 + self.rowHeight * max(days_of_month(month), days_of_month(month - 1)))
                painter.setPen(QPen(Qt.gray))
                painter.drawLine(x + 1, 0, x + 1, 40 + 20 + self.rowHeight * max(days_of_month(month), days_of_month(month - 1)) - 1)
            else:
                painter.setPen(QPen(Qt.gray))
                painter.drawLine(x, 40 + 20, x, 40 + 20 + self.rowHeight * max(days_of_month(month), days_of_month(month - 1)) - 1)
            painter.restore()

        # Draw ranges.
        painter.save()
        for key in sorted(self.model.ranges):
            r = self.model.ranges[key]
            if not r.deleted:
                self.drawRange(painter, (GOLDEN_RATIO_CONJUGATE * r.index) % 1, r.start, r.end, r.color)
        painter.restore()

        # Mark current day.
        now = datetime.date.today()
        month = (now.year - 1900) * 12 + now.month - 1
        x = (month - self.offset) * self.columnWidth
        self.drawRaisedRect(painter, QRect(x, 40 + 20 + (now.day - 1) * self.rowHeight, self.columnWidth, self.rowHeight), Qt.red)

    def drawRange(self, painter, iterated_golden_ratio, start, end, color):
        from_month = (start.year() - 1900) * 12 + start.month() - 1
        from_day = start.day()

        to_month = (end.year() - 1900) * 12 + end.month() - 1
        to_day = end.day()

        radius = max(6, min(self.rowHeight * 0.5, self.columnWidth * 0.25) - 2) / 2

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, max(2.0, radius * 0.8)))

        from_y = 40 + 20 + self.rowHeight * (from_day - 0.5)
        to_y = 40 + 20 + self.rowHeight * (to_day - 0.5)

        for month in range(from_month, to_month + 1):
            x = (month - self.offset) * self.columnWidth + 5 + (self.columnWidth - 10) * iterated_golden_ratio

            if month == from_month:
                painter.drawEllipse(QPoint(x, from_y), radius, radius)
                painter.drawLine(x, from_y, x, to_y if month == to_month else self.height())

            if month == to_month:
                painter.drawEllipse(QPoint(x, to_y), radius, radius)
                painter.drawLine(x, from_y if month == from_month else 0, x, to_y)

            if month != to_month and month != from_month:
                painter.drawLine(x, 0, x, self.height())

    def drawRaisedRect(self, painter, rect, color):
        # Draw rect.
        pen = QPen(color, 4)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.drawRect(rect)

        # Draw inner shadow.
        painter.setPen(QPen(SHADOW_COLOR, 3))
        painter.drawLine(
            rect.x() + 6, rect.y() + 3,
            rect.x() + rect.width() - 4, rect.y() + 3)
        painter.drawLine(
            rect.x() + 3, rect.y() + 3,
            rect.x() + 3, rect.y() + rect.height() - 4)

        # Draw outer shadow.
        painter.drawLine(
            rect.x() + 3, rect.y() + rect.height() + 3,
            rect.x() + rect.width() + 3, rect.y() + rect.height() + 3)
        painter.drawLine(
            rect.x() + rect.width() + 3, rect.y() + 3,
            rect.x() + rect.width() + 3, rect.y() + rect.height())

        # Draw highlight.
        painter.setPen(QPen(LIGHT_COLOR, 1))
        painter.drawLine(
            rect.x() - 2, rect.y() - 2,
            rect.x() + rect.width() + 1, rect.y() -2)
        painter.drawLine(
            rect.x() - 2, rect.y() - 2,
            rect.x() - 2, rect.y() + rect.height() + 1)

        # Draw highlight shadow.
        painter.setPen(QPen(SHADOW_COLOR, 1))
        painter.drawLine(
            rect.x() - 2, rect.y() + rect.height() + 1,
            rect.x() + rect.width() + 1, rect.y() + rect.height() + 1)
        painter.drawLine(
            rect.x() + rect.width() + 1, rect.y() - 2,
            rect.x() + rect.width() + 1, rect.y() + rect.height() + 1)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Down, Qt.Key_Up, Qt.Key_Left, Qt.Key_Right, Qt.Key_PageUp, Qt.Key_PageDown, Qt.Key_Home):
            # Move selection end.
            if event.key() == Qt.Key_Down:
                self.selection_end = self.selection_end.addDays(1)
            elif event.key() == Qt.Key_Up:
                self.selection_end = self.selection_end.addDays(-1)
            elif event.key() == Qt.Key_Left:
                self.selection_end = self.selection_end.addMonths(-1)
            elif event.key() == Qt.Key_Right:
                self.selection_end = self.selection_end.addMonths(1)
            elif event.key() == Qt.Key_PageUp:
                self.selection_end = QDate(self.selection_end.year(), self.selection_end.month(), 1)
            elif event.key() == Qt.Key_PageDown:
                self.selection_end = QDate(
                    self.selection_end.year(),
                    self.selection_end.month(),
                    days_of_month((self.selection_end.year() - 1900) * 12 + self.selection_end.month() - 1))
            elif event.key() == Qt.Key_Home:
                self.selection_end = QDate.currentDate()

            # Also move selection start, unless modifier pressed.
            if not (event.modifiers() & Qt.ShiftModifier):
                self.selection_start = self.selection_end

            # Scroll into view.
            while self.selection_end < qdate(self.targetOffset, 1):
                self.onLeftClicked()
            while self.selection_end > qdate(self.targetOffset + 11, days_of_month(self.targetOffset + 11)):
                self.onRightClicked()

            self.repaint()
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.onNewClicked()

        return super(CalendarWidget, self).keyPressEvent(event)

    def monthForX(self, x):
        return int(self.offset + x / self.columnWidth)

    def dayForY(self, month, y):
        return max(1, min((y - 40 - 20) // self.rowHeight + 1, days_of_month(month)))

    def mouseDoubleClickEvent(self, event):
        if 40 + 20 < event.y():
            self.loadContextActions()
            if len(self.actions.actions()):
                self.showContextMenu(event.pos())
            else:
                self.onNewClicked()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            return

        month = self.monthForX(event.x())

        if 5 <= event.y() <= 35:
            x = (event.x() - self.offset * self.columnWidth) % (self.columnWidth * 12)
            if 5 <= x <= 35:
                self.mouse_down = MOUSE_DOWN_LEFT
                self.update(QRect(0, 0, self.width(), 40))
            if 40 <= x <= 70:
                self.mouse_down = MOUSE_DOWN_TODAY
                self.update(QRect(0, 0, self.width(), 40))
            if 75 <= x <= 105:
                self.mouse_down = MOUSE_DOWN_RIGHT
                self.update(QRect(0, 0, self.width(), 40))
            if 200 <= x <= 200 + 146:
                self.mouse_down = MOUSE_DOWN_NEW
                self.update(QRect(0, 0, self.width(), 40))
        elif 40 < event.y() < 40 + 20:
            self.mouse_down = MOUSE_DOWN_MONTH
            if not event.modifiers() & Qt.ShiftModifier:
                self.selection_start = qdate(month, 1)
            self.selection_end = qdate(month, days_of_month(month))
            self.repaint()
        elif 40 + 20 < event.y():
            self.mouse_down = MOUSE_DOWN_DAY
            self.selection_end = qdate(month, self.dayForY(month, event.y()))
            if not event.modifiers() & Qt.ShiftModifier:
                self.selection_start = self.selection_end
        else:
            self.mouse_down = MOUSE_DOWN_NONE

        return super(CalendarWidget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.button() == Qt.RightButton:
            return

        month = self.monthForX(event.x())

        if 40 < event.y() < 40 + 20:
            self.selection_end = qdate(month, days_of_month(month))
            if not event.modifiers() & Qt.ShiftModifier and not self.mouse_down in (MOUSE_DOWN_MONTH, MOUSE_DOWN_DAY):
                self.selection_start = qdate(month, 1)
            self.update()
        elif 40 + 20 < event.y():
            self.selection_end = qdate(month, self.dayForY(month, event.y()))
            self.update()

    def loadContextActions(self):
        # Clear.
        while self.actions.actions():
            self.actions.removeAction(self.actions.actions()[0])

        # Fill action group with entries in the selection.
        for key in sorted(self.model.ranges):
            r = self.model.ranges[key]
            if r.deleted:
                continue

            if r.end < self.selectionStart():
                continue
            if r.start > self.selectionEnd():
                continue

            if r.title:
                action = self.actions.addAction(r.title)
            else:
                action = self.actions.addAction("Eintrag %d" % r.index)

            action.setData(r.index)

            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(r.color)
            painter.drawEllipse(0, 0, 24, 24)
            painter.end()
            action.setIcon(QIcon(pixmap))

    def showContextMenu(self, pos):
        menu = QMenu()
        action = menu.addAction("Eintrag erstellen")
        action.triggered.connect(self.onNewClicked)

        if len(self.actions.actions()):
            menu.addSeparator()
            for action in self.actions.actions():
                menu.addAction(action)

        menu.exec_(self.mapToGlobal(pos))

    def mouseReleaseEvent(self, event):
        repaint = False

        if event.button() == Qt.RightButton and 40 + 20 < event.y():
            # Handle right clicks.
            month = self.monthForX(event.x())
            date = qdate(month, self.dayForY(month, event.y()))

            if not self.inSelection(date):
                self.selection_start = date
                self.selection_end = date
                repaint = True

            # Open context menu.
            self.loadContextActions()
            self.showContextMenu(event.pos())
        else:
            # Update the selection.
            self.mouseMoveEvent(event)
            repaint = True

        # Handle button clicks.
        if self.mouse_down:
            if 5 <= event.y() <= 35:
                x = (event.x() - self.offset * self.columnWidth) % (self.columnWidth * 12)
                if 5 <= x <= 35 and self.mouse_down == MOUSE_DOWN_LEFT:
                    self.onLeftClicked()
                elif 40 <= x <= 70 and self.mouse_down == MOUSE_DOWN_TODAY:
                    self.onTodayClicked()
                elif 75 <= x <= 105 and self.mouse_down == MOUSE_DOWN_RIGHT:
                    self.onRightClicked()
                elif 200 <= x <= 200 + 146 and self.mouse_down == MOUSE_DOWN_NEW:
                    self.onNewClicked()

            repaint = True
            self.mouse_down = MOUSE_DOWN_NONE

        if repaint:
            self.repaint()

    def sizeHint(self):
        return QSize(40 * 12, 40 + 20 + 10 * 31 + 10)


if __name__ == "__main__":
    app = Application(sys.argv)

    mainWindow = MainWindow(app)
    mainWindow.show()

    app.exec_()
