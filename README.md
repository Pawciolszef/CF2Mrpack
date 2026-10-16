# CF2Mrpack

A simple GUI tool to convert local CurseForge Minecraft instances into Modrinth (`.mrpack`) packages.

## How it works

1. **Environment detection:** Reads Minecraft version and modloader (`Forge`, `Fabric`, `NeoForge`, `Quilt`) directly from instance files (`manifest.json` or `minecraftinstance.json`).
2. **Modrinth API matching:** Calculates SHA-1 and SHA-512 hashes for all `.jar` files and checks them against the Modrinth API. Matched mods are linked via Modrinth CDN to keep the archive lightweight.
3. **Fallback handling:** Any CurseForge-exclusive, disabled, or custom mods are bundled directly into `overrides/mods/`, ensuring nothing goes missing.
4. **Config & assets migration:** Copies `config/`, `defaultconfigs/`, `kubejs/`, `scripts/`, and optionally resource packs, shaders, and saves.

---

## Download

Download the latest standalone executable (`CF2Mrpack.exe`) from **[Releases](https://github.com/Pawciolszef/CF2Mrpack/releases)**. No Python installation required.

---

## Running from Source

Requires Python 3.9+:

```bash
git clone https://github.com/Pawciolszef/CF2Mrpack.git
cd CF2Mrpack
pip install -r requirements.txt
python main.py
```

---

## How to Use

1. Select your CurseForge instance directory (e.g. `C:\curseforge\minecraft\Instances\<modpack>`).
2. Verify or adjust the modpack name and version.
3. Choose whether to include shaderpacks, resourcepacks, or world saves.
4. Click **Build .mrpack Archive**.
5. Import the generated `.mrpack` into Modrinth App, Prism Launcher, or another compatible launcher.

---

## Building Executable

To build the Windows `.exe` locally:

```bash
python -m PyInstaller --noconfirm --onefile --windowed --collect-all customtkinter --name "CF2Mrpack" --clean main.py
```

The output binary will be created in `dist/CF2Mrpack.exe`.

---

## License

[MIT](LICENSE)
