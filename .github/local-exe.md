# How to Build Local .exe

Run these commands in PowerShell from your project root:

```powershell
# Go to project folder
cd A2L-Wizard

# Create virtual environment named .venv
py -3.13 -m venv .venv

# Activate the venv
.\.venv\Scripts\activate

# Upgrade pip, setuptools, wheel
python -m pip install --upgrade pip setuptools wheel

# Install project dependencies
pip install -r requirements.txt

# Install PyInstaller in the venv
pip install pyinstaller
```

After this, you can build inside the venv:

```powershell
pyinstaller --clean a2l_wizard.spec
```
