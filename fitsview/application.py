# -*- coding: utf-8 -*-
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
from __future__ import print_function, unicode_literals, division
from astropy import coordinates
from astropy import units
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from functools import wraps
from .fitsview import FitsView
import simplejson as json
import logging
from .common import *


class FitsViewer(QtWidgets.QApplication):
    """
    Application User interface
    """
    MaxRecentFiles = 5

    def hasImage(f):
        @wraps(f)
        def _hasImage(*args, **kwargs):
            if args[0].fits._gc is not None:
                return f(*args, **kwargs)
            else:
                return None
        return _hasImage

    def __init__(self, *args, **kwargs):
        QtWidgets.QApplication.__init__(self, *args, **kwargs)
        ui = uic.loadUi(get_ui_file('viewer.ui'))

        self.ui = ui
        self.about_ui = uic.loadUi(get_ui_file('about.ui'))
        self.fits = FitsView()
        self.fits.hoverSignal.connect(self.updateStatus)
        self._session_file = None
        ui.setCentralWidget(self.fits)
        
        ui.setWindowIcon(QtGui.QIcon(get_ui_file('icon.svg')))


        # Display tools
        ui.normalisation.addItems(list(self.fits.getScales().keys()))
        ui.normalisation.currentIndexChanged.connect(self.scaleChange)

        ui.colourMap.addItems(get_colour_maps())
        ui.colourMap.setCurrentIndex(get_colour_maps().index('gray'))

        ui.colourMap.currentIndexChanged.connect(self.cmapChange)
        ui.cutUpperValue.valueChanged.connect(self.fits.setUpperCut)
        ui.cutLowerValue.valueChanged.connect(self.fits.setLowerCut)

        # Connect up general actions
        ui.actionOpen.triggered.connect(self.addFiles)
        ui.actionAbout.triggered.connect(self.about_ui.show)
        ui.actionSave.triggered.connect(self.saveImage)
        ui.actionExport.triggered.connect(self.exportImage)
        ui.actionFit_to_Window.triggered.connect(self.fits.zoomFit)
        ui.actionZoom.triggered.connect(self.fits.zoom)
        ui.actionPan.triggered.connect(self.fits.pan)
        ui.actionNext.triggered.connect(self.__next__)
        ui.actionPrevious.triggered.connect(self.previous)
        ui.actionQuit.triggered.connect(self.quit)
        ui.actionLoadSession.triggered.connect(self.loadSession)
        ui.actionSaveSession.triggered.connect(self.saveSession)

        # Populate visible docks
        ui.menuDisplay.addAction(ui.displayDock.toggleViewAction())
        ui.menuDisplay.addAction(ui.fileDock.toggleViewAction())
        
        
        # Create recent file actions
        self.recent_file_acts = []
        for i in range(self.MaxRecentFiles):
            self.recent_file_acts.append(QtWidgets.QAction(self, visible=False,
                                         triggered=self.loadRecentSession))

        for i in range(self.MaxRecentFiles):
            self.ui.menuRecentFiles.addAction(self.recent_file_acts[i])

        self.aboutToQuit.connect(self.saveConfig)
        self.aboutToQuit.connect(self._autoSaveSession)

        
        # Connect matplot zoom/pan tools
        self.fits._mpl_toolbar._actions['pan'].toggled.connect(self.panUpdate)
        self.fits._mpl_toolbar._actions['zoom'].toggled.connect(self.zoomUpdate)

        self.status = QtWidgets.QLabel()
        self.status.setText('No Image Loaded')
        ui.statusBar().addWidget(self.status)

        self.model = QtGui.QStandardItemModel()
        ui.fileList.setModel(self.model)

        ui.fileList.selectionModel().selectionChanged.connect(self.setSelection)

        # Create image load throttler
        self._load_timer = QtCore.QTimer()
        self._load_timer.setSingleShot(True)
        self._load_timer.timeout.connect(self._setFileConcrete)

        ui.show()
        ui.raise_()
        self.loadConfig()

    def updateStatus(self, x, y, value, ra_d, dec_d):
        """
        Fetch information and update status bar text
        """
        try:
            coord = coordinates.SkyCoord(ra=ra_d, dec=dec_d, unit=(units.degree, units.degree))
            ra_str = ra_to_str(coord.ra.hour)
            dec_str = dec_to_str(coord.dec.degree)
        except coordinates.errors.BoundsError:
            ra_str = ''
            dec_str = ''
        co_str = "RA: {} Dec: {}".format(ra_str, dec_str)
        status = '{}\t\tX: {:>4}\tY: {:>4}\tValue: {}'.format(co_str, x, y, value)
        self.status.setText(status)

    def panUpdate(self):
        self.ui.actionPan.setChecked(self.fits._mpl_toolbar._actions["pan"].isChecked())

    def zoomUpdate(self):
        self.ui.actionZoom.setChecked(self.fits._mpl_toolbar._actions["zoom"].isChecked())

    def cmapChange(self, index):
        self.fits.setCMAP(get_colour_maps()[index])

    def scaleChange(self, index):
        self.fits.setScale(self.ui.normalisation.itemText(index))

    def addFiles(self, *args, **kwargs):
        """
        Add list of files
        Supply keyword argument 'files' or it will open a file open dialog
        """
        if not 'files' in kwargs:
            files, _ = QtWidgets.QFileDialog.getOpenFileNames(caption='Load Fits File', filter='Fits (*.fits *.fit)')
        else:
            files = kwargs['files']
        for fn in files:
            self.model.appendRow(FileItem(fn))
        if self.ui.fileList.currentIndex().row() < 0:
            self.ui.fileList.setCurrentIndex(self.model.index(0, 0))

    def setSelection(self, selection):
        """
        Set the file selection
        """
        try:
            self.setFile(selection[0].indexes()[0])
        except IndexError:
            pass

    def __next__(self):
        """
        Select next file in list
        """
        current = self.ui.fileList.currentIndex().row()
        if current < self.model.rowCount() - 1:
            self.ui.fileList.setCurrentIndex(self.model.index(current + 1, 0))

    def previous(self):
        """
        Select previous file in list
        """
        current = self.ui.fileList.currentIndex().row()
        if current > 0:
            self.ui.fileList.setCurrentIndex(self.model.index(current - 1, 0))

    def _setFileConcrete(self):
        """
        Actuallly perform a file load based on selection
        This operation can be slow (order 1s) so use the setFile method instead which
        throttles calls.
        """
        index = self._load_index
        item = self.model.itemFromIndex(index)
        self.fits.loadImage(str(item.fn))
        self.status.setText('')
        self.ui.infoExposureLabel.setText('{}s'.format(self.fits.getImageExposure()))
        dt = self.fits.getImageDateObserved()
        self.ui.infoDateLabel.setText(str(dt.date()))
        self.ui.infoTimeLabel.setText(str(dt.time()))

    def setFile(self, index):
        """
        Set the file from the list to display in the main widget
        """
        self._load_index = index
        self._load_timer.start(400)

    def _getSettings(self):
        """
        Return the QSettings object for the program
        """
        return QtCore.QSettings('Fits Viewer', 'pyfitsview')

    def _loadSessionConcrete(self, filen):
        """
        Perform a session load
        """
        f = open(filen)
        session = json.load(f)

        try:
            display = session['display']
            self.ui.cutLowerValue.setValue(display['lcut'])
            self.ui.cutUpperValue.setValue(display['ucut'])
            self.ui.colourMap.setCurrentIndex(display['cmap'])
            self.ui.normalisation.setCurrentIndex(display['scale'])
        except KeyError:
            logging.warning('display section missing or corrupted in session file')

        try:
            files = session['files']
            self.model.removeRows(0, self.model.rowCount())
            self.addFiles(files=files)
            self._session_file = filen
            self._addRecentFile(filen)
        except KeyError:
            logging.warning('files section missing or corrupted in session file')

    def _addRecentFile(self, filen):
        """
        Add a filename to the recent files list
        """
        try:
            self.recent_files.remove(filen)
        except ValueError:
            pass
        self.recent_files.insert(0, filen)
        self.recent_files = self.recent_files[:self.MaxRecentFiles]
        self._updateRecentFiles()

    def loadSession(self):
        """
        Show open dialog  and load a session file
        """
        filen = QtWidgets.QFileDialog.getOpenFileName(caption='Save Session')
        if filen != '':
            self._loadSessionConcrete(filen)

    def loadRecentSession(self):
        """
        Load a session from the recent file dialog
        """
        action = self.sender()
        if action:
            self._loadSessionConcrete(str(action.data().toPyObject()))

    def _autoSaveSession(self):
        """
        Save the current session
        """
        if self._session_file is not None:
            self._saveSessionConcrete(self._session_file)

    def _saveSessionConcrete(self, filen):
        """
        Perform a session load
        """
        f = open(filen, 'w')
        display = {
            'lcut': self.ui.cutLowerValue.value(),
            'ucut': self.ui.cutUpperValue.value(),
            'cmap': self.ui.colourMap.currentIndex(),
            'scale': self.ui.normalisation.currentIndex()
        }
        files = [str(self.model.item(i).fn) for i in range(self.model.rowCount())]
        session = {
            'display': display,
            'files': files,
        }
        json.dump(session, f)
        f.close()
        self._addRecentFile(filen)

    def saveSession(self):
        """
        Open a dialog and save the current sesion
        """
        filen = QtWidgets.QFileDialog.getSaveFileName(caption='Save Session')
        if filen != '':
            self._session_file = filen
            self._saveSessionConcrete(filen)

    def loadConfig(self):
        """
        Load the configuration
        """
        settings = self._getSettings()
        settings.beginGroup('Window')
        try:
            self.ui.restoreGeometry(settings.value('geometry', self.ui.saveGeometry(), type='QByteArray'))
        except TypeError:
            pass
        # Populate recent file list
        try:
            self.recent_files = settings.value('Files/recent', [], type='QStringList')
        except TypeError:
            self.recent_files = None
        if self.recent_files is None:
            self.recent_files = []
        else:
            self.recent_files = [i for i in list(self.recent_files) if os.path.isfile(i)]
        self._updateRecentFiles()

    def _updateRecentFiles(self):
        """
        Update the recent file menu based on the recent file list
        """
        for i in range(len(self.recent_files)):
            fn = self.recent_files[i]
            name = os.path.basename(str(fn))
            self.recent_file_acts[i].setText(name)
            self.recent_file_acts[i].setData(fn)
            self.recent_file_acts[i].setVisible(True)

    def saveConfig(self):
        """
        Save the configuration
        """
        settings = self._getSettings()
        settings.beginGroup('Window')
        settings.setValue('geometry', self.ui.saveGeometry())
        settings.endGroup()
        settings.setValue('Files/recent', self.recent_files)

    @hasImage
    def saveImage(self):
        """
        Open a dialog and save the curent fits image
        """
        filen = QtWidgets.QFileDialog.getSaveFileName(caption='Save Fits File')
        if filen != '':
            self.fits.saveImage(str(filen))
            self.status.showMessage('Saved to {}'.format(str(filen)))

    @hasImage
    def exportImage(self):
        """
        Open a dialog and export the current the image
        """
        filen = QtWidgets.QFileDialog.getSaveFileName(caption='Export to File')
        if filen != '':
            self.fits.saveImage(str(filen), export=True)
            self.status.showMessage('Exported to {}'.format(str(filen)))

