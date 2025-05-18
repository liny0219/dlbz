# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all
import glob
import os
import paddle  # <--- 新增，自动定位 paddle 路径
block_cipher = None

datas = []
binaries = []
hiddenimports = []

# 需要自动收集的依赖库
packages = [
    'uiautomator2',
    'paddleocr',
    'Cython',
]

for package in packages:
    pkg_data, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_data
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# 添加手动指定的数据目录（如有）
datas += [('config/settings.yaml', 'config/settings.yaml')]

# 自动收集 paddle/libs 下所有 DLL 文件到 dist 根目录
try:
    paddle_libs_dir = os.path.join(os.path.dirname(paddle.__file__), 'libs')
    if os.path.exists(paddle_libs_dir):
        for dll in glob.glob(os.path.join(paddle_libs_dir, '*.dll')):
            datas.append((dll, '.'))  # 目标路径为 dist 根目录
except Exception as e:
    print(f"Warning: Could not collect paddle DLLs: {e}")

main_script = 'src/main.py'

a = Analysis([main_script],
             pathex=['.'],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Traveler's Inn',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          # icon='assets/icon_exe.ico', # 如有图标可取消注释
          console=False,
          runtime_tmpdir=None)
