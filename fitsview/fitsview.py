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
from collections import OrderedDict
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QTAgg
from matplotlib.figure import Figure
import astropy.io.fits as fits
import aplpy
import dateutil
from PyQt5 import QtGui, QtWidgets, QtCore
from functools import wraps
from .common import *


class FitsView(FigureCanvasQTAgg):
    """
    A FITS image viewer base on matplotlib, rendering is done using the aplpy
    library.
    """
    hoverSignal = QtCore.Signal(int, int, int, float, float)
    selectSignal = QtCore.Signal(object)

    def refresh(f):
        @wraps(f)
        def _refresh(*args, **kwargs):
            ret = f(*args, **kwargs)
            args[0]._refresh_timer.start(150)
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
        self._fig = Figure(dpi=170)
        FigureCanvasQTAgg.__init__(self, self._fig)
        FigureCanvasQTAgg.setSizePolicy(self,
                                        QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)
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
        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._refreshConcrete)
        self.apertures = []

    def _refreshConcrete(self):
        if self._gc:
            self._gc.show_colorscale(pmin=self._lowerCut, pmax=self._upperCut,
                                     stretch=self._scale, aspect='auto',
                                     cmap=self._cmap)
            self._gc.axis_labels.hide()
            self._gc.tick_labels.hide()
            self._gc.ticks.hide()
            self._gc.frame.set_linewidth(0)

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
        if use_camera():
            from pyallsky import AllSkyCamera
            self._fig.clear()
            self._taking = True
            cam = AllSkyCamera(dev)
            image = cam.get_image(exposure=exposure, progress_callback=progress)
            self._max = image.data.max()
            self._gc = aplpy.FITSFigure(image, figure=self._fig)
            self._taking = False

    def getImageDateObserved(self):
        return dateutil.parser.parse(self._gc._header['DATE-OBS'])

    def getImageExposure(self):
        return self._gc._header['EXPOSURE']

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
                value = self._gc._data[self._gc._data.shape[0] - y][x]
        except IndexError:
            value = None
        self.hoverSignal.emit(x, y, value, ra, dec)
