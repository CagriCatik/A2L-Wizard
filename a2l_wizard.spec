# a2l_wizard.spec
# Build with: pyinstaller --clean a2l_wizard.spec

from PyInstaller.utils.win32.versioninfo import VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct, VarFileInfo, VarStruct
from PyInstaller.utils.win32.winmanifest import RT_MANIFEST
from PyInstaller.building.api import PYZ, EXE, COLLECT
import os

app_name = "A2L-Wizard"
icon_path = os.path.join("static", "wizard.ico")  # convert your PNG to ICO
entry_script = "main.py"

version = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1,0,0,0),
        prodvers=(1,0,0,0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo([StringTable("040904B0", [
            StringStruct("CompanyName", "Your Name or Org"),
            StringStruct("FileDescription", "A2L Wizard"),
            StringStruct("FileVersion", "1.0.0"),
            StringStruct("InternalName", app_name),
            StringStruct("OriginalFilename", f"{app_name}.exe"),
            StringStruct("ProductName", "A2L Wizard"),
            StringStruct("ProductVersion", "1.0.0"),
            StringStruct("LegalCopyright", "Copyright (c) 2025"),
        ])]),
        VarFileInfo([VarStruct("Translation", [0x0409, 0x04B0])])
    ]
)

manifest = r"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly manifestVersion="1.0" xmlns="urn:schemas-microsoft-com:asm.v1">
  <assemblyIdentity version="1.0.0.0" processorArchitecture="*" name="A2LWizard" type="win32"/>
  <description>A2L Wizard</description>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <dpiAware>true/pm</dpiAware>
    </windowsSettings>
  </application>
</assembly>
"""

a = Analysis([entry_script], pathex=[], binaries=[], datas=[
    ("static/wizard.png", "static"),  # if you load it at runtime
], hiddenimports=[], hookspath=[], excludes=[
    # exclude things you do not use
    "tkinter","pytest","numpy.f2py"
], noarchive=False)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=app_name,
    console=False,           # GUI app
    icon=icon_path,
    version=version,
    disable_windowed_traceback=True,
    uac_admin=False,         # never request admin
)

coll = COLLECT(exe, strip=False, upx=False)  # UPX disabled
# Embed manifest explicitly
coll.toc.append((RT_MANIFEST, 1, manifest))
