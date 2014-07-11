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
import matplotlib
matplotlib.rcParams['backend.qt4'] = 'PySide'
matplotlib.use('Qt4Agg')

from fitsview import FitsViewer
import sys
import os


def safe_remove(args, arg):
    try:
        args.remove(arg)
    except IndexError:
        pass


def main():
    app = FitsViewer(sys.argv)
    args = app.arguments()

    # Strip first argument if running on windows
    args = list(args)
    if os.name == 'nt':
        safe_remove(args, '-u')
        safe_remove(args, 'fitsview.py')

    if len(args) > 1:
        app.addFiles(files=args[1:])
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
