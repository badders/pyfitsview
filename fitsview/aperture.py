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
from matplotlib.patches import Circle
from PyQt4 import QtCore
import numpy as np
from photometry import Aperture


class ApertureWrapper(QtCore.QObject, Aperture):
    def __init__(self, x, y, r=10, br=20, name='Aperture'):
        QtCore.QObject.__init__(self)
        Aperture.__init__(self, x, y, r, br, name)
        self.inner = Circle((x, y), r, linewidth=1.0, edgecolor='yellow', facecolor='none')
        self.outer = Circle((x, y), br, linewidth=0.5, ls='dotted', edgecolor='yellow', facecolor='none')

    def refresh(self):
        self.outer.center = self.inner.center = (self.x, self.y)
        self.inner.set_radius(self.r)
        self.outer.set_radius(self.br)

    def addToAxes(self, axes):
        axes.add_patch(self.inner)
        self.inner.set_transform(axes.transData)
        axes.add_patch(self.outer)
        self.outer.set_transform(axes.transData)

    def contains(self, event):
        rdiff = np.sqrt(((np.array(self.outer.center) - np.array([event.xdata, event.ydata])) ** 2).sum())
        return rdiff < self.br
