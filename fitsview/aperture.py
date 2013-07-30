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
from matplotlib.patches import Circle
from PyQt4 import QtCore
import numpy as np


class Aperture(QtCore.QObject):
    def __init__(self, x, y, r=10, br=20, name='Aperture'):
        self.x = x
        self.y = y
        self.r = r
        self.br = br
        self.name = name
        self.inner = Circle((x, y), r, edgecolor='yellow', facecolor='none')
        self.outer = Circle((x, y), br, linestyle='dotted', edgecolor='yellow', facecolor='none')

    def refresh(self):
        self.outer.center = self.inner.center = (self.x, self.y)
        self.inner.r = self.r
        self.outer.br = self.br

    def addToAxes(self, axes):
        axes.add_patch(self.inner)
        self.inner.set_transform(axes.transData)
        axes.add_patch(self.outer)
        self.outer.set_transform(axes.transData)

    def contains(self, event):
        rdiff = np.sqrt(((np.array(self.outer.center) - np.array([event.xdata, event.ydata])) ** 2).sum())
        return rdiff < self.br

    @classmethod
    def fromDict(cls, d):
        return cls(d['x'], d['y'], d['r'], d['br'], d['name'])

    def toDict(self):
        return {'x': self.x,
                'y': self.y,
                'r': self.r,
                'br': self.br,
                'name': self.name}
