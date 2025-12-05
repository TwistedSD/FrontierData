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

def parse_resfileindex(game_path):
    """Parse resfileindex.txt and return a dict of resource paths to file info"""
    index_file = Path(game_path) / "resfileindex.txt"
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
    
    return index_data


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


def extract_blueprints(game_path, output_folder):
    """Extract blueprints data from blueprints.static (SQLite database)"""
    print("="*70)
    print("EXTRACTING BLUEPRINTS DATA")
    print("="*70)
    
    game_path = Path(game_path)
    output_dir = Path(output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse index to find blueprints.static
    index_data = parse_resfileindex(game_path)
    
    bp_key = "res:/staticdata/blueprints.static"
    if bp_key not in index_data:
        print(f"✗ blueprints.static not found in index")
        return False
    
    entry = index_data[bp_key]
    print(f"✓ Found blueprints.static")
    print(f"  Hash: {entry['hash_path']}")
    print(f"  Size: {entry['size']:,} bytes")
    
    # Locate ResFile
    resfiles_dir = game_path.parent / "ResFiles"
    resfile_path = resfiles_dir / entry['hash_path']
    
    if not resfile_path.exists():
        print(f"✗ ResFile not found: {resfile_path}")
        return False
    
    # It's a SQLite database - query it directly
    import sqlite3
    
    conn = sqlite3.connect(str(resfile_path))
    cursor = conn.cursor()
    
    # Get all cache data
    cursor.execute('SELECT key, value, time FROM cache')
    cache_data = cursor.fetchall()
    
    # Get all indexes
    cursor.execute('SELECT key, value FROM indexes')
    index_table_data = cursor.fetchall()
    
    conn.close()
    
    # Format the data
    blueprints = {
        'cache': [{'key': k, 'value': v, 'time': t} for k, v, t in cache_data],
        'indexes': [{'key': k, 'value': v} for k, v in index_table_data]
    }
    
    # Save to JSON
    output_file = output_dir / "blueprints.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(blueprints, f, indent=2, ensure_ascii=False)
    
    file_size = output_file.stat().st_size
    print(f"✓ Saved {len(blueprints['cache'])} blueprints to blueprints.json ({file_size / 1024:.1f} KB)")
    
    return True


def extract_ships(game_path, output_folder):
    """Extract ships data with full dogma attributes"""
    print("="*70)
    print("EXTRACTING SHIPS DATA")
    print("="*70)
    
    game_path = Path(game_path)
    output_dir = Path(output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for required loaders
    bin64_dir = game_path / "bin64"
    required_loaders = ['typeDogmaLoader.pyd', 'dogmaAttributesLoader.pyd', 'dogmaUnitsLoader.pyd']
    
    for loader in required_loaders:
        if not (bin64_dir / loader).exists():
            print(f"✗ Required loader not found: {loader}")
            print("  Ships extraction requires Python 3.12 and loaders from bin64")
            return False
    
    print(f"✓ Found all required loaders in {bin64_dir}")
    
    # Parse index to find required files
    index_data = parse_resfileindex(game_path)
    
    required_files = {
        'typedogma': 'res:/staticdata/typedogma.fsdbinary',
        'dogmaattributes': 'res:/staticdata/dogmaattributes.fsdbinary',
        'dogmaunits': 'res:/staticdata/dogmaunits.fsdbinary',
        'localization': 'res:/localizationfsd/localization_fsd_en-us.pickle'
    }
    
    file_paths = {}
    resfiles_dir = game_path.parent / "ResFiles"
    
    for name, res_key in required_files.items():
        if res_key not in index_data:
            print(f"✗ {name} not found in index")
            return False
        entry = index_data[res_key]
        file_path = resfiles_dir / entry['hash_path']
        if not file_path.exists():
            print(f"✗ ResFile not found: {file_path}")
            return False
        file_paths[name] = str(file_path)
        print(f"✓ Found {name}: {entry['hash_path'][:40]}...")
    
    # Need types_frontier.json - check if it exists or extract types first
    types_file = output_dir / "types_frontier.json"
    if not types_file.exists():
        print(f"\n⚠ types_frontier.json not found - extracting types first...")
        if not extract_types(str(game_path), str(output_dir)):
            return False
        # Also need to create types_frontier from blueprints
        if not (output_dir / "blueprints.json").exists():
            extract_blueprints(str(game_path), str(output_dir))
        # Create types_frontier
        create_types_frontier(str(output_dir))
    
    # Load with loaders from bin64 directory
    print(f"\nLoading dogma data...")
    
    original_cwd = os.getcwd()
    original_path = sys.path.copy()
    
    try:
        os.chdir(str(bin64_dir))
        sys.path.insert(0, str(bin64_dir))
        
        import typeDogmaLoader
        import dogmaAttributesLoader
        import dogmaUnitsLoader
        import pickle
        
        typedogma = typeDogmaLoader.load(file_paths['typedogma'])
        attrs = dogmaAttributesLoader.load(file_paths['dogmaattributes'])
        units = dogmaUnitsLoader.load(file_paths['dogmaunits'])
        
        print(f"✓ Loaded typedogma: {len(typedogma)} entries")
        print(f"✓ Loaded attributes: {len(attrs)} definitions")
        print(f"✓ Loaded units: {len(units)} definitions")
        
        # Load localization
        with open(file_paths['localization'], 'rb') as f:
            localization = pickle.load(f)
        loc_dict = localization[1]
        
        def get_loc(label_id):
            if label_id and label_id in loc_dict:
                val = loc_dict[label_id]
                if isinstance(val, tuple) and len(val) > 0:
                    return val[0]
            return ''
        
        # Build attribute info
        unit_map = {}
        for uid, u in units.items():
            display = get_loc(u.displayNameID) if hasattr(u, 'displayNameID') else ''
            if not display and hasattr(u, 'name'):
                display = u.name
            unit_map[uid] = display
        
        attr_info = {}
        for attr_id, attr in attrs.items():
            unit_name = unit_map.get(attr.unitID, '') if hasattr(attr, 'unitID') else ''
            display = get_loc(attr.displayNameID) if hasattr(attr, 'displayNameID') else ''
            if not display:
                display = attr.name
            attr_info[attr_id] = {'name': attr.name, 'displayName': display, 'unit': unit_name}
        
        # Load frontier types
        with open(types_file, 'r', encoding='utf-8') as f:
            frontier_types = json.load(f)
        
        # Find ships (types with hiSlots, medSlots, lowSlots)
        ship_type_ids = []
        for tid, data in frontier_types.items():
            if int(tid) in typedogma:
                dogma = typedogma[int(tid)]
                attr_ids = {a.attributeID for a in dogma.dogmaAttributes}
                if 12 in attr_ids and 13 in attr_ids and 14 in attr_ids:
                    ship_type_ids.append(tid)
        
        print(f"✓ Found {len(ship_type_ids)} ships")
        
        # Group names
        group_names = {
            25: 'Frigate', 26: 'Cruiser', 31: 'Shuttle',
            237: 'Corvette', 419: 'Industrial', 420: 'Destroyer'
        }
        
        # Build ship data
        ships = {}
        for tid in ship_type_ids:
            type_data = frontier_types[tid]
            dogma = typedogma[int(tid)]
            
            ship = {
                'typeID': int(tid),
                'typeName': type_data.get('typeName', ''),
                'groupID': type_data.get('groupID'),
                'groupName': group_names.get(type_data.get('groupID'), 'Unknown'),
                'mass': type_data.get('mass'),
                'volume': type_data.get('volume'),
                'basePrice': type_data.get('basePrice'),
            }
            
            # All dogma attributes
            ship['dogmaAttributes'] = {}
            for attr in dogma.dogmaAttributes:
                info = attr_info.get(attr.attributeID, {})
                ship['dogmaAttributes'][info.get('name', f'attr_{attr.attributeID}')] = {
                    'attributeID': attr.attributeID,
                    'value': attr.value,
                    'displayName': info.get('displayName', ''),
                    'unit': info.get('unit', '')
                }
            
            # Quick access stats
            ship['stats'] = {
                'highSlots': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 14), 0),
                'medSlots': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 13), 0),
                'lowSlots': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 12), 0),
                'turretHardpoints': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 102), 0),
                'launcherHardpoints': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 101), 0),
                'engineSlots': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 5652), 0),
                'powerOutput': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 11), 0),
                'cpuOutput': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 48), 0),
                'structureHP': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 9), 0),
                'armorHP': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 265), 0),
                'shieldCapacity': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 263), 0),
                'maxVelocity': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 37), 0),
                'warpSpeed': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 600), 0),
                'fuelCapacity': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 5633), 0),
                'capacitorCapacity': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 482), 0),
                'maxTargetRange': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 76), 0),
                'signatureRadius': next((a.value for a in dogma.dogmaAttributes if a.attributeID == 552), 0),
            }
            
            ships[tid] = ship
        
        # Save ships.json
        ships_file = output_dir / "ships.json"
        with open(ships_file, 'w', encoding='utf-8') as f:
            json.dump(ships, f, indent=2, ensure_ascii=False)
        
        file_size = ships_file.stat().st_size
        print(f"✓ Saved {len(ships)} ships to ships.json ({file_size / 1024:.1f} KB)")
        
        # Print summary
        print(f"\n=== Frontier Ships ===")
        for tid, ship in sorted(ships.items(), key=lambda x: (x[1]['groupName'], x[1]['typeName'])):
            s = ship['stats']
            print(f"  {ship['typeName']} ({ship['groupName']}): {int(s['highSlots'])}H/{int(s['medSlots'])}M/{int(s['lowSlots'])}L")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error extracting ships: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


