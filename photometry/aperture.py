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


class Aperture:
    def __init__(self, x, y, r=10, br=20, name='Aperture'):
        self.x = x
        self.y = y
        self.r = r
        self.br = br
        self.name = name

    @classmethod
    def fromDict(cls, d):
        return cls(d['x'], d['y'], d['r'], d['br'], d['name'])

    def toDict(self):
        return {'x': self.x,
                'y': self.y,
                'r': self.r,
                'br': self.br,
                'name': self.name}
