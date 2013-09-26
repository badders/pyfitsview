from setuptools import setup

APP = ['fitsview.py']
DATA_FILES = ['ui']

OPTIONS = {
    'argv_emulation': True,
    'packages': ['astropy', 'matplotlib'],
    'includes': ['PyQt4', 'PyQt4.QtCore', 'PyQt4.QtGui', 'sip',],
    'excludes': ['PySide', 'PyQt4.QtDesigner', 'PyQt4.QtNetwork',
                 'PyQt4.QtOpenGL', 'PyQt4.QtScript', 'PyQt4.QtSql',
                 'PyQt4.QtWebKit', 'PyQt4.QtXml', 'PyQt4.phonon',
                 'Tkinter', 'PyQt4.uic.port_v3', 'matplotlib.tests',
                 'IPython', 'zmq'],
    'iconfile': 'ui/icon.icns',
    'resources': ['ui/image-fits.icns'],
    'plist': dict(
        CFBundleDocumentTypes=[
                dict(
                    CFBundleTypeName='Flexible Image Transport System document',
                    CFBundleTypeIconFile='ui/image-fits.icns',
                    CFBundleTypeExtensions=['fits', 'fit', 'fts'],
                    CFBundleTypeOSTypes=['FITS'],
                    CFBundleTypeRole='Viewer'),
        ],
        CFBundleName='Fits Viewer',
        CFBundleDisplayName='Fits Viewer',
    )
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
