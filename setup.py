from setuptools import setup

APP = ['fitsview.py']
DATA_FILES = ['ui']

OPTIONS = {
    'argv_emulation': True,
    'packages': ['astropy', 'matplotlib', 'scipy', 'numpy'],
    'includes': ['PyQt4', 'PyQt4.QtCore', 'PyQt4.QtGui', 'sip'],
    'excludes': ['PyQt4.QtDesigner', 'PyQt4.QtNetwork', 'PyQt4.QtNetwork', 'PyQt4.QtOpenGL'
                 'PyQt4.QtScript', 'PyQt4.QtSql', 'PyQt4.QtWebKit', 'PyQt4.QtXml',
                 'PyQt4.phonon', 'Tkinter', 'PyQt4.uic.port_v3'],
    'iconfile': 'ui/icon.icns',
    'plist': dict(
        NSHumanReadableCopyright='(c) Tom Badran 2013',
        CFBundleName='Fits Viewer',
        CFBundlePackageType='APPL',
        CFBundleExecutable='Fits Viewer',
        CFBundleDisplayName='Fits Viewer',
        CFBundleShortVersionString='0.1.0',
        CFBundleDocumentTypes=[
                dict(
                    CFBundleTypeName='Flexible Image Transport System',
                    CFBundleTypeExtensions=['fits', 'fit', 'fts'],
                ),
        ]
    )
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
