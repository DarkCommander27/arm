# Windows Build Process

This document outlines the process for building the Android TV Remote Control app for Windows.

## Prerequisites

- Windows 10 or 11
- Python 3.9+ (tested with 3.11)
- Git

## Build Steps

1. **Clone the repository**

   ```powershell
   git clone https://github.com/DarkCommander27/arm.git
   cd arm
   ```

2. **Set up a virtual environment**

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**

   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Build the app**

   Option 1: Using the build script
   ```powershell
   .\scripts\build.ps1
   ```

   Option 2: Manually with PyInstaller
   ```powershell
   pyinstaller app.spec
   ```

5. **Find the built application**

   After building, the application will be located in `dist\AndroidTVRemote\`.

   You can run the app by double-clicking `AndroidTVRemote.exe` in that folder.

## Automated Build with GitHub Actions

We've set up a GitHub Actions workflow to automatically build the app for Windows. To use it:

1. Push your changes to the `main` branch.
2. GitHub Actions will automatically build the app.
3. Download the artifact from the Actions tab in the GitHub repository.

## Testing the Build

1. Run the built application:
   ```
   .\dist\AndroidTVRemote\AndroidTVRemote.exe
   ```

2. If you want to test the CLI version:
   ```
   python cli_test.py
   ```

## Troubleshooting

- If you encounter "DLL not found" errors, make sure you have the Visual C++ Redistributable installed.
- If you have issues with PyQt5, try reinstalling it with `pip install --force-reinstall PyQt5`.
- For network discovery issues, make sure your firewall allows the app to access the network.

## Distribution

To distribute the app:
1. Copy the entire `dist\AndroidTVRemote\` folder.
2. Create a ZIP file of the folder or use an installer generator like NSIS or InnoSetup.