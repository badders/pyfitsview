# coding: utf-8
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
import aplpy
from collections import OrderedDict
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt4 import QtGui, QtCore, uic

try:
    from serial.tools import list_ports
    from allsky import AllSkyCamera
    USE_CAMERA = True
except ImportError:
    USE_CAMERA = False

def getUiFile(name):
  return os.path.join(os.path.dirname(os.path.realpath( __file__ )), 'ui', name)

def list_serial_ports():
    ports = []
    for x in list_ports.comports():
        port = x[0]
        if port.count('Bluetooth') == 0:
            ports.append(port)
    return ports

def get_colour_maps():
    maps = matplotlib.cm.datad.keys()
    maps.sort(key=str.lower)
    return maps

class FitsView(FigureCanvasQTAgg):
    """
    A FITS imageviewer base on matplotlib, rendering is done using the astropy
    library.
    """
    hoverSignal = QtCore.pyqtSignal(int, int, int)

    def __init__(self):
        self._fig = Figure(dpi=96)
        FigureCanvasQTAgg.__init__(self, self._fig)
        FigureCanvasQTAgg.setSizePolicy(self,
                                        QtGui.QSizePolicy.Expanding,
                                        QtGui.QSizePolicy.Expanding)
        self._fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.__taking = False
        self._scale = 'log'
        self.scales = OrderedDict()
        self.scales['Logarithmic'] = 'log'
        self.scales['Linear'] =  'linear'
        self.scales['Square Root'] = 'sqrt'
        self.scales['Power'] = 'power'
        self.scales['Arc Sinh'] = 'arcsinh'
        self.gc = None
        self.upperCut = 99.75
        self.lowerCut = 0.25
        self.cmap = 'gray'

    def loadImage(self, filename):
        """
        Load a fits image from disk
        filename -- full path to the image file
        """
        self.gc = aplpy.FITSFigure(filename, figure=self._fig)
        self._updateDisplay()

    def takeImage(self, exposure, progress, dev='/dev/tty.usberial'):
        """
        Take an image using the All Sky camera
        exposure -- Desired exposure time
        progress -- Function for progress update callback
        dev -- Path to serial device
        """
        if self.__taking:
            return
        self._taking = True
        cam = AllSkyCamera(dev)
        image = cam.get_image(exposure=exposure, progress_callback=progress)
        self._max = image.data.max()
        self.gc = aplpy.FITSFigure(image, figure=self._fig)
        self._updateDisplay()
        self._taking = False

    def _updateDisplay(self):
        if self.gc is not None:
            self.gc.show_colorscale(pmin=self.lowerCut, pmax=self.upperCut,
                                    stretch=self._scale, aspect='auto',
                                    cmap=self.cmap)
            self.gc.axis_labels.hide()
            self.gc.tick_labels.hide()
            self.gc.ticks.hide()
            self.gc.frame.set_linewidth(0)

    def setCMAP(self, cmap):
        """
        Set the colourmap for the image display
        cmap -- colourmap name (see matplotlib.cm)
        """
        self.cmap = cmap
        self._updateDisplay()

    def setUpperCut(self, value):
        """
        Set the upper limit for display cut
        value -- percentage for upper limit
        """
        self.upperCut = value
        self._updateDisplay()

    def setLowerCut(self, value):
        """
        Set the lower limit for display cut
        value -- percentage for the lower limit
        """
        self.lowerCut = value
        self._updateDisplay()

    def getScales(self):
        """
        return the available normalisation scales
        """
        return self.scales

    def setScale(self, scale):
        """
        Set normalisation scale
        scale -- desired scale
        """
        self._scale = self.scales[str(scale)]
        self._updateDisplay()

    def mouseMoveEvent(self, event):
        FigureCanvasQTAgg.mouseMoveEvent(self, event)
        if self.gc is not None:
            pixel_x = event.x()
            pixel_y = event.y()
            inv = self._fig.gca().transData.inverted()
            x, y = inv.transform((pixel_x, pixel_y))
            value = self.gc._data[480 - y][x]
            self.hoverSignal.emit(x, y, value)

class MainWindow(QtGui.QMainWindow):
    """
    Application User interface
    """
    def __init__(self):
        global USE_CAMERA
        QtGui.QMainWindow.__init__(self)
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

        self.ui.actionOpen.triggered.connect(self.loadImage)
        self.ui.actionAbout.triggered.connect(self.about)
        self.status = QtGui.QLabel()
        self.status.setText('No Image Loaded')
        self.ui.statusBar().addWidget(self.status)

        self.ui.show()

    def updateStatus(self, x, y, value):
        status = 'X: {:>4}\tY: {:>4}\tValue: {}'.format(x, y, value)
        self.status.setText(status)

    def cmapChange(self, index):
        self.fits.setCMAP(get_colour_maps()[index])

    def scaleChange(self, index):
        self.fits.setScale(self.ui.normalisation.itemText(index))

    def loadImage(self):
        filen = QtGui.QFileDialog.getOpenFileName(caption='Load Fits File', filter='*.fits')
        if filen != '':
            self.fits.loadImage(str(filen))
            self.status.setText('')

    def about(self):
        QtGui.QMessageBox.about(self.ui, 'About Fits Image Viewer', 
            'Fits Image Viewer\nCopyright Tom Badran 2013\nhttp://github.com/badders/pyfitsview\n\nLicensed under the GPL')

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

def main():
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    app.exec_()

if __name__ == '__main__':
    main()