def extract_all_dogma(game_path, output_folder):
    """Extract dogma attributes for ALL frontier types (modules, ammo, fuel, etc.)"""
    game_path = Path(game_path)
    output_dir = Path(output_folder).absolute()  # Use absolute path since we chdir later
    
    print("="*70)
    print("EXTRACTING ALL DOGMA DATA")
    print("="*70)
    
    # Get paths from resfileindex
    index_data = parse_resfileindex(game_path)
    resfiles_dir = game_path.parent / "ResFiles"
    bin64_dir = game_path / "bin64"
    
    # Check for loaders
    loaders = ['typeDogmaLoader.pyd', 'dogmaAttributesLoader.pyd', 'dogmaUnitsLoader.pyd']
    for loader in loaders:
        if not (bin64_dir / loader).exists():
            print(f"[FAIL] Missing loader: {loader}")
            return False
    print(f"[OK] Found all required loaders in {bin64_dir}")
    
    # Find dogma files
    dogma_files = {
        'typedogma': 'res:/staticdata/typedogma.fsdbinary',
        'dogmaattributes': 'res:/staticdata/dogmaattributes.fsdbinary',
        'dogmaunits': 'res:/staticdata/dogmaunits.fsdbinary',
        'localization': 'res:/localizationfsd/localization_fsd_en-us.pickle'
    }
    
    file_paths = {}
    for name, res_path in dogma_files.items():
        if res_path not in index_data:
            print(f"[FAIL] {name} not found in index")
            return False
        entry = index_data[res_path]
        file_path = resfiles_dir / entry['hash_path']
        if not file_path.exists():
            print(f"[FAIL] ResFile not found: {file_path}")
            return False
        file_paths[name] = str(file_path)
        print(f"[OK] Found {name}: {entry['hash_path'][:40]}...")
    
    # Need types_frontier.json
    types_file = output_dir / "types_frontier.json"
    if not types_file.exists():
        print(f"\n[WARN] types_frontier.json not found - extracting types first...")
        if not extract_types(str(game_path), str(output_dir)):
            return False
        if not (output_dir / "blueprints.json").exists():
            extract_blueprints(str(game_path), str(output_dir))
        create_types_frontier(str(output_dir))
    
    # Load frontier types BEFORE changing directory
    with open(types_file, 'r', encoding='utf-8') as f:
        frontier_types = json.load(f)
    print(f"[OK] Loaded {len(frontier_types)} frontier types")
    
    print(f"\nLoading dogma data...")
    
    original_cwd = os.getcwd()
    original_path = sys.path.copy()
    
    try:
        os.chdir(str(bin64_dir))
        sys.path.insert(0, str(bin64_dir))
        
        import typeDogmaLoader
        import dogmaAttributesLoader
        import dogmaUnitsLoader
        import pickle
        
        typedogma = typeDogmaLoader.load(file_paths['typedogma'])
        attrs = dogmaAttributesLoader.load(file_paths['dogmaattributes'])
        units = dogmaUnitsLoader.load(file_paths['dogmaunits'])
        
        print(f"[OK] Loaded typedogma: {len(typedogma)} entries")
        print(f"[OK] Loaded attributes: {len(attrs)} definitions")
        print(f"[OK] Loaded units: {len(units)} definitions")
        
        # Load localization
        with open(file_paths['localization'], 'rb') as f:
            localization = pickle.load(f)
        loc_dict = localization[1]
        
        def get_loc(label_id):
            if label_id and label_id in loc_dict:
                val = loc_dict[label_id]
                if isinstance(val, tuple) and len(val) > 0:
                    return val[0]
            return ''
        
        # Build attribute info
        unit_map = {}
        for uid, u in units.items():
            display = get_loc(u.displayNameID) if hasattr(u, 'displayNameID') else ''
            if not display and hasattr(u, 'name'):
                display = u.name
            unit_map[uid] = display
        
        attr_info = {}
        for attr_id, attr in attrs.items():
            unit_name = unit_map.get(attr.unitID, '') if hasattr(attr, 'unitID') else ''
            display = get_loc(attr.displayNameID) if hasattr(attr, 'displayNameID') else ''
            if not display:
                display = attr.name
            attr_info[attr_id] = {'name': attr.name, 'displayName': display, 'unit': unit_name}
        
        # Build dogma data for all frontier types that have dogma
        all_dogma = {}
        for tid_str, type_data in frontier_types.items():
            tid = int(tid_str)
            if tid in typedogma:
                dogma = typedogma[tid]
                dogma_attrs = {}
                for attr in dogma.dogmaAttributes:
                    info = attr_info.get(attr.attributeID, {})
                    dogma_attrs[info.get('name', f'attr_{attr.attributeID}')] = {
                        'attributeID': attr.attributeID,
                        'value': attr.value,
                        'displayName': info.get('displayName', ''),
                        'unit': info.get('unit', '')
                    }
                if dogma_attrs:
                    all_dogma[tid_str] = dogma_attrs
        
        # Save all_dogma.json
        dogma_file = output_dir / "all_dogma.json"
        with open(dogma_file, 'w', encoding='utf-8') as f:
            json.dump(all_dogma, f, indent=2, ensure_ascii=False)
        
        file_size = dogma_file.stat().st_size
        print(f"[OK] Saved dogma for {len(all_dogma)} types to all_dogma.json ({file_size / 1024:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error extracting dogma: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_cwd)
        sys.path = original_path


def create_types_frontier(output_folder):
    """Create types_frontier.json from types.json filtered by blueprints"""
    output_dir = Path(output_folder)
    
    blueprints_file = output_dir / "blueprints.json"
    types_file = output_dir / "types.json"
    
    if not blueprints_file.exists() or not types_file.exists():
        print(f"✗ Need both blueprints.json and types.json to create types_frontier.json")
        return False
    
    # Load blueprints
    with open(blueprints_file, 'r', encoding='utf-8') as f:
        blueprints = json.load(f)
    
    # Get all type IDs from blueprints
    blueprint_type_ids = set()
    for entry in blueprints['cache']:
        bp_json = json.loads(entry['value'])
        if 'blueprintTypeID' in bp_json:
            blueprint_type_ids.add(bp_json['blueprintTypeID'])
        if 'activities' in bp_json:
            for activity_name, activity in bp_json['activities'].items():
                if 'products' in activity:
                    for prod in activity['products']:
                        blueprint_type_ids.add(prod['typeID'])
                if 'materials' in activity:
                    for mat in activity['materials']:
                        blueprint_type_ids.add(mat['typeID'])
    
    # Load all types
    with open(types_file, 'r', encoding='utf-8') as f:
        all_types = json.load(f)
    
    # Filter to frontier types
    frontier_types = {}
    for tid in blueprint_type_ids:
        tid_str = str(tid)
        if tid_str in all_types:
            frontier_types[tid_str] = all_types[tid_str]
    
    # Save
    output_file = output_dir / "types_frontier.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(frontier_types, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created types_frontier.json with {len(frontier_types)} types")
    return True

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
    
    # Extract MD5 hash from hash_path for version tracking
    hash_parts = entry['hash_path'].split('_')
    data_hash = hash_parts[-1] if len(hash_parts) > 1 else "unknown"
    
    print(f"✓ Found in index:")
    print(f"  Data version: {data_hash[:8]}...")  # Show first 8 chars of hash
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
            
            # Load localization for type names
            print(f"\nLoading type names from localization...")
            loc_key = "res:/localizationfsd/localization_fsd_en-us.pickle"
            if loc_key in index_data:
                loc_entry = index_data[loc_key]
                loc_path = game_path.parent / "ResFiles" / loc_entry['hash_path']
                
                if loc_path.exists():
                    import pickle
                    with open(loc_path, 'rb') as lf:
                        lang, loc_data = pickle.load(lf)
                    
                    # Add type names
                    names_found = 0
                    for type_id, type_data in data_dict.items():
                        name_id = type_data.get('typeNameID')
                        if name_id and name_id in loc_data:
                            loc_entry = loc_data[name_id]
                            if isinstance(loc_entry, tuple):
                                type_data['typeName'] = loc_entry[0]
                            else:
                                type_data['typeName'] = str(loc_entry)
                            names_found += 1
                        else:
                            type_data['typeName'] = None
                    
                    print(f"✓ Added names for {names_found:,} types")
                else:
                    print(f"⚠ Localization file not found, skipping type names")
            else:
                print(f"⚠ Localization not in index, skipping type names")
            
            # Save to JSON
            output_file = output_dir / "types.json"
            print(f"\nSaving to: {output_file}")
            
            # Use indent=2 for readable formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            
            file_size = output_file.stat().st_size
            print(f"✓ Saved! Size: {file_size / (1024*1024):.1f} MB")
            print(f"✓ Total types: {len(data_dict):,}")
            
            # Show sample with name
            if data_dict:
                # Find a type with a name for better sample
                sample_id = None
                for tid in ['34', '35', '100', '1000']:
                    if tid in data_dict and data_dict[tid].get('typeName'):
                        sample_id = tid
                        break
                if not sample_id:
                    sample_id = next(iter(data_dict))
                
                sample = data_dict[sample_id]
                print(f"\nSample type (ID {sample_id}): {sample.get('typeName', 'Unknown')}")
                for key, value in list(sample.items())[:11]:
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
  
  # Extract types, blueprints, and ships
  python extract.py --types --blueprints --ships
  
  # Extract everything
  python extract.py --all
  
  # Custom paths
  python extract.py --types --game-path "C:\\CCP\\EVE Frontier\\stillness" --output "./data"
  
  # Help
  python extract.py --help

