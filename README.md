# EVE Frontier Solar System Data Extractor

Custom tool to extract solar system data from EVE Frontier game files using the game's official FSD (Fast Serialized Data) loaders.

## Requirements

- **Python 3.12** (required for FSD binary parsing)
- **Python 3.13** (or any version for running the main script)
- **PyYAML** (installed for Python 3.12)
- **EVE Frontier** installed at `C:\CCP\EVE Frontier\`

## Installation

1. Install Python 3.12 from [python.org](https://www.python.org/downloads/)
2. Install PyYAML for Python 3.12:
   ```powershell
   python3.12 -m pip install pyyaml
   ```

## Usage

Simply run the main extraction script:

```powershell
python extract_solarsystem_data.py
```

This will:
1. Auto-detect your Python 3.12 installation
2. Extract `solarsystemcontent.static` from game files
3. Parse the binary data using game's FSD loaders
4. Output JSON to `extracted_data/solarsystemcontent.json`

## Output

The extracted JSON contains **24,426 solar systems** with complete data:

- **Coordinates**: 3D position (x, y, z) for each system
- **Planets**: Full planet data including moons, stations, lagrange points
- **Stargates**: Stargate connections between systems
- **Security**: Security status and classification
- **Star Data**: Sun type, luminosity, frost line, habitable zone
- **Statistics**: Border, corridor, fringe, hub, international flags

**File size**: ~389 MB JSON

## Files

- **`extract_solarsystem_data.py`** - Main script (run this)
- **`extract_game_data.py`** - Stage 1: Extracts .static from ResFiles
- **`load_fsd_py312.py`** - Stage 2: Parses FSD binary (Python 3.12 worker)

## How It Works

1. Reads `resfileindex.txt` to locate `solarsystemcontent.static`
2. Extracts raw binary file (68.6 MB) from ResFiles hash storage
3. Extracts game's Python modules from `code.ccp` archive
4. Uses game's official FSD loaders to parse binary format
5. Converts FSD structures (DictLoader, VectorLoader, etc.) to JSON

## Technical Details

- **FSD Format**: 4-byte header + pickled schema + binary data
- **Loaders Used**: MultiIndexLoader, DictLoader, IndexLoader, ObjectLoader, VectorLoader
- **Python 3.12 Required**: Game modules compiled for Python 3.12 bytecode
- **Subprocess Isolation**: Uses subprocess to call Python 3.12 separately

## Extracting Other Game Data

To extract other .static files, modify the search term in `extract_game_data.py`:

```python
# Change this line:
target_resource = "res:/staticdata/solarsystemcontent.static"

# To extract different data:
target_resource = "res:/staticdata/typedata.static"  # Item types
target_resource = "res:/staticdata/blueprints.static"  # Blueprints
# etc.
```

Then run `extract_solarsystem_data.py` as normal.
