# -*- coding: utf-8 -*-
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pdb, sys, os, sip
from puddlestuff.audioinfo import GENRES, INFOTAGS, READONLY
from puddlestuff.audioinfo.util import commonimages
from puddlestuff.puddleobjects import ListButtons, PuddleConfig, PicWidget
import puddlestuff.resource as resource
pyqtRemoveInputHook()
from puddlestuff.constants import LEFTDOCK, SELECTIONCHANGED
import time

def timemethod(method):
    def f(*args, **kwargs):
        name = method.__name__
        t = time.time()
        ret = method(*args, **kwargs)
        print name, time.time() - t
        return ret
    return f

def loadsettings(filepath = None):
    settings = PuddleConfig()
    if filepath:
        setting.filename = filepath
    else:
        settings.filename = os.path.join(settings.savedir, 'tagpanel')
    numrows = settings.get('panel','numrows',-1, True)
    if numrows > -1:
        sections = settings.sections()
        d = {}
        for row in xrange(numrows):
            section = unicode(row)
            tags = settings.get(section, 'tags', [''])
            titles = settings.get(section, 'titles', [''])
            d[row] = zip(titles, tags)
    else:
        titles = ['&Artist', '&Title', 'Al&bum', 'T&rack', u'&Year', "&Genre", '&Comment']
        tags = ['artist', 'title', 'album', 'track', u'year', 'genre', 'comment']
        newtags = zip(titles, tags)
        d = {0:[newtags[0]], 1:[newtags[1]], 2: [newtags[2]],
             3:[newtags[3], newtags[4], newtags[5]] ,
             4:[newtags[6]]}
    return d

def savesettings(d, filepath=None):
    settings = PuddleConfig()
    if filepath:
        setting.filename = filepath
    else:
        settings.filename = os.path.join(settings.savedir, 'tagpanel')
    settings.set('panel', 'numrows', unicode(len(d)))
    for row, rowtags in d.items():
        settings.set(unicode(row), 'tags', [z[1] for z in rowtags])
        settings.set(unicode(row), 'titles', [z[0] for z in rowtags])

class Thread(QThread):
    def __init__(self, values, parent=None):
        self._values = values
        QThread.__init__(self, parent)

    def run(self):
        self.emit(SIGNAL('update'), self._values)

