# -*- mode: python -*-
a = Analysis(['fitsview.py'],
             pathex=['/Users/tom/Developer/pyfitsview'],
             hiddenimports=[],
             hookspath=None,
             runtime_hooks=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='fitsview',
          debug=False,
          strip=None,
          upx=True,
          console=False , icon='ui/icon.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='fitsview')
app = BUNDLE(coll,
             name='fitsview.app',
             icon='ui/icon.icns')
