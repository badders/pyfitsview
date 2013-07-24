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
from astropy import coordinates
from astropy import units
from PyQt4 import QtGui, QtCore, uic
from functools import wraps
from fitsview import FitsView
from common import *


class FitsViewer(QtGui.QApplication):
    """
    Application User interface
    """
    def hasImage(f):
        @wraps(f)
        def _hasImage(*args, **kwargs):
            if args[0].fits.gc is not None:
                return f(*args, **kwargs)
            else:
                return None
        return _hasImage

    def __init__(self, *args, **kwargs):
        global USE_CAMERA
        QtGui.QApplication.__init__(self, *args, **kwargs)
        self.ui = uic.loadUi(get_ui_file('viewer.ui'))
        self.about_ui = uic.loadUi(get_ui_file('about.ui'))
        self.fits = FitsView()
        self.fits.hoverSignal.connect(self.updateStatus)
        self.ui.setCentralWidget(self.fits)

        self.ui.setWindowIcon(QtGui.QIcon(get_ui_file('icon.svg')))

        if use_camera():
            ports = list_serial_ports()
            if len(ports) == 0:
                self.ui.allSkyControls.hide()
            else:
                self.ui.portChoice.addItems(ports)
                self.ui.takeImage.clicked.connect(self.takeImage)

        self.ui.normalisation.addItems(self.fits.getScales().keys())
        self.ui.normalisation.currentIndexChanged.connect(self.scaleChange)

        self.ui.colourMap.addItems(get_colour_maps())
        self.ui.colourMap.setCurrentIndex(get_colour_maps().index('gray'))

        self.ui.colourMap.currentIndexChanged.connect(self.cmapChange)
        self.ui.cutUpperValue.valueChanged.connect(self.fits.setUpperCut)
        self.ui.cutLowerValue.valueChanged.connect(self.fits.setLowerCut)

        self.ui.actionOpen.triggered.connect(self.addFiles)
        self.ui.actionAbout.triggered.connect(self.about)
        self.ui.actionSave.triggered.connect(self.saveImage)
        self.ui.actionExport.triggered.connect(self.exportImage)
        self.ui.actionFit_to_Window.triggered.connect(self.fits.zoomFit)
        self.ui.actionZoom.triggered.connect(self.fits.zoom)
        self.ui.actionPan.triggered.connect(self.fits.pan)
        self.ui.actionNext.triggered.connect(self.next)
        self.ui.actionPrevious.triggered.connect(self.previous)
        self.ui.actionQuit.triggered.connect(self.quit)

        self.ui.menuDisplay.addAction(self.ui.displayDock.toggleViewAction())
        self.ui.menuDisplay.addAction(self.ui.toolsDock.toggleViewAction())
        self.ui.menuDisplay.addAction(self.ui.fileDock.toggleViewAction())

        self.aboutToQuit.connect(self.saveConfig)

        self.fits._mpl_toolbar._actions['pan'].toggled.connect(self.panUpdate)
        self.fits._mpl_toolbar._actions['zoom'].toggled.connect(self.zoomUpdate)

        self.status = QtGui.QLabel()
        self.status.setText('No Image Loaded')
        self.ui.statusBar().addWidget(self.status)

        self.model = QtGui.QStandardItemModel()
        self.ui.fileList.setModel(self.model)
        self.ui.fileList.selectionModel().selectionChanged.connect(self.setSelection)

        self.ui.tabifyDockWidget(self.ui.toolsDock, self.ui.displayDock)

        self.ui.show()
        self.loadConfig()

    def updateStatus(self, x, y, value, ra_d, dec_d):
        try:
            coord = coordinates.ICRSCoordinates(ra=ra_d, dec=dec_d, unit=(units.degree, units.degree))
            ra_str = coord.ra.format(units.hour)
            dec_str = coord.dec.format(units.degree, alwayssign=True)
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
        if not 'files' in kwargs:
            files = QtGui.QFileDialog.getOpenFileNames(caption='Load Fits File', filter='*.fits')
        else:
            files = kwargs['files']
        for fn in files:
            self.model.appendRow(FileItem(fn))
        if self.ui.fileList.currentIndex().row() < 0:
            self.ui.fileList.setCurrentIndex(self.model.index(0, 0))

    def setSelection(self, selection):
        self.setFile(selection[0].indexes()[0])

    def next(self):
        current = self.ui.fileList.currentIndex().row()
        if current < self.model.rowCount() - 1:
            self.ui.fileList.setCurrentIndex(self.model.index(current + 1, 0))

    def previous(self):
        current = self.ui.fileList.currentIndex().row()
        if current > 0:
            self.ui.fileList.setCurrentIndex(self.model.index(current - 1, 0))

    def setFile(self, index):
        item = self.model.itemFromIndex(index)
        self.fits.loadImage(str(item.fn))
        self.status.setText('')
        self.ui.infoExposureLabel.setText('{}s'.format(self.fits.getImageExposure()))
        dt = self.fits.getImageDateObserved()
        self.ui.infoDateLabel.setText(str(dt.date()))
        self.ui.infoTimeLabel.setText(str(dt.time()))

    def _getSettings(self):
        """
        Return the QSettings object for the program
        """
        return QtCore.QSettings('Fits Viewer', 'pyfitsview')

    def loadConfig(self):
        settings = self._getSettings()
        settings.beginGroup('Window')
        self.ui.restoreGeometry(settings.value('geometry', self.ui.saveGeometry()).toPyObject())
        settings.endGroup()
        settings.beginGroup('Display')
        self.ui.cutLowerValue.setValue(settings.value('lcut', self.ui.cutLowerValue.value()).toPyObject())
        self.ui.cutUpperValue.setValue(settings.value('ucut', self.ui.cutUpperValue.value()).toPyObject())
        self.ui.colourMap.setCurrentIndex(settings.value('cmap', self.ui.colourMap.currentIndex()).toPyObject())
        self.ui.normalisation.setCurrentIndex(settings.value('scale', self.ui.normalisation.currentIndex()).toPyObject())
        settings.endGroup()

    def saveConfig(self):
        settings = self._getSettings()
        settings.beginGroup('Window')
        settings.setValue('geometry', self.ui.saveGeometry())
        settings.endGroup()
        settings.beginGroup('Display')
        settings.setValue('lcut', self.ui.cutLowerValue.value())
        settings.setValue('ucut', self.ui.cutUpperValue.value())
        settings.setValue('cmap', self.ui.colourMap.currentIndex())
        settings.setValue('scale', self.ui.normalisation.currentIndex())
        settings.endGroup()

    @hasImage
    def saveImage(self):
        filen = QtGui.QFileDialog.getSaveFileName(caption='Save Fits File')
        if filen != '':
            self.fits.saveImage(str(filen))
            self.status.showMessage('Saved to {}'.format(str(filen)))

    @hasImage
    def exportImage(self):
        filen = QtGui.QFileDialog.getSaveFileName(caption='Export to File')
        if filen != '':
            self.fits.saveImage(str(filen), export=True)
            self.status.showMessage('Exported to {}'.format(str(filen)))

    def about(self):
        self.about_ui.show()

    def takeImage(self):
        port = str(self.ui.portChoice.currentText())
        self.progress = QtGui.QProgressDialog('Downloading Image from Camera ...', '', 0, 0)
        self.progress.setCancelButton(None)
        self.progress.setValue(0)
        self.progress.setMinimum(0)
        self.progress.setMaximum(100.0)
        self.progress.setModal(True)
        self.progress.show()
        QtGui.QApplication.processEvents()
        self.fits.takeImage(self.ui.exposureTime.value(), self._takeImageProgress, dev=port)
        self.progress.hide()
        self.status.setText('')

    def _takeImageProgress(self, percent):
        self.progress.setValue(percent)
        QtGui.QApplication.processEvents()
