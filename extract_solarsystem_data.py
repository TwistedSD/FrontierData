"""
Extract solar system data from EVE Frontier using Python 3.12 subprocess
"""

import subprocess
import sys
import os
import shutil
import argparse

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Extract solar system data from EVE Frontier game files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default paths
  python extract_solarsystem_data.py
  
  # Specify custom game folder
  python extract_solarsystem_data.py --game-path "C:\\CCP\\EVE Frontier"
  
  # Specify custom output folder
  python extract_solarsystem_data.py --output-folder "C:\\MyData\\EVE"
  
  # Specify both
  python extract_solarsystem_data.py --game-path "/path/to/eve" --output-folder "./output"
        """
    )
    parser.add_argument(
        '--game-path', '-g',
        help='Path to EVE Frontier installation folder (will look for stillness subfolder)',
        default=None
    )
    parser.add_argument(
        '--output-folder', '-o',
        help='Folder where solarsystemcontent.json will be saved',
        default=None
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("EVE FRONTIER SOLAR SYSTEM DATA EXTRACTOR")
    print("="*70)
    
    # Determine paths - priority: CLI args > environment variables > defaults
    if args.game_path:
        game_folder = args.game_path
        GAME_PATH = os.path.join(game_folder, "stillness")
    else:
        GAME_PATH = os.environ.get('GAME_PATH', r"C:\CCP\EVE Frontier\stillness")
    
    if args.output_folder:
        OUTPUT_FILE = os.path.join(args.output_folder, 'solarsystemcontent.json')
    else:
        OUTPUT_FILE = os.environ.get('OUTPUT_PATH', os.path.join('extracted_data', 'solarsystemcontent.json'))
    
    CODE_CCP = os.path.join(GAME_PATH, "code.ccp")
    STATIC_FILE = os.path.join(os.path.dirname(OUTPUT_FILE) or 'extracted_data', 'solarsystemcontent.static')
    PY312_SCRIPT = "load_fsd_py312.py"
    
    # Show paths
    print(f"\nGame path: {GAME_PATH}")
    print(f"Output file: {OUTPUT_FILE}")
    
    # Validate game path
    if not os.path.exists(GAME_PATH):
        print(f"\nERROR: Game path does not exist: {GAME_PATH}")
        sys.exit(1)
    
    if not os.path.exists(os.path.join(GAME_PATH, "resfileindex.txt")):
        print(f"\nERROR: Cannot find resfileindex.txt in: {GAME_PATH}")
        print("Make sure you point to the EVE Frontier installation folder.")
        sys.exit(1)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE) or 'extracted_data', exist_ok=True)
    
    # Step 1: Extract .static file if it doesn't exist
    if not os.path.exists(STATIC_FILE):
        print("\nStep 1: Extracting .static file from game files...")
        try:
            # Set environment variables for extract_game_data.py
            env = os.environ.copy()
            env['GAME_PATH'] = GAME_PATH
            env['OUTPUT_PATH'] = OUTPUT_FILE
            
            result = subprocess.run(
                [sys.executable, "extract_game_data.py"],
                capture_output=True,
                text=True,
                timeout=60,
                env=env
            )
            print(result.stdout)
            if result.returncode != 0:
                print("ERROR extracting game data:")
                print(result.stderr)
                sys.exit(1)
            if not os.path.exists(STATIC_FILE):
                print(f"ERROR: {STATIC_FILE} was not created")
                sys.exit(1)
            print("OK Extraction complete")
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)
    else:
        print(f"\nOK Found existing {STATIC_FILE}")
    
    # Step 2: Check if Python 3.12 is available
    print("\nStep 2: Checking for Python 3.12...")
    py312_paths = [
        r"C:\Python312\python.exe",
        r"C:\Program Files\Python312\python.exe",
        r"C:\Users\demps\AppData\Local\Programs\Python\Python312\python.exe",
        "py -3.12",
        "python3.12"
    ]
    
    python312 = None
    for py_path in py312_paths:
        try:
            result = subprocess.run(
                [py_path if not py_path.startswith("py ") else "py", "-3.12" if py_path.startswith("py ") else "--version"],
                capture_output=True, text=True, timeout=5
            )
            if "3.12" in result.stdout or "3.12" in result.stderr:
                python312 = py_path
                print(f"OK Found Python 3.12: {py_path}")
                break
        except:
            continue
    
    if not python312:
        print("\n" + "="*70)
        print("ERROR: Python 3.12 NOT FOUND!")
        print("="*70)
        print("""
EVE Frontier's FSD loaders require Python 3.12.

Options to proceed:
1. Install Python 3.12 from https://www.python.org/downloads/
2. Use 'py' launcher: py -3.12 -m pip install --upgrade pip
3. Clone Phobos fsdbinary-t1 branch which handles this automatically

Your current Python version: """ + sys.version)
        
        print("\nAlternatively, I can build a pure Python parser...")
        sys.exit(1)
    
    print(f"\nUsing: {python312}")
    print(f"Input:  {STATIC_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    
    # Step 3: Run the Python 3.12 script
    print("\nStep 3: Calling Python 3.12 to load FSD data...")
    print("(This may take a minute - 68MB of binary data to parse)")
    
    try:
        cmd = [python312, PY312_SCRIPT, CODE_CCP, STATIC_FILE, OUTPUT_FILE]
        if python312.startswith("py "):
            cmd = ["py", "-3.12", PY312_SCRIPT, CODE_CCP, STATIC_FILE, OUTPUT_FILE]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        print("\nPython 3.12 output:")
        print(result.stdout)
        
        if result.returncode != 0:
            print("\nERROR:")
            print(result.stderr)
            sys.exit(1)
        
        print("\n" + "="*70)
        print("SUCCESS!")
        print("="*70)
        print(f"Solar system data extracted to: {OUTPUT_FILE}")
        
        # Show file size
        if os.path.exists(OUTPUT_FILE):
            size_mb = os.path.getsize(OUTPUT_FILE) / (1024*1024)
            print(f"Output file size: {size_mb:.1f} MB")
        
        # Clean up temporary files
        print("\nCleaning up temporary files...")
        temp_dirs = ["temp_code_ccp_py312", "temp_code_ccp"]
        output_dir = os.path.dirname(OUTPUT_FILE) or 'extracted_data'
        temp_files = [
            STATIC_FILE, 
            os.path.join(output_dir, "analysis_report.txt")
        ]
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"  Removed: {temp_dir}/")
        
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
                print(f"  Removed: {temp_file}")
        
        print("OK Cleanup complete")
    
    except subprocess.TimeoutExpired:
        print("\nERROR: Process timed out after 5 minutes")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
