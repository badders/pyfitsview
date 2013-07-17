from setuptools import setup

APP = ['fitsview.py']
DATA_FILES = []

FITS_UTI = {
    'UTTypeIdentifier': 'public.fits',
    'UTTypeReferenceURL': 'http://fits.gsfc.nasa.gov/',
    'UTTypeDescription': 'FITS Image',
    'UTTypeConformsTo': ['public.image', 'public.data'],
    'UTTypeTagSpecification': {
        'com.apple.ostype': 'FITS',
        'public.filename-extension': 'fits',
        'public.mime-type': 'image/fits'
    }
}

PLIST = {
    'NSHumanReadableCopyright': '(c) Tom Badran 2013',
    'CFBundleName': 'Fits Viewer',
    'CFBundlePackageType': 'APPL',
    'CFBundleExecutable': 'Fits Viewer',
    'CFBundleDisplayName': 'Fits Viewer',
    'UTExportedTypeDeclarations': [FITS_UTI],
    'CFBundleShortVersionString': '0.1.0',
    'CFBundleDocumentTypes': {
        'CFBundleTypeName': 'FITS Image',
        'CFBundleTypeRole': 'Viewer',
        'LSItemContentTypes': ['public.FITS']
    }
}

OPTIONS = {
    'argv_emulation': True,
    'includes': ['sip', 'PyQt4._qt'],
    'excludes': ['PyQt4.QtDesigner'],
    'iconfile': 'ui/icon.icns',
    'plist': PLIST
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
