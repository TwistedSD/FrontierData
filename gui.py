"""
EVE Frontier Data Extractor - GUI
Cross-platform GUI for extracting game data from EVE Frontier

Options:
- Galaxy: Solar system data (24,426 systems)
- Ships: All ships with full dogma stats + dependencies
- Modules: All modules with dogma stats + dependencies  
- Blueprints: All blueprints with types + dependencies

Each option automatically includes all dependent data.
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import sys
import os
import threading
import platform
import json
from pathlib import Path


class ExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EVE Frontier Data Extractor")
        self.root.geometry("850x700")
        
        # Determine default paths based on OS
        self.os_type = platform.system()
        self.default_game_path = self.get_default_game_path()
        self.default_output_path = self.get_default_output_path()
        
        # Variables
        self.game_path = tk.StringVar(value=self.default_game_path)
        self.output_path = tk.StringVar(value=self.default_output_path)
        self.is_running = False
        
        # Extraction options - none selected by default
        self.extract_galaxy = tk.BooleanVar(value=False)
        self.extract_ships = tk.BooleanVar(value=False)
        self.extract_modules = tk.BooleanVar(value=False)
        self.extract_blueprints = tk.BooleanVar(value=False)
        self.extract_ammo = tk.BooleanVar(value=False)
        self.extract_fuel = tk.BooleanVar(value=False)
        self.extract_materials = tk.BooleanVar(value=False)
        
        self.setup_ui()
        
    def get_default_game_path(self):
        """Get default code.ccp path based on OS"""
        if self.os_type == "Windows":
            return r"C:\CCP\EVE Frontier\stillness\code.ccp"
        elif self.os_type == "Darwin":  # macOS
            return os.path.expanduser("~/Library/Application Support/CCP/EVE Frontier/stillness/code.ccp")
        else:  # Linux
            return os.path.expanduser("~/.local/share/CCP/EVE Frontier/stillness/code.ccp")
    
    def get_default_output_path(self):
        """Get default output directory"""
        return os.path.join(os.getcwd(), "extracted_data")
    
    def setup_ui(self):
        """Setup the GUI components"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Title
        title_font = ('Helvetica', 16, 'bold')
        title_label = ttk.Label(main_frame, text="EVE Frontier Data Extractor", font=title_font)
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # code.ccp File Path
        ttk.Label(main_frame, text="Game Path:").grid(row=1, column=0, sticky=tk.W, pady=5)
        game_entry = ttk.Entry(main_frame, textvariable=self.game_path, width=60)
        game_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_game_path).grid(row=1, column=2, pady=5)
        
        # Output Path
        ttk.Label(main_frame, text="Output Folder:").grid(row=2, column=0, sticky=tk.W, pady=5)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_path, width=60)
        output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_output_path).grid(row=2, column=2, pady=5)
        
        # Data Selection Frame
        selection_frame = ttk.LabelFrame(main_frame, text="Select Data to Extract", padding="15")
        selection_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        selection_frame.columnconfigure(0, weight=1)
        selection_frame.columnconfigure(1, weight=1)
        selection_frame.columnconfigure(2, weight=1)
        
        # Create option cards
        # Row 0: Galaxy, Ships, Modules
        self.create_option_card(selection_frame, 0, 0,
            "Galaxy",
            "24,426 solar systems",
            "Coordinates, planets, stargates\nOutput: Galaxy.json (~389 MB)",
            self.extract_galaxy)
        
        self.create_option_card(selection_frame, 0, 1,
            "Ships",
            "14 ships with stats",
            "Dogma attributes, slot layouts\nOutput: Ships.json",
            self.extract_ships)
        
        self.create_option_card(selection_frame, 0, 2,
            "Modules",
            "142 modules",
            "Weapons, shields, engines\nOutput: Modules.json",
            self.extract_modules)
        
        # Row 1: Blueprints, Ammo, Fuel, Materials
        self.create_option_card(selection_frame, 1, 0,
            "Blueprints",
            "265 blueprints",
            "Manufacturing recipes\nOutput: Blueprints.json",
            self.extract_blueprints)
        
        self.create_option_card(selection_frame, 1, 1,
            "Ammo",
            "23 ammo types",
            "Projectiles, charges\nOutput: Ammo.json",
            self.extract_ammo)
        
        self.create_option_card(selection_frame, 1, 2,
            "Fuel",
            "10 fuel types",
            "Ship fuel, station fuel\nOutput: Fuel.json",
            self.extract_fuel)
        
        self.create_option_card(selection_frame, 2, 0,
            "Materials",
            "157 materials",
            "Ores, components, resources\nOutput: Materials.json",
            self.extract_materials)
        
        # Extract Button
        self.extract_btn = ttk.Button(main_frame, text="Extract Selected Data", 
                                      command=self.start_extraction)
        self.extract_btn.grid(row=4, column=0, columnspan=3, pady=20)
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=400)
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.progress.grid_remove()
        
        # Output Log
        output_frame = ttk.LabelFrame(main_frame, text="Output Log", padding="5")
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                     width=80, height=15, state='disabled')
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready - Select data to extract")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def create_option_card(self, parent, row, col, title, subtitle, details, variable):
        """Create an option card with checkbox"""
        card = ttk.Frame(parent, relief="groove", padding="10")
        card.grid(row=row, column=col, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Checkbox with title
        cb = ttk.Checkbutton(card, text=title, variable=variable)
        cb.grid(row=0, column=0, sticky=tk.W)
        
        # Subtitle
        sub_label = ttk.Label(card, text=subtitle, font=('Helvetica', 9, 'bold'))
        sub_label.grid(row=1, column=0, sticky=tk.W, padx=(20, 0))
        
        # Details
        detail_label = ttk.Label(card, text=details, font=('Helvetica', 8), foreground='gray')
        detail_label.grid(row=2, column=0, sticky=tk.W, padx=(20, 0), pady=(5, 0))
        
    def browse_game_path(self):
        """Browse for code.ccp file"""
        initial_dir = os.path.dirname(self.game_path.get())
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
        
        path = filedialog.askopenfilename(
            title="Select code.ccp file",
            initialdir=initial_dir,
            filetypes=[("CCP Files", "code.ccp"), ("All Files", "*.*")]
        )
        if path:
            self.game_path.set(path)
    
    def browse_output_path(self):
        """Browse for output folder"""
        initial_dir = self.output_path.get()
        if not os.path.exists(initial_dir):
            initial_dir = os.getcwd()
            
        path = filedialog.askdirectory(title="Select Output Folder", initialdir=initial_dir)
        if path:
            self.output_path.set(path)
    
    def log_message(self, message):
        """Add message to output log"""
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state='disabled')
    
    def clear_log(self):
        """Clear the output log"""
        self.output_text.configure(state='normal')
        self.output_text.delete(1.0, tk.END)
        self.output_text.configure(state='disabled')
    
    def validate_paths(self):
        """Validate game path"""
        code_ccp_path = self.game_path.get()
        
        if not os.path.exists(code_ccp_path):
            messagebox.showerror("Error", f"code.ccp file not found:\n{code_ccp_path}")
            return False
        
        if not code_ccp_path.endswith("code.ccp"):
            messagebox.showerror("Error", f"Please select the code.ccp file.\n\nSelected: {os.path.basename(code_ccp_path)}")
            return False
        
        game_dir = os.path.dirname(code_ccp_path)
        index_file = os.path.join(game_dir, "resfileindex.txt")
        
        if not os.path.exists(index_file):
            messagebox.showerror("Error", 
                f"Cannot find resfileindex.txt in:\n{game_dir}\n\n"
                "code.ccp should be in the stillness folder.")
            return False
        
        # Create output folder if needed
        output_dir = self.output_path.get()
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create output folder:\n{output_dir}\n\nError: {e}")
                return False
        
        return True
    
    def find_python312(self):
        """Find Python 3.12 installation"""
        py312_paths = [
            r"C:\Python312\python.exe",
            r"C:\Program Files\Python312\python.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Python\Python312\python.exe"),
            "py -3.12",
            "python3.12"
        ]
        
        for py_path in py312_paths:
            try:
                if py_path == "py -3.12":
                    result = subprocess.run(["py", "-3.12", "--version"], 
                                          capture_output=True, text=True, timeout=5)
                else:
                    result = subprocess.run([py_path, "--version"], 
                                          capture_output=True, text=True, timeout=5)
                if "3.12" in result.stdout or "3.12" in result.stderr:
                    return py_path
            except:
                continue
        
        return None
    
    def start_extraction(self):
        """Start extraction in separate thread"""
        if self.is_running:
            messagebox.showwarning("Warning", "Extraction is already running!")
            return
        
        # Check if at least one option selected
        if not any([self.extract_galaxy.get(), self.extract_ships.get(), 
                   self.extract_modules.get(), self.extract_blueprints.get(),
                   self.extract_ammo.get(), self.extract_fuel.get(),
                   self.extract_materials.get()]):
            messagebox.showwarning("Warning", "Please select at least one data type to extract!")
            return
        
        if not self.validate_paths():
            return
        
        self.clear_log()
        self.is_running = True
        self.extract_btn.configure(state='disabled')
        self.status_var.set("Extracting data...")
        self.progress.grid()
        self.progress.start(10)
        
        thread = threading.Thread(target=self.run_extraction, daemon=True)
        thread.start()
    
    def run_extraction(self):
        """Main extraction logic with dependency resolution"""
        try:
            code_ccp_path = self.game_path.get()
            output_folder = self.output_path.get()
            game_dir = os.path.dirname(code_ccp_path)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            self.log_message("="*70)
            self.log_message("EVE FRONTIER DATA EXTRACTOR")
            self.log_message("="*70)
            self.log_message(f"Game: {game_dir}")
            self.log_message(f"Output: {output_folder}")
            self.log_message("")
            
            # Determine what needs to be extracted based on dependencies
            need_galaxy = self.extract_galaxy.get()
            need_ships = self.extract_ships.get()
            need_modules = self.extract_modules.get()
            need_blueprints = self.extract_blueprints.get()
            need_ammo = self.extract_ammo.get()
            need_fuel = self.extract_fuel.get()
            need_materials = self.extract_materials.get()
            
            # Dependencies: any category except galaxy needs base data
            need_base_data = need_ships or need_modules or need_blueprints or need_ammo or need_fuel or need_materials
            need_types = need_base_data
            # Dogma needed for ships, modules, ammo, fuel (anything with stats)
            need_dogma = need_ships or need_modules or need_ammo or need_fuel or need_materials
            need_bp_data = need_base_data
            
            extraction_count = 0
            python312 = self.find_python312()
            
            if not python312 and (need_types or need_dogma):
                self.log_message("WARNING: Python 3.12 not found - required for types/dogma extraction")
                self.log_message("  Install from: https://www.python.org/downloads/")
                self.log_message("")
            
            # 1. Extract Galaxy (solar systems)
            if need_galaxy:
                self.log_message("="*70)
                self.log_message("EXTRACTING GALAXY DATA")
                self.log_message("="*70)
                
                cmd = [sys.executable, "extract_cli.py",
                       "--code-ccp", code_ccp_path,
                       "--output-folder", output_folder]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, cwd=script_dir)
                for line in process.stdout:
                    self.log_message(line.rstrip())
                process.wait()
                
                if process.returncode == 0:
                    extraction_count += 1
                    self.log_message("[OK] Galaxy data extracted")
                else:
                    self.log_message("[FAIL] Galaxy extraction failed")
                self.log_message("")
            
            # 2. Extract Blueprints (needed by ships/modules/blueprints option)
            if need_bp_data:
                self.log_message("="*70)
                self.log_message("EXTRACTING BLUEPRINTS DATA")
                self.log_message("="*70)
                
                if python312:
                    cmd = self.build_python312_cmd(python312, 
                           ["extract.py", "--blueprints",
                            "--game-path", game_dir,
                            "--output", output_folder])
                    
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                              text=True, bufsize=1, cwd=script_dir)
                    for line in process.stdout:
                        self.log_message(line.rstrip())
                    process.wait()
                    
                    if process.returncode == 0:
                        extraction_count += 1
                else:
                    # Fallback: extract blueprints directly
                    self.extract_blueprints_direct(game_dir, output_folder)
                    extraction_count += 1
                
                self.log_message("")
            
            # 3. Extract Types (needed by ships/modules/blueprints)
            if need_types and python312:
                self.log_message("="*70)
                self.log_message("EXTRACTING TYPES DATA")
                self.log_message("="*70)
                
                cmd = self.build_python312_cmd(python312,
                       ["extract.py", "--types", "--frontier-only",
                        "--game-path", game_dir,
                        "--output", output_folder])
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, cwd=script_dir)
                for line in process.stdout:
                    self.log_message(line.rstrip())
                process.wait()
                
                if process.returncode == 0:
                    extraction_count += 1
                self.log_message("")
            
            # 4. Extract Dogma for all types (needed for modules, ammo, etc.)
            if need_dogma and python312:
                self.log_message("="*70)
                self.log_message("EXTRACTING DOGMA DATA")
                self.log_message("="*70)
                
                cmd = self.build_python312_cmd(python312,
                       ["extract.py", "--dogma",
                        "--game-path", game_dir,
                        "--output", output_folder])
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, cwd=script_dir)
                for line in process.stdout:
                    self.log_message(line.rstrip())
                process.wait()
                self.log_message("")
            
            # 5. Extract Ships with dogma
            if need_ships and python312:
                self.log_message("="*70)
                self.log_message("EXTRACTING SHIPS DATA")
                self.log_message("="*70)
                
                cmd = self.build_python312_cmd(python312,
                       ["extract.py", "--ships",
                        "--game-path", game_dir,
                        "--output", output_folder])
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, cwd=script_dir)
                for line in process.stdout:
                    self.log_message(line.rstrip())
                process.wait()
                
                if process.returncode == 0:
                    extraction_count += 1
                    
                    # Create Ships.json with all dependencies (uses any Python)
                    self.log_message("\nCreating Ships.json with manufacturing dependencies...")
                    cmd2 = [sys.executable, "extract_selective.py",
                            "--category", "ships",
                            "--output", os.path.join(output_folder, "Ships.json"),
                            "--data-path", output_folder]
                    
                    process2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                               text=True, bufsize=1, cwd=script_dir)
                    for line in process2.stdout:
                        self.log_message(line.rstrip())
                    process2.wait()
                
                self.log_message("")
            
            # 5. Extract Modules (uses any Python - just needs JSON data)
            if need_modules:
                self.log_message("="*70)
                self.log_message("EXTRACTING MODULES DATA")
                self.log_message("="*70)
                
                # Create Modules.json with all dependencies
                cmd = [sys.executable, "extract_selective.py",
                       "--category", "modules",
                       "--output", os.path.join(output_folder, "Modules.json"),
                       "--data-path", output_folder]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, cwd=script_dir)
                for line in process.stdout:
                    self.log_message(line.rstrip())
                process.wait()
                
                if process.returncode == 0:
                    extraction_count += 1
                self.log_message("")
            
            # 6. Create Blueprints.json if blueprints option selected
            if need_blueprints:
                self.log_message("="*70)
                self.log_message("CREATING BLUEPRINTS.JSON")
                self.log_message("="*70)
                
                # Create Blueprints.json with all dependencies
                cmd = [sys.executable, "extract_selective.py",
                       "--category", "blueprints",
                       "--output", os.path.join(output_folder, "Blueprints.json"),
                       "--data-path", output_folder]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, cwd=script_dir)
                for line in process.stdout:
                    self.log_message(line.rstrip())
                process.wait()
                
                if process.returncode == 0:
                    extraction_count += 1
                self.log_message("")
            
            # 7. Create Ammo.json if ammo option selected
            if need_ammo:
                self.log_message("="*70)
                self.log_message("EXTRACTING AMMO DATA")
                self.log_message("="*70)
                
                cmd = [sys.executable, "extract_selective.py",
                       "--category", "ammo",
                       "--output", os.path.join(output_folder, "Ammo.json"),
                       "--data-path", output_folder]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, cwd=script_dir)
                for line in process.stdout:
                    self.log_message(line.rstrip())
                process.wait()
                
                if process.returncode == 0:
                    extraction_count += 1
                self.log_message("")
            
            # 8. Create Fuel.json if fuel option selected
            if need_fuel:
                self.log_message("="*70)
                self.log_message("EXTRACTING FUEL DATA")
                self.log_message("="*70)
                
                cmd = [sys.executable, "extract_selective.py",
                       "--category", "fuel",
                       "--output", os.path.join(output_folder, "Fuel.json"),
                       "--data-path", output_folder]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, cwd=script_dir)
                for line in process.stdout:
                    self.log_message(line.rstrip())
                process.wait()
                
                if process.returncode == 0:
                    extraction_count += 1
                self.log_message("")
            
            # 9. Create Materials.json if materials option selected
            if need_materials:
                self.log_message("="*70)
                self.log_message("EXTRACTING MATERIALS DATA")
                self.log_message("="*70)
                
                cmd = [sys.executable, "extract_selective.py",
                       "--category", "materials",
                       "--output", os.path.join(output_folder, "Materials.json"),
                       "--data-path", output_folder]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                          text=True, bufsize=1, cwd=script_dir)
                for line in process.stdout:
                    self.log_message(line.rstrip())
                process.wait()
                
                if process.returncode == 0:
                    extraction_count += 1
                self.log_message("")
            
            # Summary
            self.log_message("="*70)
            self.log_message("EXTRACTION COMPLETE")
            self.log_message("="*70)
            
            # List output files
            output_path = Path(output_folder)
            json_files = sorted(output_path.glob("*.json"))
            if json_files:
                self.log_message("\nExtracted files:")
                for f in json_files:
                    size = f.stat().st_size
                    if size > 1024*1024:
                        size_str = f"{size / (1024*1024):.1f} MB"
                    else:
                        size_str = f"{size / 1024:.1f} KB"
                    self.log_message(f"  {f.name}: {size_str}")
            
            self.log_message("")
            
            if extraction_count > 0:
                self.log_message(f"[OK] Successfully extracted {extraction_count} data type(s)!")
                self.status_var.set(f"Completed - {extraction_count} extracted")
                messagebox.showinfo("Success", 
                    f"Extracted {extraction_count} data type(s)!\n\nOutput: {output_folder}")
            else:
                self.log_message("[FAIL] No data was extracted")
                self.status_var.set("Extraction failed")
                messagebox.showerror("Error", "Extraction failed. Check the log for details.")
        
        except Exception as e:
            self.log_message(f"ERROR: {str(e)}")
            self.status_var.set("Error occurred")
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
        
        finally:
            self.progress.stop()
            self.progress.grid_remove()
            self.is_running = False
            self.extract_btn.configure(state='normal')
    
    def build_python312_cmd(self, python312, args):
        """Build command for Python 3.12"""
        if python312 == "py -3.12":
            return ["py", "-3.12"] + args
        else:
            return [python312] + args
    
    def extract_blueprints_direct(self, game_dir, output_folder):
        """Extract blueprints without Python 3.12 (uses SQLite directly)"""
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from extract_static_files import GameDataExtractor
            import sqlite3
            
            extractor = GameDataExtractor(game_dir)
            extractor.parse_index_file()
            
            matches = extractor.find_entry("blueprints.static")
            if matches:
                entry = matches[0]
                self.log_message(f"Found: {entry['resource_path']}")
                
                blueprints_static = os.path.join(output_folder, "blueprints.static")
                data = extractor.extract_data(entry, blueprints_static)
                
                if data:
                    conn = sqlite3.connect(blueprints_static)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    output_data = {}
                    for table in tables:
                        cursor.execute(f"SELECT * FROM {table}")
                        rows = cursor.fetchall()
                        col_names = [desc[0] for desc in cursor.description]
                        output_data[table] = [
                            {col_names[i]: row[i] for i in range(len(col_names))}
                            for row in rows
                        ]
                    
                    conn.close()
                    
                    blueprints_json = os.path.join(output_folder, "blueprints.json")
                    with open(blueprints_json, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False)
                    
                    os.remove(blueprints_static)
                    self.log_message(f"[OK] Extracted {len(output_data.get('cache', []))} blueprints")
        except Exception as e:
            self.log_message(f"[FAIL] Error: {e}")


def main():
    try:
        root = tk.Tk()
        app = ExtractorGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nUse command-line instead: python extract.py --help")
        sys.exit(1)


if __name__ == "__main__":
    main()