class FrameCombo(QGroupBox):
    """A group box with combos that allow to edit
    tags individually if so inclined.

    tags should be a list with the tags
    that each combo box should hold specified
    in the form [(Display Value, internal tag)]
    .e.g [("Artist","artist"), ("Track Number", "track")]

    Individual comboboxes can be accessed by using FrameCombo.combos
    which is a dictionary key = tag, value = respective combobox.
    """

    def __init__(self,tags = None,parent= None, status=None):
        self.settingsdialog = SettingsWin
        QGroupBox.__init__(self,parent)
        self.emits = ['onetomany']
        self.receives = [(SELECTIONCHANGED, self.fillCombos)]
        self.combos = {}
        self.labels = {}
        self._status = status

    def disableCombos(self):
        for z in self.combos:
            if z  == "__image":
                self.combos[z].setImages(None)
            else:
                self.combos[z].clear()
            self.combos[z].setEnabled(False)

    def fillCombos(self, *args):
        audios = self._status['selectedfiles']
        t = time.time()
        combos = self.combos

        if not audios:
            for combo in combos.values():
                combo.clear()
                combo.setEnabled(False)
            return

        self.initCombos(True)
        tags = dict([(tag, set()) for tag in combos])
        for audio in audios:
            for tag in tags:
                try:
                    if tag in audio.preview:
                        value = audio.preview[tag]
                    else:
                        value = audio[tag]
                    if isinstance(value, basestring):
                        tags[tag].add(value)
                    else:
                        tags[tag].add("\\\\".join(value))
                except KeyError:
                    tags[tag].append("")

        for field, values in tags.iteritems():
            if field in combos:
                combo = combos[field]
                values = sorted(values)
                combo.addItems(["<keep>", "<blank>"] + values)
                if len(values) == 1:
                    combo.setCurrentIndex(2)
                else:
                    combo.setCurrentIndex(0)

        if 'genre' in tags and len(tags['genre']) == 1:
            combo = combos['genre']
            values = sorted(tags['genre'])
            index = combo.findText(values[0])
            if index > -1:
                combo.setCurrentIndex(index)
            else:
                combo.setEditText(values[0])
        else:
            combos['genre'].setCurrentIndex(0)

    def save(self):
        """Writes the tags of the selected files to the values in self.combogroup.combos."""
        combos = self.combos
        tags = {}

        images = self._status['images']
        if images is not None:
            tags['__image'] = images
        for tag, combo in combos.items():
            if tag == '__image':
                continue
            curtext = unicode(combo.currentText())
            if curtext == "<blank>": tags[tag] = []
            elif curtext == "<keep>": pass
            else:
                if tag in INFOTAGS:
                    tags[tag] = curtext
                else:
                    tags[tag] = curtext.split("\\\\")
        self.emit(SIGNAL('onetomany'), tags)
        if 'genre' in combos:
            combo = combos['genre']
            genre = unicode(combo.currentText())
            genres = self._status['genres']
            if genre not in genres:
                self._status['genres'] = genres + [genre]

    def setCombos(self, rowtags):
        """Creates a vertical column of comboboxes.
        tags are tags is usual in the (tag, backgroundvalue) case[should be enumerable].
        rows are a dictionary with each key being a list of the indexes of tags that should
        be one one row.

        E.g Say you wanted to have the artist, album, title, and comments on
        seperate rows. But then you want year, genre and track on one row. With that
        row being before the comments row. You'd do something like...

        >>>tags = [('Artist', 'artist'), ('Title', 'title'), ('Album', 'album'),
        ...        ('Track', 'track'), ("Comments",'comment'), ('Genre', 'genre'), (u'Year', u'date')]
        >>>rows = {0:[0], 1:[1], 2:[2], 3[3,4,6],4:[5]
        >>>f = FrameCombo()
        >>>f.setCombo(tags,rows)"""
        #pdb.set_trace()
        if self.combos:
            vbox = self.layout()
            for box, control in self._hboxes:
                box.removeWidget(control)
                sip.delete(control)
                if not box.count():
                    vbox.removeItem(box)
                    sip.delete(box)
        else:
            vbox = QVBoxLayout()
            vbox.setMargin(0)
        self.combos = {}
        self.labels = {}
        self._hboxes = []

        j = 0
        for row, tags in sorted(rowtags.items()):
            labelbox = QHBoxLayout()
            labelbox.setContentsMargins(6, 1, 1, 1)
            widgetbox = QHBoxLayout()
            widgetbox.setMargin(0)
            for tag in tags:
                tagval = tag[1]
                self.labels[tagval] = QLabel(tag[0])
                self.combos[tagval] = QComboBox()
                self.combos[tagval].setInsertPolicy(QComboBox.NoInsert)
                self.combos[tagval].setEditable(True)
                self.labels[tagval].setBuddy(self.combos[tagval])
                labelbox.addWidget(self.labels[tagval])
                widgetbox.addWidget(self.combos[tagval])
                self._hboxes.append((labelbox, self.labels[tagval]))
                self._hboxes.append((widgetbox, self.combos[tagval]))
            vbox.addLayout(labelbox)
            vbox.addLayout(widgetbox)
        vbox.addStrut(0)
        self.setLayout(vbox)
        QApplication.processEvents()
        self.setMaximumHeight(self.sizeHint().height())

    def initCombos(self, enable=False):
        """Clears the comboboxes and adds two items, <keep> and <blank>.
        If <keep> is selected and the tags in the combos are saved,
        then they remain unchanged. If <blank> is selected, then the tag is removed"""
        for combo in self.combos.values():
            combo.clear()
            combo.setEnabled(enable)

        if 'genre' in self.combos:
            pass
            self.combos['genre'].addItems(self._status['genres'])

    def reloadCombos(self, tags):
        self.setCombos(tags)

    def loadSettings(self):
        self.setCombos(loadsettings())

