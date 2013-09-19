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
import numpy as np
import math
from matplotlib import pyplot as plt
from astropy.io import fits


def masks(aperture):
    """
    Generates the masks used for the regions of interest
    returns (background mask, aperture mask)
    """
    r = aperture.r
    br = aperture.br
    size = int(math.ceil(2 * br + 2))
    m = np.zeros((size, size))
    bm = np.zeros_like(m)
    cx = br
    cy = br
    for x in range(size):
        for y in range(size):
            rx = x - cx
            ry = y - cy
            dr = np.sqrt(rx ** 2 + ry ** 2)
            if dr <= r:
                m[x][y] = 1
            elif dr < r + 1:
                m[x][y] = 1 - (dr % 1)
            if dr <= br:
                bm[x][y] = 1
            elif dr < br + 1:
                bm[x][y] = 1 - (dr % 1)

    bm = bm - m
    return (bm, m)


def __debug_apertures(ap, bg, data):
    import matplotlib.cm as cm
    plt.figure(figsize=(14, 5))
    plt.subplot(131)
    plt.imshow(ap, cmap=cm.gist_gray)
    plt.subplot(132)
    plt.imshow(bg, cmap=cm.gist_gray)
    plt.subplot(133)

    lower, upper = np.percentile(data.flatten(), [0.75, 99.25])
    for x in range(bg.shape[0]):
        for y in range(bg.shape[1]):
            if data[x, y] < lower:
                data[x, y] = lower
            elif data[x, y] > upper:
                data[x, y] = upper
    plt.imshow(data, cmap=cm.gist_gray)


def do_photometry(file_names, apertures):
    """
    Generate photon counts for the images under the apertures provided
    file_names -- List of files to perform operation open
    apertures -- List of the apertures to use
    returns a 2d list of the photometry data as columns:
    ap-bg 1, error 1, ap-bg 2, error 2, etc.
    """
    ms = [(ap, masks(ap)) for ap in apertures]
    output = []
    for name in file_names:
        row = []
        hdulist = fits.open(name)
        for ap, (bg_m, ap_m) in ms:
            w, h = ap_m.shape
            x1 = (ap.x - math.ceil(ap.br))
            y1 = (ap.y - math.ceil(ap.br))

            data = hdulist[0].data[y1:y1 + h, x1:x1 + w]

            data = data.flatten()
            bg_m = bg_m.flatten()
            ap_m = ap_m.flatten()

            bg = (data * bg_m).sum() / bg_m.sum()
            ap = (data * ap_m).sum() - bg * ap_m.sum()

            row.append(ap)
            row.append(np.sqrt(ap))

        output.append(row)

    return np.array(output)

if __name__ == '__main__':
    from aperture import Aperture
    import glob
    fs = glob.glob('/Users/tom/fits/transition/*.fits')
    ap = Aperture(614.96, 806.929, 10.0, 20.0)
    data = do_photometry(fs, [ap])

    print(data.shape)
    plt.figure()
    y = data[:,0]
    y_err = data[:,1]
    x = range(len(y))
    plt.errorbar(x, y, yerr=y_err)
    plt.show()
