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
import sys
import os
import matplotlib
import astropy.io.fits as fits
from astropy import coordinates
from astropy import units
import aplpy
from collections import OrderedDict
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg
from matplotlib.figure import Figure
from PyQt4 import QtGui, QtCore, uic
from functools import wraps

try:
    from serial.tools import list_ports
    from allsky import AllSkyCamera
    USE_CAMERA = True
except ImportError:
    USE_CAMERA = False

ABOUT_TEXT = """Fits Image Viewer
Copyright Tom Badran 2013
http://github.com/badders/pyfitsview

Licensed under the GPL

Makes use of the following projects:
* APLpy - http://aplpy.github.io/
* astropy - https://astropy.readthedocs.org/en/stable/
* PyQt4 - http://www.riverbankcomputing.com/software/pyqt/
* Matplotlib - http://www.matplotlib.org/
"""


def getUiFile(name):
    """
    Helper function to automatically correct path for files in ui/
    """
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ui', name)


def getConfigFile():
    """
    Return path to the configuration files
    """
    return os.path.join(os.environ['HOME'], '.fitsview')


def list_serial_ports():
    """
    Helper function to get a list of serial ports.
    Currently strips out bluetooth ports
    """
    ports = []
    for x in list_ports.comports():
        port = x[0]
        if port.count('Bluetooth') == 0:
            ports.append(port)
    return ports


def get_colour_maps():
    """
    Get the list of available colour maps from the matplotlib library
    """
    maps = matplotlib.cm.datad.keys()
    maps.sort(key=str.lower)
    return maps


class FitsView(FigureCanvasQTAgg):
    """
    A FITS image viewer base on matplotlib, rendering is done using the astropy
    library.
    """
    hoverSignal = QtCore.pyqtSignal(int, int, int, float, float)

    def refresh(f):
        @wraps(f)
        def _refresh(*args, **kwargs):
            ret = f(*args, **kwargs)
            fv = args[0]
            if not fv._timer:
                QtCore.QTimer.singleShot(100, fv._refreshConcrete)
                fv._timer = True
            return ret
        return _refresh

    def hasImage(f):
        @wraps(f)
        def _hasImage(*args, **kwargs):
            if args[0]._gc is not None:
                return f(*args, **kwargs)
            else:
                return None
        return _hasImage

    def __init__(self):
        self._fig = Figure(dpi=96)
        FigureCanvasQTAgg.__init__(self, self._fig)
        FigureCanvasQTAgg.setSizePolicy(self,
                                        QtGui.QSizePolicy.Expanding,
                                        QtGui.QSizePolicy.Expanding)
        self._fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self._mpl_toolbar = NavigationToolbar2QTAgg(self, self)
        self._mpl_toolbar.hide()
        self.__taking = False
        self._scale = 'log'
        self._scales = OrderedDict()
        self._scales['Logarithmic'] = 'log'
        self._scales['Linear'] = 'linear'
        self._scales['Square Root'] = 'sqrt'
        self._scales['Power'] = 'power'
        self._scales['Arc Sinh'] = 'arcsinh'
        self._gc = None
        self._upperCut = 99.75
        self._lowerCut = 0.25
        self._cmap = 'gray'
        self._timer = False

    @hasImage
    def _refreshConcrete(self):
        self._gc.show_colorscale(pmin=self._lowerCut, pmax=self._upperCut,
                                 stretch=self._scale, aspect='auto',
                                 cmap=self._cmap)
        self._gc.axis_labels.hide()
        self._gc.tick_labels.hide()
        self._gc.ticks.hide()
        self._gc.frame.set_linewidth(0)
        self._timer = False

    @refresh
    def loadImage(self, filename):
        """
        Load a fits image from disk
        filename -- full path to the image file
        """
        self._fig.clear()
        self._gc = aplpy.FITSFigure(filename, figure=self._fig)

    @refresh
    def takeImage(self, exposure, progress, dev='/dev/tty.usberial'):
        """
        Take an image using the All Sky camera
        exposure -- Desired exposure time
        progress -- Function for progress update callback
        dev -- Path to serial device
        """
        if self.__taking:
            return
        self._fig.clear()
        self._taking = True
        cam = AllSkyCamera(dev)
        image = cam.get_image(exposure=exposure, progress_callback=progress)
        self._max = image.data.max()
        self._gc = aplpy.FITSFigure(image, figure=self._fig)
        self._taking = False

    @refresh
    def setCMAP(self, cmap):
        """
        Set the colourmap for the image display
        cmap -- colourmap name (see matplotlib.cm)
        """
        self._cmap = cmap

    @refresh
    def setUpperCut(self, value):
        """
        Set the upper limit for display cut
        value -- percentage for upper limit
        """
        self._upperCut = value

    @refresh
    def setLowerCut(self, value):
        """
        Set the lower limit for display cut
        value -- percentage for the lower limit
        """
        self._lowerCut = value

    def getScales(self):
        """
        return the available normalisation scales
        """
        return self._scales

    @hasImage
    @refresh
    def setScale(self, scale):
        """
        Set normalisation scale
        scale -- desired scale
        """
        self._scale = self._scales[str(scale)]

    @hasImage
    @refresh
    def zoomFit(self, *args):
        """
        Fit image to window
        """
        self._mpl_toolbar.home()

    @hasImage
    @refresh
    def zoom(self, *args):
        """
        Zoom in on selected region
        """
        self._mpl_toolbar.zoom()

    @hasImage
    @refresh
    def pan(self, *args):
        """
        Pan around image
        """
        self._mpl_toolbar.pan()

    @hasImage
    def saveToFile(self, fn, export=False):
        if export:
            self._gc.save(fn)
        else:
            hdu = fits.PrimaryHDU(self._gc._data, header=self._gc._header)
            hdu.writeto(fn, clobber=True)

    @hasImage
    def mouseMoveEvent(self, event):
        FigureCanvasQTAgg.mouseMoveEvent(self, event)
        pixel_x = event.x()
        pixel_y = event.y()
        ra, dec = self._gc.pixel2world(pixel_x, pixel_y)
        inverted = self._fig.gca().transData.inverted()
        x, y = inverted.transform((pixel_x, pixel_y))
        try:
            if x < 0 or y < 0:
                value = None
            else:
                value = self._gc._data[480 - y][x]
        except IndexError:
            value = None
        self.hoverSignal.emit(x, y, value, ra, dec)


