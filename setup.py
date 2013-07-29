from setuptools import setup

setup(
    name='Fits Viewer',
    version='0.2.0a',
    description='Explore sets of astronomical FITS images',
    long_description=(open('README.md').read()),
    url='http://github.com/badders/pyfitsview/',
    license='GPL',
    author='Tom Badran',
    author_email='tom@badrunner.net',
    py_modules=['fitsview'],
    include_package_data=True,
    package_data=['README.md', 'COPYING', 'ui/*'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Astronomy',
    ],
)
