"""
EVE Frontier Data Extractor - Unified CLI
Extracts solar systems, blueprints, and types data from EVE Frontier
"""

import subprocess
import sys
import os
import shutil
import argparse
import json
import tempfile
import importlib
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def extract_solarsystem_and_blueprints(game_path, output_folder):
    """Extract solar system and blueprints data - currently not supported in CLI"""
    print("="*70)
    print("EXTRACTING SOLAR SYSTEMS & BLUEPRINTS")
    print("="*70)
    print("\n⚠ Solar systems and blueprints extraction via CLI is not yet supported.")
    print("   These require complex Python 3.12 + code.ccp integration.")
    print("   Please use the GUI (gui.py) for solar systems and blueprints extraction.")
    print("\n   Run: python gui.py")
    return False

def extract_types(game_path, output_folder):
    """Extract types data using typesLoader.pyd"""
    print("="*70)
    print("EXTRACTING TYPES DATA")
    print("="*70)
    
    game_path = Path(game_path)
    loader_dll = game_path / "bin64" / "typesLoader.pyd"
    types_fsdbinary = "res:/staticdata/types.fsdbinary"
    
    # Check if loader exists
    if not loader_dll.exists():
        print(f"✗ Loader not found: {loader_dll}")
        print("  Types extraction requires Python 3.12 and typesLoader.pyd from bin64")
        return False
    
    print(f"\n✓ Found typesLoader.pyd: {loader_dll}")
    print(f"  Size: {loader_dll.stat().st_size:,} bytes")
    
    # Find types.fsdbinary in ResFiles
    print(f"\nLocating types.fsdbinary...")
    index_file = game_path / "resfileindex.txt"
    
    index_data = {}
    with open(index_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) >= 5:
                index_data[parts[0]] = {
                    'hash_path': parts[1],
                    'file_hash': parts[2],
                    'offset': int(parts[3]),
                    'size': int(parts[4])
                }
    
    if types_fsdbinary not in index_data:
        print(f"✗ types.fsdbinary not in index")
        return False
    
    entry = index_data[types_fsdbinary]
    print(f"✓ Found in index:")
    print(f"  Hash path: {entry['hash_path']}")
    print(f"  Offset: {entry['offset']:,}")
    print(f"  Size: {entry['size']:,}")
    
    # Locate ResFile
    resfiles_dir = game_path.parent / "ResFiles"
    resfile_path = resfiles_dir / entry['hash_path']
    if not resfile_path.exists():
        print(f"✗ ResFile not found: {resfile_path}")
        return False
    
    file_size = resfile_path.stat().st_size
    print(f"  ResFile size: {file_size:,}")
    
    # Read ResFile
    print(f"\nReading ResFile...")
    with open(resfile_path, 'rb') as f:
        if entry['offset'] < file_size:
            f.seek(entry['offset'])
            types_binary = f.read(entry['size'])
        else:
            # If offset is beyond file, read the whole file
            types_binary = f.read()
    
    print(f"✓ Read {len(types_binary):,} bytes")
    
    # Save binary data temporarily
    output_dir = Path(output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    types_temp = output_dir / "types_temp.fsdbinary"
    with open(types_temp, 'wb') as f:
        f.write(types_binary)
    
    print(f"✓ Saved binary to: {types_temp}")
    
    # Load using typesLoader.pyd
    print(f"\nLoading with typesLoader.pyd...")
    
    with tempfile.TemporaryDirectory(prefix="types_extract_", ignore_cleanup_errors=True) as temp_dir:
        temp_dir = Path(temp_dir)
        
        # Copy loader to temp directory
        temp_loader = temp_dir / "typesLoader.pyd"
        shutil.copy2(loader_dll, temp_loader)
        
        # Add temp directory to path
        sys.path.insert(0, str(temp_dir))
        
        try:
            # Import the loader
            typesLoader = importlib.import_module('typesLoader')
            print(f"✓ Imported typesLoader")
            
            # Load the data
            fsd_data = typesLoader.load(str(types_temp))
            
            print(f"✓ Loaded FSD data")
            print(f"  Type: {type(fsd_data)}")
            print(f"  Length: {len(fsd_data) if hasattr(fsd_data, '__len__') else 'N/A'}")
            
            # Convert to JSON-serializable format
            print(f"\nConverting to JSON format...")
            
            def convert_fsd_to_dict(obj):
                """Recursively convert FSD objects to dictionaries"""
                obj_type_name = type(obj).__name__
                obj_module = type(obj).__module__
                
                if obj_type_name == 'dict' and hasattr(obj, 'items'):
                    # cfsd.dict type - iterate like a normal dict
                    result = {}
                    for key, value in obj.items():
                        result[convert_fsd_to_dict(key)] = convert_fsd_to_dict(value)
                    return result
                elif obj_type_name == 'type' and obj_module == 'typesLoader':
                    # typesLoader.type - extract all public attributes
                    result = {}
                    for attr in dir(obj):
                        if not attr.startswith('_'):
                            try:
                                value = getattr(obj, attr)
                                result[attr] = convert_fsd_to_dict(value)
                            except:
                                pass
                    return result
                elif isinstance(obj, dict):
                    return {convert_fsd_to_dict(k): convert_fsd_to_dict(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [convert_fsd_to_dict(item) for item in obj]
                elif isinstance(obj, (int, float, str, bool, type(None))):
                    return obj
                elif hasattr(obj, '__dict__') and not isinstance(obj, type):
                    result = {}
                    for key, value in obj.__dict__.items():
                        if not key.startswith('_'):
                            result[key] = convert_fsd_to_dict(value)
                    return result
                else:
                    return str(obj)
            
            data_dict = convert_fsd_to_dict(fsd_data)
            
            # Save to JSON
            output_file = output_dir / "types.json"
            print(f"\nSaving to: {output_file}")
            
            # Use indent=2 for readable formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            
            file_size = output_file.stat().st_size
            print(f"✓ Saved! Size: {file_size / (1024*1024):.1f} MB")
            print(f"✓ Total types: {len(data_dict):,}")
            
            # Show sample
            if data_dict:
                first_key = next(iter(data_dict))
                sample = data_dict[first_key]
                print(f"\nSample type (ID {first_key}):")
                for key, value in list(sample.items())[:10]:
                    print(f"  {key}: {value}")
            
            # Cleanup temp binary
            types_temp.unlink()
            
            return True
            
        except Exception as e:
            print(f"✗ Error loading types: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Remove temp dir from path
            sys.path.remove(str(temp_dir))

def main():
    parser = argparse.ArgumentParser(
        description='Extract data from EVE Frontier game files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract types data (recommended - works in CLI)
  python extract.py --types
  
  # Custom paths
  python extract.py --types --game-path "C:\\CCP\\EVE Frontier\\stillness" --output "./data"
  
  # Help
  python extract.py --help

Note: 
  - Types extraction requires Python 3.12
  - Solar systems and blueprints extraction currently only supported via GUI
  - Run 'python gui.py' for solar systems and blueprints
        """
    )
    
    parser.add_argument('--game-path', '-g',
                       help='Path to game directory (EVE Frontier/stillness)',
                       default=None)
    parser.add_argument('--output', '-o',
                       help='Output folder for extracted data',
                       default=None)
    parser.add_argument('--all', '-a',
                       action='store_true',
                       help='Extract all available data types')
    parser.add_argument('--solar-systems', '-s',
                       action='store_true',
                       help='Extract solar system data')
    parser.add_argument('--blueprints', '-b',
                       action='store_true',
                       help='Extract blueprints data')
    parser.add_argument('--types', '-t',
                       action='store_true',
                       help='Extract types data (requires Python 3.12)')
    
    args = parser.parse_args()
    
    # Determine game path
    if args.game_path:
        game_path = args.game_path
    else:
        game_path = os.environ.get('GAME_PATH', r"C:\CCP\EVE Frontier\stillness")
    
    # Determine output folder
    if args.output:
        output_folder = args.output
    else:
        output_folder = os.path.join(os.getcwd(), 'extracted_data')
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    print("="*70)
    print("EVE FRONTIER DATA EXTRACTOR")
    print("="*70)
    print(f"Game path: {game_path}")
    print(f"Output folder: {output_folder}")
    print()
    
    # Validate game path
    if not os.path.exists(os.path.join(game_path, "resfileindex.txt")):
        print(f"ERROR: Cannot find resfileindex.txt in: {game_path}")
        print("Please specify the correct game path using --game-path")
        sys.exit(1)
    
    # Determine what to extract
    extract_solar = args.all or args.solar_systems
    extract_bp = args.all or args.blueprints
    extract_types_data = args.all or args.types
    
    # If nothing specified, show help
    if not (extract_solar or extract_bp or extract_types_data):
        parser.print_help()
        print("\nNo extraction options specified. Use --all or specific options.")
        sys.exit(0)
    
    success_count = 0
    
    # Extract solar systems and blueprints
    if extract_solar or extract_bp:
        try:
            extract_solarsystem_and_blueprints(game_path, output_folder)
            success_count += 1
        except Exception as e:
            print(f"✗ Error extracting solar systems/blueprints: {e}")
            import traceback
            traceback.print_exc()
    
    # Extract types
    if extract_types_data:
        print()
        if extract_types(game_path, output_folder):
            success_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("EXTRACTION COMPLETE")
    print("="*70)
    print(f"Output folder: {output_folder}")
    print(f"Extracted files: Check {output_folder} for output")
    
    if success_count > 0:
        print("\n✓ Extraction successful!")
    else:
        print("\n✗ No data was extracted")
        sys.exit(1)

if __name__ == "__main__":
    main()
