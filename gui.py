"""
EVE Frontier Solar System Data Extractor - GUI
Cross-platform GUI for extracting solar system data from EVE Frontier
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import sys
import os
import threading
import platform

class ExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EVE Frontier Data Extractor")
        self.root.geometry("800x600")
        
        # Determine default paths based on OS
        self.os_type = platform.system()
        self.default_game_path = self.get_default_game_path()
        self.default_output_path = self.get_default_output_path()
        
        # Variables
        self.game_path = tk.StringVar(value=self.default_game_path)
        self.output_path = tk.StringVar(value=self.default_output_path)
        self.is_running = False
        
        # Check Tk version for compatibility (parse major.minor only)
        try:
            tk_version_str = self.root.tk.call('info', 'patchlevel')
            # Parse only major.minor (e.g., "8.6.15" -> 8.6)
            version_parts = tk_version_str.split('.')
            self.tk_version = float(f"{version_parts[0]}.{version_parts[1]}")
        except:
            self.tk_version = 8.6  # Default fallback
        
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
        main_frame.rowconfigure(4, weight=1)
        
        # Title (use default font for better compatibility)
        try:
            title_font = ('Helvetica', 16, 'bold')
        except:
            title_font = ('TkDefaultFont', 16, 'bold')
        
        title_label = ttk.Label(main_frame, text="EVE Frontier Solar System Data Extractor", 
                                font=title_font)
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # code.ccp File Path
        ttk.Label(main_frame, text="code.ccp File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        game_entry = ttk.Entry(main_frame, textvariable=self.game_path, width=50)
        game_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_game_path).grid(row=1, column=2, pady=5)
        
        # Output Path
        ttk.Label(main_frame, text="Output Folder:").grid(row=2, column=0, sticky=tk.W, pady=5)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_path, width=50)
        output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(main_frame, text="Browse...", command=self.browse_output_path).grid(row=2, column=2, pady=5)
        
        # Extract Button (no special styling for compatibility)
        self.extract_btn = ttk.Button(main_frame, text="Extract Solar System Data", 
                                      command=self.start_extraction)
        self.extract_btn.grid(row=3, column=0, columnspan=3, pady=20)
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=400)
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.progress.grid_remove()  # Hide initially
        
        # Progress/Output Area
        output_frame = ttk.LabelFrame(main_frame, text="Output Log", padding="5")
        output_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, 
                                                     width=70, height=20, state='disabled')
        self.output_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Status Bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def browse_game_path(self):
        """Browse for code.ccp file"""
        path = filedialog.askopenfilename(
            title="Select code.ccp file",
            initialdir=os.path.dirname(self.game_path.get()) if os.path.exists(os.path.dirname(self.game_path.get())) else os.getcwd(),
            filetypes=[("CCP Files", "code.ccp"), ("All Files", "*.*")]
        )
        if path:
            self.game_path.set(path)
    
    def browse_output_path(self):
        """Browse for output folder location"""
        path = filedialog.askdirectory(
            title="Select Output Folder",
            initialdir=self.output_path.get() if os.path.exists(self.output_path.get()) else os.getcwd()
        )
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
        """Validate that paths are correct"""
        code_ccp_path = self.game_path.get()
        
        # Check if code.ccp file exists
        if not os.path.exists(code_ccp_path):
            messagebox.showerror("Error", f"code.ccp file does not exist:\n{code_ccp_path}")
            return False
        
        # Check if it's actually the code.ccp file
        if not code_ccp_path.endswith("code.ccp"):
            messagebox.showerror("Error", 
                f"Please select the code.ccp file.\n\nSelected: {os.path.basename(code_ccp_path)}")
            return False
        
        # Get the directory (should be stillness folder)
        game_dir = os.path.dirname(code_ccp_path)
        
        # Check for resfileindex.txt in same directory
        index_file = os.path.join(game_dir, "resfileindex.txt")
        if not os.path.exists(index_file):
            messagebox.showerror("Error", 
                f"Cannot find resfileindex.txt in:\n{game_dir}\n\n"
                "code.ccp should be in the stillness folder with resfileindex.txt.")
            return False
        
        # Check output folder
        output_dir = self.output_path.get()
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create output folder:\n{output_dir}\n\nError: {e}")
                return False
        
        return True
    
    def start_extraction(self):
        """Start the extraction process in a separate thread"""
        if self.is_running:
            messagebox.showwarning("Warning", "Extraction is already running!")
            return
        
        if not self.validate_paths():
            return
        
        # Clear log and start
        self.clear_log()
        self.is_running = True
        self.extract_btn.configure(state='disabled')
        self.status_var.set("Please wait - Extracting data...")
        
        # Show and start progress bar
        self.progress.grid()
        self.progress.start(10)  # Animate every 10ms
        
        # Run extraction in separate thread
        thread = threading.Thread(target=self.run_extraction, daemon=True)
        thread.start()
    
    def run_extraction(self):
        """Run the extraction process"""
        try:
            code_ccp_path = self.game_path.get()
            output_folder = self.output_path.get()
            
            # Build full paths
            output_file = os.path.join(output_folder, "solarsystemcontent.json")
            
            # Update environment variables for the extraction script (for backwards compatibility)
            env = os.environ.copy()
            
            self.log_message("="*70)
            self.log_message("EVE FRONTIER SOLAR SYSTEM DATA EXTRACTOR")
            self.log_message("="*70)
            self.log_message(f"code.ccp: {code_ccp_path}")
            self.log_message(f"Output File: {output_file}")
            self.log_message("")
            
            # Run the extraction script with command-line arguments
            cmd = [sys.executable, "extract_solarsystem_data.py",
                   "--code-ccp", code_ccp_path,
                   "--output-folder", output_folder]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # Read output line by line
            for line in process.stdout:
                self.log_message(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                self.log_message("")
                self.log_message("="*70)
                self.log_message("SUCCESS - EXTRACTION COMPLETED!")
                self.log_message("="*70)
                self.status_var.set("Completed successfully")
                
                # Show output file size
                if os.path.exists(output_file):
                    size_mb = os.path.getsize(output_file) / (1024*1024)
                    self.log_message(f"Output file size: {size_mb:.1f} MB")
                
                messagebox.showinfo("Success", 
                    f"Solar system data extracted successfully!\n\n"
                    f"Output: {output_file}")
            else:
                self.log_message("")
                self.log_message("="*70)
                self.log_message("EXTRACTION FAILED")
                self.log_message("="*70)
                self.status_var.set("Extraction failed")
                messagebox.showerror("Error", "Extraction failed. Check the output log for details.")
        
        except Exception as e:
            self.log_message(f"ERROR: {str(e)}")
            self.status_var.set("Error occurred")
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")
        
        finally:
            # Stop and hide progress bar
            self.progress.stop()
            self.progress.grid_remove()
            
            self.is_running = False
            self.extract_btn.configure(state='normal')
            if self.status_var.get() == "Please wait - Extracting data...":
                self.status_var.set("Ready")

def main():
    try:
        root = tk.Tk()
        
        # Check Tk version
        tk_version = root.tk.call('info', 'patchlevel')
        print(f"Tk version: {tk_version}")
        
        # Create the app
        app = ExtractorGUI(root)
        root.mainloop()
        
    except tk.TclError as e:
        error_msg = str(e)
        print(f"ERROR: Failed to start GUI: {e}")
        
        if "version" in error_msg.lower() or "required" in error_msg.lower():
            print("\n" + "="*70)
            print("Your Tk/Tcl version is not compatible with this GUI.")
            print("="*70)
            print("\nOptions to proceed:")
            print("1. Use the command-line version (no GUI required):")
            print("     python extract_solarsystem_data.py")
            print("\n2. Update Python to the latest version:")
            print("     https://www.python.org/downloads/")
            print("\n3. On macOS, install Python via Homebrew:")
            print("     brew install python-tk@3.12")
        else:
            print("\nPlease use the command-line version:")
            print("  python extract_solarsystem_data.py")
        
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error starting GUI: {e}")
        print("\nPlease use the command-line version:")
        print("  python extract_solarsystem_data.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