Note: 
  - All extraction requires Python 3.12 (for .pyd loaders)
  - Hashes are read dynamically from resfileindex.txt (handles game updates automatically)
  - Solar systems extraction currently only supported via GUI
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
                       help='Extract solar system data (GUI only)')
    parser.add_argument('--blueprints', '-b',
                       action='store_true',
                       help='Extract blueprints data')
    parser.add_argument('--types', '-t',
                       action='store_true',
                       help='Extract types data (requires Python 3.12)')
    parser.add_argument('--ships',
                       action='store_true',
                       help='Extract ships with full dogma attributes')
    parser.add_argument('--dogma',
                       action='store_true',
                       help='Extract dogma attributes for all frontier types')
    parser.add_argument('--frontier-only', '-f',
                       action='store_true',
                       help='Create types_frontier.json (types used in blueprints only)')
    
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
    
    # Show index info (to confirm dynamic hash reading)
    index_data = parse_resfileindex(game_path)
    print(f"✓ Loaded resfileindex.txt: {len(index_data)} entries")
    print("  (Hashes are read dynamically - extraction handles game updates)")
    print()
    
    # Determine what to extract
    extract_solar = args.all or args.solar_systems
    extract_bp = args.all or args.blueprints
    extract_types_data = args.all or args.types
    extract_ships_data = args.all or args.ships
    extract_dogma_data = args.all or args.dogma
    extract_frontier = args.all or args.frontier_only
    
    # If nothing specified, show help
    if not (extract_solar or extract_bp or extract_types_data or extract_ships_data or extract_dogma_data or extract_frontier):
        parser.print_help()
        print("\nNo extraction options specified. Use --all or specific options.")
        sys.exit(0)
    
    success_count = 0
    
    # Extract solar systems (GUI only warning)
    if extract_solar:
        try:
            extract_solarsystem_and_blueprints(game_path, output_folder)
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Extract blueprints
    if extract_bp:
        print()
        try:
            if extract_blueprints(game_path, output_folder):
                success_count += 1
        except Exception as e:
            print(f"✗ Error extracting blueprints: {e}")
            import traceback
            traceback.print_exc()
    
    # Extract types
    if extract_types_data:
        print()
        if extract_types(game_path, output_folder):
            success_count += 1
    
    # Create types_frontier
    if extract_frontier:
        print()
        # Need blueprints and types first
        bp_file = Path(output_folder) / "blueprints.json"
        types_file = Path(output_folder) / "types.json"
        
        if not bp_file.exists():
            print("Extracting blueprints first for frontier types...")
            extract_blueprints(game_path, output_folder)
        if not types_file.exists():
            print("Extracting types first for frontier types...")
            extract_types(game_path, output_folder)
        
        if create_types_frontier(output_folder):
            success_count += 1
    
    # Extract ships
    if extract_ships_data:
        print()
        try:
            if extract_ships(game_path, output_folder):
                success_count += 1
        except Exception as e:
            print(f"[FAIL] Error extracting ships: {e}")
            import traceback
            traceback.print_exc()
    
    # Extract all dogma
    if extract_dogma_data:
        print()
        try:
            if extract_all_dogma(game_path, output_folder):
                success_count += 1
        except Exception as e:
            print(f"[FAIL] Error extracting dogma: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*70)
    print("EXTRACTION COMPLETE")
    print("="*70)
    print(f"Output folder: {output_folder}")
    
    # List extracted files
    output_path = Path(output_folder)
    json_files = list(output_path.glob("*.json"))
    if json_files:
        print(f"\nExtracted files:")
        for f in sorted(json_files):
            size = f.stat().st_size
            if size > 1024*1024:
                size_str = f"{size / (1024*1024):.1f} MB"
            else:
                size_str = f"{size / 1024:.1f} KB"
            print(f"  {f.name}: {size_str}")
    
    if success_count > 0:
        print("\n✓ Extraction successful!")
    else:
        print("\n✗ No data was extracted")
        sys.exit(1)

if __name__ == "__main__":
    main()