class FileItem(QtGui.QStandardItem):
    def __init__(self, fn):
        dn = os.path.basename(str(fn))[:-5]
        super(FileItem, self).__init__(dn)
        self.fn = fn


class MainWindow(QtGui.QApplication):
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
        self.ui = uic.loadUi(getUiFile('viewer.ui'))
        self.fits = FitsView()
        self.fits.hoverSignal.connect(self.updateStatus)
        self.ui.fitsLayout.addWidget(self.fits)

        self.ui.setWindowIcon(QtGui.QIcon(getUiFile('icon.svg')))

        if USE_CAMERA:
            ports = list_serial_ports()
            if len(ports) == 0:
                USE_CAMERA = False
            else:
                self.ui.portChoice.addItems(ports)
                self.ui.takeImage.clicked.connect(self.takeImage)

        if not USE_CAMERA:
            self.ui.allSkyControls.hide()

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

        self.fits._mpl_toolbar._actions['pan'].toggled.connect(self.panUpdate)
        self.fits._mpl_toolbar._actions['zoom'].toggled.connect(self.zoomUpdate)

        self.status = QtGui.QLabel()
        self.status.setText('No Image Loaded')
        self.ui.statusBar().addWidget(self.status)

        self.model = QtGui.QStandardItemModel()
        self.ui.fileList.setModel(self.model)
        self.ui.fileList.selectionModel().selectionChanged.connect(self.setSelection)
        self.ui.show()

    def updateStatus(self, x, y, value, ra_d, dec_d):
        coord = coordinates.ICRSCoordinates(ra=ra_d, dec=dec_d, unit=(units.degree, units.degree))
        ra_str = coord.ra.format(units.hour)
        dec_str = coord.dec.format(units.degree, alwayssign=True)
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
        QtGui.QMessageBox.about(self.ui, 'About Fits Image Viewer', ABOUT_TEXT)

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

    def quit(self):
        sys.exit()


def main():
    app = MainWindow(sys.argv)
    args = app.arguments()
    if len(args) > 1:
        app.addFiles(files=args[1:])
    app.exec_()

if __name__ == '__main__':
    main()
