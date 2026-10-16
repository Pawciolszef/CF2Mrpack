import os
import sys
import json
import zipfile
import hashlib
import threading
import subprocess
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
import requests

APP_NAME = "CF2Mrpack"
APP_VERSION = "1.0.0"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")


def get_default_cf_instances_dir() -> str:
    """Detect standard CurseForge instances directory across OSes."""
    home = Path.home()
    candidates = [
        Path("C:/curseforge/minecraft/Instances"),
        home / "curseforge" / "minecraft" / "Instances",
        home / "Documents" / "Curse" / "Minecraft" / "Instances",
    ]
    for path in candidates:
        if path.exists() and path.is_dir():
            return str(path).replace("\\", "/")
    return ""


class CFToMrpackApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} v{APP_VERSION} — CurseForge to Modrinth (.mrpack) Converter")
        self.geometry("760x720")
        self.minsize(680, 650)
        self.resizable(True, True)

        # State Variables
        self.instance_path = ctk.StringVar(value="")
        self.output_path = ctk.StringVar(value="")
        self.pack_name = ctk.StringVar(value="")
        self.pack_version = ctk.StringVar(value="1.0.0")

        self.use_modrinth_api = ctk.BooleanVar(value=True)
        self.include_shaders_rp = ctk.BooleanVar(value=True)
        self.include_saves = ctk.BooleanVar(value=False)
        self.include_options = ctk.BooleanVar(value=False)

        self._cancel_requested = False

        self._build_ui()

    def _build_ui(self):
        # --- Header ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(16, 8))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="CurseForge to Modrinth (.mrpack) Converter",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.pack(side="left")

        ver_lbl = ctk.CTkLabel(
            header_frame,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        ver_lbl.pack(side="right", pady=(6, 0))

        # --- Paths Section ---
        paths_frame = ctk.CTkFrame(self)
        paths_frame.pack(fill="x", padx=24, pady=6)

        ctk.CTkLabel(
            paths_frame, text="CurseForge Instance Directory:", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=14, pady=(10, 2))

        in_row = ctk.CTkFrame(paths_frame, fg_color="transparent")
        in_row.pack(fill="x", padx=14, pady=(0, 8))

        self.entry_in = ctk.CTkEntry(
            in_row, textvariable=self.instance_path, placeholder_text="Select a CurseForge instance folder..."
        )
        self.entry_in.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(in_row, text="Browse...", width=100, command=self.browse_instance).pack(side="right")

        ctk.CTkLabel(
            paths_frame, text="Output .mrpack File:", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=14, pady=(4, 2))

        out_row = ctk.CTkFrame(paths_frame, fg_color="transparent")
        out_row.pack(fill="x", padx=14, pady=(0, 12))

        self.entry_out = ctk.CTkEntry(
            out_row, textvariable=self.output_path, placeholder_text="Output path for the .mrpack archive..."
        )
        self.entry_out.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(out_row, text="Save As...", width=100, command=self.browse_output).pack(side="right")

        # --- Metadata Override Section ---
        meta_frame = ctk.CTkFrame(self)
        meta_frame.pack(fill="x", padx=24, pady=6)

        meta_grid = ctk.CTkFrame(meta_frame, fg_color="transparent")
        meta_grid.pack(fill="x", padx=14, pady=10)
        meta_grid.columnconfigure(0, weight=3)
        meta_grid.columnconfigure(1, weight=1)

        ctk.CTkLabel(meta_grid, text="Modpack Name:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 4)
        )
        ctk.CTkLabel(meta_grid, text="Modpack Version:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=1, sticky="w", pady=(0, 4)
        )

        ctk.CTkEntry(meta_grid, textvariable=self.pack_name, placeholder_text="Auto-detected from instance").grid(
            row=1, column=0, sticky="ew", padx=(0, 12)
        )
        ctk.CTkEntry(meta_grid, textvariable=self.pack_version, placeholder_text="1.0.0").grid(
            row=1, column=1, sticky="ew"
        )

        # --- Export Options Section ---
        opts_frame = ctk.CTkFrame(self)
        opts_frame.pack(fill="x", padx=24, pady=6)

        ctk.CTkLabel(
            opts_frame, text="Packaging Options:", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=14, pady=(10, 6))

        ctk.CTkCheckBox(
            opts_frame,
            text="Resolve mods via Modrinth API (lightweight pack; unmatched mods fall back to overrides/)",
            variable=self.use_modrinth_api
        ).pack(anchor="w", padx=14, pady=4)

        ctk.CTkCheckBox(
            opts_frame,
            text="Include resourcepacks, shaderpacks, and datapacks",
            variable=self.include_shaders_rp
        ).pack(anchor="w", padx=14, pady=4)

        ctk.CTkCheckBox(
            opts_frame,
            text="Include world saves (saves/ folder)",
            variable=self.include_saves
        ).pack(anchor="w", padx=14, pady=4)

        ctk.CTkCheckBox(
            opts_frame,
            text="Include client settings & server list (options.txt, servers.dat)",
            variable=self.include_options
        ).pack(anchor="w", padx=14, pady=(4, 12))

        # --- Bottom Action Bar (Pinned to Bottom) ---
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(side="bottom", fill="x", padx=24, pady=(6, 18))

        self.progress = ctk.CTkProgressBar(bottom_frame)
        self.progress.pack(fill="x", pady=(0, 10))
        self.progress.set(0)

        btn_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_row.pack(fill="x")

        self.btn_convert = ctk.CTkButton(
            btn_row,
            text="Build .mrpack Archive",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=42,
            command=self.start_conversion
        )
        self.btn_convert.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_open_folder = ctk.CTkButton(
            btn_row,
            text="Open Output Folder",
            height=42,
            width=160,
            fg_color="gray30",
            hover_color="gray40",
            command=self.open_output_folder
        )
        self.btn_open_folder.pack(side="right")

        # --- Console Log Box (Fills remaining middle space) ---
        self.log_box = ctk.CTkTextbox(self, height=130, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.pack(fill="both", expand=True, padx=24, pady=6)
        self.log_box.configure(state="disabled")

        self.log(f"[*] {APP_NAME} v{APP_VERSION} initialized. Select a CurseForge instance folder to begin.")

    def log(self, message: str):
        self.after(0, self._append_log, message)

    def _append_log(self, message: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_progress(self, val: float):
        self.after(0, self.progress.set, val)

    def _auto_populate_from_instance(self, folder_path: str):
        folder_name = os.path.basename(os.path.normpath(folder_path))
        desktop = Path.home() / "Desktop"
        out_dir = desktop if desktop.exists() else Path(folder_path)
        self.output_path.set(str(out_dir / f"{folder_name}.mrpack"))

        try:
            name, version, deps = self.parse_instance_metadata(folder_path)
            self.pack_name.set(name)
            self.pack_version.set(version)
            self.log(f"[+] Detected instance: '{name}' | Target: {deps}")
        except Exception as e:
            self.pack_name.set(folder_name)
            self.pack_version.set("1.0.0")
            self.log(f"[!] Metadata warning: {e}")

    def browse_instance(self):
        initial_dir = get_default_cf_instances_dir() or str(Path.home())
        folder = filedialog.askdirectory(
            title="Select CurseForge Instance Folder",
            initialdir=initial_dir
        )
        if folder:
            self.instance_path.set(folder)
            self._auto_populate_from_instance(folder)

    def browse_output(self):
        file = filedialog.asksaveasfilename(
            title="Save .mrpack Archive As",
            defaultextension=".mrpack",
            filetypes=[("Modrinth Modpack", "*.mrpack"), ("All Files", "*.*")]
        )
        if file:
            self.output_path.set(file)

    def open_output_folder(self):
        out = self.output_path.get().strip()
        target_dir = os.path.dirname(out) if out else str(Path.home())
        if not os.path.isdir(target_dir):
            messagebox.showwarning("Directory Not Found", "Output directory does not exist yet.")
            return
        if sys.platform == "win32":
            os.startfile(target_dir)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", target_dir])
        else:
            subprocess.Popen(["xdg-open", target_dir])

    def parse_instance_metadata(self, inst_dir: str):
        """Extracts pack name, version, Minecraft version, and loader from manifest.json or minecraftinstance.json."""
        name = os.path.basename(os.path.normpath(inst_dir))
        version = "1.0.0"
        mc_version = None
        loader_type = None
        loader_version = None

        manifest_file = os.path.join(inst_dir, "manifest.json")
        mc_inst_file = os.path.join(inst_dir, "minecraftinstance.json")

        if os.path.exists(manifest_file):
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("name", name)
            version = str(data.get("version", version))
            mc_data = data.get("minecraft", {})
            mc_version = mc_data.get("version")
            loaders = mc_data.get("modLoaders", [])
            if loaders:
                loader_id = loaders[0].get("id", "")
                if "-" in loader_id:
                    l_name, l_ver = loader_id.split("-", 1)
                    loader_type = self._map_loader_name(l_name)
                    loader_version = l_ver

        if (not mc_version or not loader_type) and os.path.exists(mc_inst_file):
            with open(mc_inst_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            name = data.get("name", name)
            base_loader = data.get("baseModLoader", {})
            mc_version = mc_version or base_loader.get("minecraftVersion") or data.get("gameVersion")

            if base_loader:
                l_name = base_loader.get("name", "")
                if "-" in l_name:
                    parts = l_name.split("-", 1)
                    loader_type = self._map_loader_name(parts[0])
                    loader_version = parts[1]
                else:
                    loader_version = base_loader.get("forgeVersion") or base_loader.get("modLoaderVersion")
                    type_id = base_loader.get("type", 1)
                    type_map = {1: "forge", 4: "fabric-loader", 5: "quilt-loader", 6: "neoforge"}
                    loader_type = type_map.get(type_id, "forge")

        if not mc_version:
            raise ValueError("Could not detect Minecraft version from manifest.json or minecraftinstance.json.")

        dependencies = {"minecraft": mc_version}
        if loader_type and loader_version:
            dependencies[loader_type] = loader_version

        return name, version, dependencies

    @staticmethod
    def _map_loader_name(raw_name: str) -> str:
        raw_name = raw_name.lower()
        if "neoforge" in raw_name:
            return "neoforge"
        if "fabric" in raw_name:
            return "fabric-loader"
        if "quilt" in raw_name:
            return "quilt-loader"
        return "forge"

    @staticmethod
    def get_file_hashes(filepath: str):
        sha1 = hashlib.sha1()
        sha512 = hashlib.sha512()
        with open(filepath, "rb") as f:
            while chunk := f.read(65536):
                sha1.update(chunk)
                sha512.update(chunk)
        return sha1.hexdigest(), sha512.hexdigest()

    def start_conversion(self):
        inst_dir = self.instance_path.get().strip()
        out_file = self.output_path.get().strip()

        if not os.path.isdir(inst_dir):
            messagebox.showerror("Invalid Directory", "Please select a valid CurseForge instance directory.")
            return
        if not out_file:
            messagebox.showerror("Missing Output Path", "Please specify where to save the .mrpack file.")
            return

        self.btn_convert.configure(state="disabled", text="Building...")
        self.progress.set(0)
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

        threading.Thread(target=self.run_conversion, args=(inst_dir, out_file), daemon=True).start()

    def run_conversion(self, inst_dir: str, out_file: str):
        try:
            self.log(f"[*] Analyzing instance at: {inst_dir}")
            detected_name, detected_ver, dependencies = self.parse_instance_metadata(inst_dir)

            final_name = self.pack_name.get().strip() or detected_name
            final_ver = self.pack_version.get().strip() or detected_ver

            self.log(f"[+] Modpack Name: {final_name} (v{final_ver})")
            self.log(f"[+] Target Environment: {dependencies}")

            mods_dir = os.path.join(inst_dir, "mods")
            mod_files = []
            if os.path.isdir(mods_dir):
                for root, _, files in os.walk(mods_dir):
                    for file in files:
                        if file.endswith((".jar", ".disabled")):
                            mod_files.append(os.path.join(root, file))

            self.log(f"[*] Found {len(mod_files)} mod file(s) in mods/ directory.")

            mrpack_files_index = []
            override_mods = []

            if self.use_modrinth_api.get() and mod_files:
                self.log("[*] Computing SHA-1 & SHA-512 hashes for active mods...")
                hash_to_mod = {}
                for mf in mod_files:
                    if mf.endswith(".disabled"):
                        override_mods.append(mf)
                        continue
                    s1, s512 = self.get_file_hashes(mf)
                    hash_to_mod[s1] = (mf, s512)

                self.log(f"[*] Querying Modrinth API (/v2/version_files) for {len(hash_to_mod)} mod(s)...")
                try:
                    resp = requests.post(
                        "https://api.modrinth.com/v2/version_files",
                        json={"hashes": list(hash_to_mod.keys()), "algorithm": "sha1"},
                        headers={"User-Agent": f"{APP_NAME}/{APP_VERSION} (github.com)"},
                        timeout=25
                    )
                    if resp.status_code == 200:
                        found_data = resp.json()
                        for s1, (mf, s512) in hash_to_mod.items():
                            if s1 in found_data:
                                ver_info = found_data[s1]
                                matched_file = next(
                                    (f for f in ver_info.get("files", []) if f.get("hashes", {}).get("sha1") == s1),
                                    None
                                )
                                if matched_file and matched_file.get("url"):
                                    rel_path = os.path.relpath(mf, inst_dir).replace("\\", "/")
                                    mrpack_files_index.append({
                                        "path": rel_path,
                                        "hashes": {
                                            "sha1": s1,
                                            "sha512": matched_file["hashes"].get("sha512", s512)
                                        },
                                        "env": {"client": "required", "server": "required"},
                                        "downloads": [matched_file["url"]],
                                        "fileSize": os.path.getsize(mf)
                                    })
                                else:
                                    override_mods.append(mf)
                            else:
                                override_mods.append(mf)
                        self.log(f"[+] Linked {len(mrpack_files_index)} mod(s) directly to Modrinth CDN.")
                        self.log(f"[+] {len(override_mods)} CurseForge-exclusive/disabled mod(s) queued for overrides/.")
                    else:
                        self.log(f"[!] Modrinth API returned HTTP {resp.status_code}. Falling back to local overrides.")
                        override_mods = list(mod_files)
                except Exception as e:
                    self.log(f"[!] Modrinth API unreachable ({e}). Bundling all mods in overrides/.")
                    override_mods = list(mod_files)
            else:
                override_mods = list(mod_files)

            folders_to_copy = [
                "config", "defaultconfigs", "configureddefaults",
                "kubejs", "scripts", "patchouli_books", "fancymenu_data", "schematics"
            ]
            if self.include_shaders_rp.get():
                folders_to_copy.extend(["resourcepacks", "shaderpacks", "datapacks"])
            if self.include_saves.get():
                folders_to_copy.append("saves")

            override_files = list(override_mods)
            for folder in folders_to_copy:
                f_path = os.path.join(inst_dir, folder)
                if os.path.isdir(f_path):
                    for root, _, files in os.walk(f_path):
                        for file in files:
                            override_files.append(os.path.join(root, file))

            if self.include_options.get():
                for single_file in ["options.txt", "servers.dat", "optionsof.txt", "optionsshaders.txt"]:
                    sf_path = os.path.join(inst_dir, single_file)
                    if os.path.isfile(sf_path):
                        override_files.append(sf_path)

            total_to_pack = max(len(override_files) + 1, 1)
            self.log(f"[*] Compressing {len(override_files)} override file(s) into .mrpack archive...")

            index_data = {
                "formatVersion": 1,
                "game": "minecraft",
                "versionId": final_ver,
                "name": final_name,
                "summary": f"Converted from CurseForge instance ({final_name}) via {APP_NAME}",
                "files": mrpack_files_index,
                "dependencies": dependencies
            }

            os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)

            with zipfile.ZipFile(out_file, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("modrinth.index.json", json.dumps(index_data, indent=2, ensure_ascii=False))

                for idx, file_path in enumerate(override_files, start=1):
                    rel_path = os.path.relpath(file_path, inst_dir).replace("\\", "/")
                    arcname = f"overrides/{rel_path}"
                    zf.write(file_path, arcname)

                    if idx % 20 == 0 or idx == len(override_files):
                        self.set_progress(idx / total_to_pack)

            self.set_progress(1.0)
            size_mb = os.path.getsize(out_file) / (1024 * 1024)
            self.log(f"\n[SUCCESS] Build complete! ({size_mb:.2f} MB)\nSaved to: {out_file}")
            self.after(0, lambda: messagebox.showinfo(
                "Conversion Complete",
                f"Successfully created Modrinth modpack (.mrpack)!\n\nFile: {out_file}\nSize: {size_mb:.2f} MB"
            ))

        except Exception as e:
            self.log(f"\n[FATAL ERROR] {e}")
            self.after(0, lambda err=str(e): messagebox.showerror("Conversion Failed", err))
        finally:
            self.after(0, lambda: self.btn_convert.configure(state="normal", text="Build .mrpack Archive"))


if __name__ == "__main__":
    app = CFToMrpackApp()
    app.mainloop()
