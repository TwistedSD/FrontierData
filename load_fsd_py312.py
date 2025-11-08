"""
Python 3.12 wrapper to load FSD data using EVE Frontier's binaryLoader
This script should be run with Python 3.12!
"""

import sys
import os
import json
import zipfile

# Configuration
CODE_CCP_ZIP = sys.argv[1]  # Path to code.ccp
STATIC_FILE = sys.argv[2]   # Path to .static file
OUTPUT_FILE = sys.argv[3]   # Output JSON file

# Extract code.ccp
extract_dir = "temp_code_ccp_py312"
if not os.path.exists(extract_dir):
    os.makedirs(extract_dir)
    print("Extracting code.ccp (this may take a minute)...")
    with zipfile.ZipFile(CODE_CCP_ZIP, 'r') as zf:
        # Extract ALL .pyc files - they may have interdependencies
        pyc_files = [f for f in zf.namelist() if f.endswith('.pyc')]
        for i, f in enumerate(pyc_files):
            if i % 1000 == 0:
                print(f"  Extracted {i}/{len(pyc_files)} files...")
            zf.extract(f, extract_dir)
        print(f"  OK Extracted {len(pyc_files)} Python modules")
else:
    print("Using existing extracted code.ccp")

sys.path.insert(0, extract_dir)

# Import FSD loaders
import fsd.schemas.binaryLoader as binLoader
import fsd.schemas.loaders.dictLoader as dictLoader
import fsd.schemas.loaders.objectLoader as objectLoader
import fsd.schemas.loaders as miscLoaders

# Load the data
print(f"Loading: {STATIC_FILE}")
fsd_data = binLoader.LoadFSDDataInPython(STATIC_FILE, None, False, None)

print(f"Type: {type(fsd_data).__name__}")

# Convert to JSON-serializable format
def convert_to_dict(obj):
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    elif isinstance(obj, dict):
        return {str(k): convert_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_dict(item) for item in obj]
    elif type(obj).__name__ == 'VectorLoader':
        # Vector (x, y, z coordinates)
        return {name: float(obj.data[idx]) for name, idx in obj.schema['aliases'].items()}
    elif type(obj).__name__ in ('DictLoader', 'IndexLoader', 'MultiIndexLoader'):
        # Dictionary-like objects
        return {str(k): convert_to_dict(v) for k, v in obj.items()}
    elif type(obj).__name__ == 'ObjectLoader':
        # Object with attributes
        result = {}
        for attr in dir(obj):
            if not attr.startswith('__'):
                try:
                    result[attr] = convert_to_dict(getattr(obj, attr))
                except:
                    pass
        return result
    else:
        return str(obj)

print("Converting to JSON...")
result = convert_to_dict(fsd_data)

print(f"Writing to: {OUTPUT_FILE}")
with open(OUTPUT_FILE, 'w') as f:
    json.dump(result, f, indent=2)

print(f"OK Done! Extracted {len(result)} entries")
