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

WEEKDAY_NAMES = ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag",
                 "Freitag", "Samstag", "Sonntag"]

GOLDEN_RATIO_CONJUGATE = 0.618033988749895


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
    elif date.month() == 12 and date.day() in (25, 26):
        holiday |= HOLIDAY_CHRISTMAS

    return holiday


class Application(QApplication):

    def __init__(self, argv):
        super(Application, self).__init__(argv)

        self.white = QColor(255, 255, 255)
        self.black = QColor(0, 0, 0)
        self.gray = QColor(191, 191, 191)
        self.shadow = QColor(0, 0, 0, 50)
        self.light = QColor(255, 255, 255, 200)
        self.red = QColor(255, 0, 0)
        self.lightRed = QColor(242, 219, 219, 100)


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


class HolidayOverlay(object):
    def __init__(self, app):
        self.brush = QBrush(app.lightRed)

    def matches(self, month, day):
        return is_holiday(month, day) &~ HOLIDAY_SUNDAY

    def draw(self, painter, rect):
        painter.fillRect(rect, self.brush)


class SundayOverlay(HolidayOverlay):
    def matches(self, month, day):
        return is_holiday(month, day) & HOLIDAY_SUNDAY


class FerienNiedersachsen(HolidayOverlay):
    def __init__(self, app):
        self.brush = QBrush(QColor(100, 200, 100, 50))

    def matches(self, month, day):
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

        return match


class VariantAnimation(QVariantAnimation):
    def updateCurrentValue(self, value):
        pass


MOUSE_DOWN_NONE = 0
MOUSE_DOWN_MONTH = 1
MOUSE_DOWN_DAY = 2