class PuddleTable(QTableWidget):
    def __init__(self, columns=None, defaultvals=None, parent=None):
        QTableWidget.__init__(self, parent)
        self._default = defaultvals
        self.verticalHeader().hide()
        if columns:
            self.setColumnCount(len(columns))
            self.setHorizontalHeaderLabels(columns)
            self.horizontalHeader().setStretchLastSection(True)

    def add(self, texts = None):
        row = self.rowCount()
        item = self.horizontalHeaderItem
        if self._default and (not texts):
            texts = self._default
        elif not texts:
            texts = [item(z).text() for z in range(self.columnCount())]
        self.insertRow(row)
        for column, v in enumerate(texts):
            self.setItem(row, column, QTableWidgetItem(v))

    def remove(self):
        self.removeRow(self.currentRow())

    def moveUp(self):
        row = self.currentRow()
        if row <= 0:
            return
        previtems = self.texts(row - 1)
        newitems = self.texts(row)
        self.setRowTexts(row, previtems)
        self.setRowTexts(row - 1, newitems)
        curitem = self.item(row-1, self.currentItem().column())
        self.setCurrentItem(curitem)

    def moveDown(self):
        row = self.currentRow()
        if row >= self.rowCount() - 1:
            return
        previtems = self.texts(row + 1)
        newitems = self.texts(row)
        self.setRowTexts(row, previtems)
        self.setRowTexts(row + 1, newitems)
        curitem = self.item(row+1, self.currentItem().column())
        self.setCurrentItem(curitem)

    rows = property(lambda x: xrange(x.rowCount()))

    def setRowTexts(self, row, texts):
        item = self.item
        for column, text in zip(range(self.columnCount()), texts):
            item(row, column).setText(text)

    def texts(self, row):
        item = self.item
        return [unicode(item(row, z).text()) for z in range(self.columnCount())]

    def items(self, row):
        item = self.item
        return [item(row, z) for z in range(self.columnCount())]

    def text(self, row, column):
        return unicode(self.item(row, column).text())

TABLEWIDGETBG = QTableWidgetItem().background()
RED = QBrush(Qt.red)

class SettingsWin(QWidget):
    title = 'Tag Panel'
    def __init__(self, parent = None, status=None):
        QDialog.__init__(self, parent)
        self._table = PuddleTable(['Title', 'Tag', 'Row'],
                                        ['Title', 'tag', unicode(0)], self)
        buttons = ListButtons()
        buttons.connectToWidget(self._table, add=self.add, edit=self.edit,
                    moveup=self._table.moveUp, movedown=self._table.moveDown,
                    duplicate=self.duplicate)

        hbox = QHBoxLayout()
        hbox.addWidget(self._table, 1)
        hbox.addLayout(buttons, 0)
        self.setLayout(hbox)

        self.connect(self._table, SIGNAL('cellChanged(int,int)'), self._checkItem)
        self.fill()

    def add(self, texts = None):
        table = self._table
        if not texts:
            text = table.text
            table.add(['Title', 'tag', max([text(row, 2) for row in table.rows])])
        else:
            table.add(texts)
        item = table.item(table.rowCount() - 1, 0)
        table.setCurrentItem(item)
        table.editItem(item)

    def fill(self):
        d = loadsettings()
        for row in d:
            for z in d[row]:
                self._table.add(z + (unicode(row),))

    def applySettings(self, control = None):
        texts = self._table.texts
        d = {}
        for row in self._table.rows:
            l = texts(row)
            try:
                l[2] = int(l[2])
            except ValueError:
                return 'All row numbers should be integers.'
            try:
                d[l[2]].append(l[:-1])
            except KeyError:
                d[l[2]] = [l[:-1]]
        d = dict([(i,d[v]) for i,v in enumerate(sorted(d))]) #consecutive rows
        savesettings(d)
        control.setCombos(d)


    def edit(self):
        self._table.editItem(self._table.currentItem())

    def _checkItem(self, row, column):
        table = self._table
        if column == 2:
            try:
               int(table.text(row, column))
               table.item(row, column).setBackground(TABLEWIDGETBG)
            except ValueError:
                i = table.item(row, column)
                i.setBackground(RED)

    def duplicate(self):
        table = self._table
        row = table.currentRow()
        if row < 0: return
        self.add(table.texts(row))


control = ('Tag Panel', FrameCombo, LEFTDOCK, True)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SettingsWin()
    win.show()
    app.exec_()