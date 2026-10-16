# CF2Mrpack — CurseForge Instance to Modrinth (`.mrpack`) Converter

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

**CF2Mrpack** is a desktop utility built with Python and **CustomTkinter** that converts local **CurseForge** Minecraft instances directly into standalone **Modrinth (`.mrpack`)** modpack archives.

---

## ✨ Features

- **Automatic Environment Detection:** Reads `manifest.json` and `minecraftinstance.json` to automatically detect the Minecraft version and Modloader (`Forge`, `Fabric`, `NeoForge`, `Quilt`) along with its exact version.
- **Smart Modrinth API Resolution:** Hashes all `.jar` files (`SHA-1` & `SHA-512`) and queries Modrinth's `/v2/version_files` endpoint in a single batch request:
  - Mods available on Modrinth are linked via lightweight CDN URLs inside `modrinth.index.json`.
  - CurseForge-exclusive or disabled mods automatically fall back to `overrides/mods/`, ensuring **zero missing mods**.
- **Complete Configuration Migration:** Bundles `config/`, `defaultconfigs/`, `configureddefaults/`, `kubejs/`, `scripts/`, `patchouli_books/`, and optionally `resourcepacks/`, `shaderpacks/`, `datapacks/`, `saves/`, and `options.txt`.
- **Responsive Dark UI:** Built with CustomTkinter with high-DPI scaling support.

---

## 🚀 Installation & Usage

### 📥 Download Pre-built Executable
You can download the ready-to-run Windows executable (`CF2Mrpack.exe`) directly from **[GitHub Releases](https://github.com/Pawciolszef/CF2Mrpack/releases)**. No Python installation needed!

### 🐍 Running from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Pawciolszef/CF2Mrpack.git
   cd CF2Mrpack
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the application:**
   ```bash
   python main.py
   ```

---

## 📦 Building a Standalone `.exe` (PyInstaller)

You can compile **CF2Mrpack** into a single standalone `.exe` file that runs on any Windows PC without Python installed.

### Option A: One-Click Batch Script (Windows)
Double-click `build_exe.bat` or run it from the terminal:
```cmd
build_exe.bat
```

### Option B: Manual PyInstaller Command
```bash
pyinstaller --noconfirm --onefile --windowed --collect-all customtkinter --name "CF2Mrpack" main.py
```
The compiled executable will appear in `dist/CF2Mrpack.exe`.

---

## 📥 Importing into Modrinth App

1. Open **CF2Mrpack**, select your CurseForge instance folder (e.g. `C:/curseforge/minecraft/Instances/YourModpack`), and click **Build .mrpack Archive**.
2. Open the **Modrinth App**.
3. Click the **+** (**Create new profile**) button on the left sidebar.
4. Select **Import from file** and choose your generated `.mrpack` file.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.
