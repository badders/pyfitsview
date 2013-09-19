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
try:
    from serial.tools import list_ports
    from allsky import AllSkyCamera
    _USE_CAMERA = True
except ImportError:
    _USE_CAMERA = False

import os
import matplotlib
from PyQt4 import QtGui
import __main__


def get_ui_file(name):
    """
    Helper function to automatically correct path for files in ui/
    """
    return os.path.join(os.path.dirname(os.path.realpath(__main__.__file__)), 'ui', name)


def get_config_file():
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
    maps = list(matplotlib.cm.datad.keys())
    maps.sort(key=str.lower)
    return maps


def use_camera():
    """
    Returns true if the libraries required to use the AllSky camera are available
    """
    return _USE_CAMERA

def ra_to_str(ra):
    """
    Convert right ascension to a pretty printed string
    ra -- Right ascension from astropy.coordinates
    Returns string like ±18d26m32s
    """
    ra = int(abs(ra * 3600))
    h, m, s = ra // 3600, (ra // 60) % 60, ra % 60
    if ra < 0:
        sign = '-'
    else:
        sign = '+'
    return '{}{:02d}h{:02d}m{:02d}s'.format(sign, h, m, s)


def dec_to_str(dec):
    """
    Convert right ascension to a pretty printed string
    dec -- Declination from astropy.coordinates
    Returns string like ±18d26m32s
    """
    dec = int(abs(dec * 3600))
    d, m, s = dec // 3600, (dec // 60) % 60, dec % 60
    if dec < 0:
        sign = '-'
    else:
        sign = '+'
    return '{}{:02d}d{:02d}m{:02d}s'.format(sign, d, m, s)

class FileItem(QtGui.QStandardItem):
    def __init__(self, fn):
        dn = os.path.basename(str(fn))[:-5]
        super(FileItem, self).__init__(dn)
        self.fn = fn
