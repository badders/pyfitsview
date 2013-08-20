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
from __future__ import division
import numpy as np


def masks(aperture):
    """
    Generates the masks used for the regions of interest
    returns (background mask, aperture mask)
    """
    r = aperture.r
    br = aperture.br
    offset = (aperture.x % 1, aperture.y % 1)
    size = 2 * br + 2
    m = np.zeros((size, size))
    bm = np.zeros_like(m)
    cx = size / 2 + offset_x
    cy = size / 2 + offset_y
    for x in range(size):
        for y in range(size):
            dr = np.sqrt((cx - x) ** 2 + (cy - y) ** 2)
            dbr = np.sqrt((cx - x) ** 2 + (cy - y) ** 2)
            if dr <= r:
                m[x][y] = 1
            elif dr < r + 1:
                m[x][y] = abs(r - dr)
            if dr <= br:
                bm[x][y] = 1
            elif dr < br + 1:
                bm[x][y] = abs(br - dr)

    bm = bm - m
    return (bm, m)


def do_photometry(files, apertures):
    return []
