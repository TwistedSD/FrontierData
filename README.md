# EVE Frontier Solar System Data Extractor

Extract solar system data from EVE Frontier game files using a simple cross-platform GUI or command-line interface.

## Features

✅ **Cross-platform GUI** - Works on Windows, macOS, and Linux  
✅ **Automatic extraction** - No manual file handling required  
✅ **Complete data** - All 24,426 solar systems with full details  
✅ **Progress tracking** - Real-time log and progress bar  
✅ **Clean output** - Auto-cleanup of temporary files  

## Quick Start

### Using the GUI (Recommended)

1. **Install Python 3.12**:
   - Download from [python.org](https://www.python.org/downloads/)
   - Install PyYAML: `python3.12 -m pip install pyyaml`

2. **Run the GUI**:
   ```bash
   python gui.py
   ```

3. **Select paths**:
   - **EVE Frontier Folder**: Point to your game installation (e.g., `C:\CCP\EVE Frontier`)
   - **Output Folder**: Choose where to save the extracted data

4. **Click "Extract Solar System Data"** and wait for completion!

### Using Command Line

```bash
python extract_solarsystem_data.py
```

The script will use default paths and extract to `extracted_data/solarsystemcontent.json`.

## Requirements

- **Python 3.12** (required for parsing game data)
- **Python 3.13+** (or any version for running the GUI/CLI)
- **PyYAML** (for Python 3.12: `python3.12 -m pip install pyyaml`)
- **tkinter** (built-in with Python - used for GUI)

## Installation Paths

The tool auto-detects game installation paths:

- **Windows**: `C:\CCP\EVE Frontier`
- **macOS**: `~/Library/Application Support/CCP/EVE Frontier`
- **Linux**: `~/.local/share/CCP/EVE Frontier`

## Extracted Data

**Output**: `solarsystemcontent.json` (~389 MB)  
**Systems**: 24,426 solar systems

Each system includes:
- **Coordinates**: 3D position (x, y, z)
- **Planets**: Full details with moons, stations, lagrange points
- **Stargates**: Network connections (3,163 connected systems)
- **Security**: Status (0.0 or -0.99) and class (D1 or empty)
- **Star Properties**: Type, spectral class (O/B/A/F/G/K/M), luminosity, age
- **Orbital Data**: Frost line, habitable zone, radius

### Interesting Statistics

- **83,356 planets** across 98% of systems
- **61 spectral classes** from O0 (hottest) to M9 (coolest)
- **50.8% M-class red dwarfs** (realistic distribution!)
- **Only 13% of systems have stargates** (87% isolated)
- **400 dangerous systems** with -0.99 security and zero luminosity

## Project Structure

```
FrontierData/
├── gui.py                      # GUI application (cross-platform)
├── extract_solarsystem_data.py # Main extraction orchestrator
├── extract_game_data.py        # Extracts .static from game files
├── load_fsd_py312.py          # Python 3.12 FSD parser
└── extracted_data/
    └── solarsystemcontent.json # Output file
```

## How It Works

1. **Locate game files**: Reads `resfileindex.txt` to find `solarsystemcontent.static`
2. **Extract binary**: Pulls 68.6 MB binary file from ResFiles hash storage
3. **Load game modules**: Extracts 10,472 Python modules from `code.ccp`
4. **Parse FSD data**: Uses game's official loaders (Python 3.12 required)
5. **Convert to JSON**: Transforms FSD structures to standard JSON
6. **Cleanup**: Removes all temporary files

## Technical Details

- **FSD Format**: 4-byte header + pickled schema + binary data
- **Loaders**: MultiIndexLoader, DictLoader, IndexLoader, ObjectLoader, VectorLoader
- **Python 3.12 Requirement**: Game modules compiled for Python 3.12 bytecode
- **Subprocess Architecture**: Isolates Python 3.12 parsing from main app

## Troubleshooting

**GUI won't start on macOS (Tk version error)**
- Some older macOS Python installations have incompatible Tk versions
- **Solution 1**: Use the command-line version instead:
  ```bash
  python extract_solarsystem_data.py
  ```
- **Solution 2**: Install Python via Homebrew (recommended):
  ```bash
  brew install python@3.12 python-tk@3.12
  ```
- **Solution 3**: Download the latest Python from python.org

**"Python 3.12 NOT FOUND"**
- Install Python 3.12 from python.org
- Verify installation: `python3.12 --version`

**"Cannot find stillness folder"**
- Make sure you select the main EVE Frontier folder, not a subfolder
- The tool automatically looks for `stillness` inside

**"Cannot find resfileindex.txt"**
- Verify EVE Frontier is fully installed
- Try repairing/reinstalling the game

## Future Enhancements

Planned features for future releases:
- Extract other game data types (blueprints, items, etc.)
- Filter and query specific systems
- Export to CSV/SQL formats
- Data visualization tools

## License

This is a community tool for EVE Frontier data extraction. Not affiliated with CCP Games.

---

**Created**: November 2025  
**Game Version**: EVE Frontier (Stillness server)  
**Repository**: [github.com/TwistedSD/FrontierData](https://github.com/TwistedSD/FrontierData)