class CalendarWidget(QWidget):

    def __init__(self, app, parent=None):
        super(CalendarWidget, self).__init__(parent)
        self.app = app

        self.setFocusPolicy(Qt.StrongFocus)

        self.targetOffset = (QDate.currentDate().year() - 1900) * 12
        self.offset = self.targetOffset

        self.overlays = [
                FerienNiedersachsen(self.app),
                HolidayOverlay(self.app),
                SundayOverlay(self.app),
            ]

        self.selection_end = QDate.currentDate()
        self.selection_start = self.selection_end
        self.mouse_down = MOUSE_DOWN_NONE

        self.animation = VariantAnimation(self)
        self.animation.setEasingCurve(QEasingCurve(QEasingCurve.InOutQuad))
        self.animation.valueChanged.connect(self.onAnimate)
        self.animation.setDuration(1000)
        self.animationEnabled = False

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

    def onAnimate(self, value):
        if not self.animationEnabled:
            return

        self.offset = value
        self.repaint()

    def inSelection(self, date):
        start = min(self.selection_start, self.selection_end)
        end = max(self.selection_start, self.selection_end)
        return start <= date <= end

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
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

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
            for day in range(1, days_of_month(month) + 1):
                date = qdate(month, day)

                # Draw horizontal lines.
                yStart = 40 + 20 + (day - 1) * self.rowHeight()
                yEnd = yStart + self.rowHeight()
                if date.dayOfWeek() == 7:
                    painter.setPen(QPen(self.app.gray, 2))
                else:
                    painter.setPen(QPen(self.app.gray))
                painter.drawLine(x + 1, yEnd, x + self.columnWidth(), yEnd)

                # Draw overlays.
                for overlay in self.overlays:
                    if overlay.matches(month, day):
                        overlay.draw(painter, QRect(x, yStart, self.columnWidth() + 1, self.rowHeight() + 1))

                # Draw selection.
                if self.inSelection(date):
                    painter.fillRect(QRect(x, yStart, self.columnWidth() + 1, self.rowHeight() + 1), QColor(91, 91, 255, 50))

                # Draw selection end.
                if date == self.selection_end:
                    painter.setPen(QPen(QColor(30, 30, 200), 2))
                    painter.drawRect(QRect(x + 2, yStart + 2, self.columnWidth() - 4, self.rowHeight() - 4))

                # Draw day numbers.
                if self.rowHeight() > 22 or day % 2 == 0:
                    font = self.font()
                    font.setPointSizeF(min(self.rowHeight() * 0.6, font.pointSizeF()))
                    painter.setFont(font)
                    xAlign = min(self.rowHeight() / 20.0, 1.0) * 25
                    painter.drawText(QRect(x, yStart, xAlign, self.rowHeight()), Qt.AlignVCenter | Qt.AlignRight, str(day))

                    # Draw weekday names.
                    if self.columnWidth() > 120:
                        painter.drawText(QRect(x + xAlign + 10, yStart, self.columnWidth() - xAlign - 10, self.rowHeight()), Qt.AlignVCenter, WEEKDAY_NAMES[date.dayOfWeek()])
                    elif self.columnWidth() > 70:
                        painter.drawText(QRect(x + xAlign + 10, yStart, self.columnWidth() - xAlign - 10, self.rowHeight()), Qt.AlignVCenter, WEEKDAY_NAMES[date.dayOfWeek()][:2])

            painter.restore()

            # Draw vertical lines.
            painter.save()
            if month % 12 == 0:
                painter.setPen(QPen(self.app.gray))
                painter.drawLine(x - 2, 0, x - 2, 40 + 20 + self.rowHeight() * max(days_of_month(month), days_of_month(month - 1)) - 1)
                painter.setPen(QPen(self.palette().window().color(), 2))
                painter.drawLine(x, 0, x, 40 + 20 + self.rowHeight() * max(days_of_month(month), days_of_month(month - 1)))
                painter.setPen(QPen(self.app.gray))
                painter.drawLine(x + 1, 0, x + 1, 40 + 20 + self.rowHeight() * max(days_of_month(month), days_of_month(month - 1)) - 1)
            else:
                painter.setPen(QPen(self.app.gray))
                painter.drawLine(x, 40 + 20, x, 40 + 20 + self.rowHeight() * max(days_of_month(month), days_of_month(month - 1)) - 1)
            painter.restore()

        painter.save()
        self.latest_range_offset = 0.0
        self.drawRange(painter, 1368, 6, 1370, 12, QColor(0, 155, 0))
        self.drawRange(painter, 1370, 7, 1370, 26, QColor(155, 155, 0))
        self.drawRange(painter, 1372, 20, 1372, 20, QColor(0, 0, 155))
        self.drawRange(painter, 1375, 15, 1375, 21, QColor(0, 155, 155))
        painter.restore()

        # Mark current day.
        now = datetime.date.today()
        month = (now.year - 1900) * 12 + now.month - 1
        x = (month - self.offset) * self.columnWidth()
        self.drawRaisedRect(painter, QRect(x, 40 + 20 + (now.day - 1) * self.rowHeight(), self.columnWidth(), self.rowHeight()), self.app.red)

    def drawRange(self, painter, from_month, from_day, to_month, to_day, color):
        self.latest_range_offset += GOLDEN_RATIO_CONJUGATE
        self.latest_range_offset %= 1

        radius = max(6, min(self.rowHeight() * 0.5, self.columnWidth() * 0.25) - 2)

        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, max(2.0, radius * 0.8)))

        from_y = 40 + 20 + self.rowHeight() * (from_day - 0.5)
        to_y = 40 + 20 + self.rowHeight() * (to_day - 0.5)

        for month in range(from_month, to_month + 1):
            x = (month - self.offset) * self.columnWidth() + self.columnWidth() * self.latest_range_offset

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
        painter.setPen(QPen(self.app.shadow, 3))
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
        painter.setPen(QPen(self.app.light, 1))
        painter.drawLine(
            rect.x() - 2, rect.y() - 2,
            rect.x() + rect.width() + 1, rect.y() -2)
        painter.drawLine(
            rect.x() - 2, rect.y() - 2,
            rect.x() - 2, rect.y() + rect.height() + 1)

        # Draw highlight shadow.
        painter.setPen(QPen(self.app.shadow, 1))
        painter.drawLine(
            rect.x() - 2, rect.y() + rect.height() + 1,
            rect.x() + rect.width() + 1, rect.y() + rect.height() + 1)
        painter.drawLine(
            rect.x() + rect.width() + 1, rect.y() - 2,
            rect.x() + rect.width() + 1, rect.y() + rect.height() + 1)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Down, Qt.Key_Up, Qt.Key_Left, Qt.Key_Right):
            # Move selection end.
            if event.key() == Qt.Key_Down:
                self.selection_end = self.selection_end.addDays(1)
            elif event.key() == Qt.Key_Up:
                self.selection_end = self.selection_end.addDays(-1)
            elif event.key() == Qt.Key_Left:
                self.selection_end = self.selection_end.addMonths(-1)
            elif event.key() == Qt.Key_Right:
                self.selection_end = self.selection_end.addMonths(1)

            # Also move selection start, unless modifier pressed.
            if not (event.modifiers() & Qt.ShiftModifier):
                self.selection_start = self.selection_end

            # Scroll into view.
            while self.selection_end < qdate(self.targetOffset, 1):
                self.onLeftClicked()
            while self.selection_end > qdate(self.targetOffset + 11, days_of_month(self.targetOffset + 11)):
                self.onRightClicked()

            self.repaint()

        return super(CalendarWidget, self).keyPressEvent(event)

    def monthForX(self, x):
        return int(self.offset + x / self.columnWidth())

    def dayForY(self, month, y):
        return max(1, min((y - 40 - 20) // self.rowHeight() + 1, days_of_month(month)))

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            return

        month = self.monthForX(event.x())

        if 40 < event.y() < 40 + 20:
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

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            month = self.monthForX(event.x())
            date = qdate(month, self.dayForY(month, event.y()))

            if not self.inSelection(date):
                self.selection_start = date
                self.selection_end = date
                self.repaint()

            print "Right click!"
            return

        self.mouseMoveEvent(event)
        self.repaint()


if __name__ == "__main__":
    app = Application(sys.argv)

    mainWindow = MainWindow(app)
    mainWindow.show()

    app.exec_()
