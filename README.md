# EVE Frontier Data Extractor

Extract game data from EVE Frontier using a cross-platform GUI or command-line interface.

## Features

✅ **Multiple data types** - Solar systems (24,426) and blueprints (263)  
✅ **Cross-platform GUI** - Works on Windows, macOS, and Linux  
✅ **Command-line tool** - For automation and scripting  
✅ **Automatic extraction** - No manual file handling  
✅ **Clean output** - JSON format with auto-cleanup  

## Quick Start

### GUI (Recommended)

1. **Install Python 3.12**:
   ```bash
   # Download from python.org
   python3.12 -m pip install pyyaml
   ```

2. **Run the GUI**:
   ```bash
   python gui.py
   ```

3. **Select options**:
   - Browse to `code.ccp` file (in `EVE Frontier/stillness/`)
   - Choose output folder
   - Check which data types to extract
   - Click "Extract Selected Data"

### Command Line

```bash
# Use default paths
python extract_cli.py

# Custom paths
python extract_cli.py --code-ccp "/path/to/code.ccp" --output-folder "./output"

# Help
python extract_cli.py --help
```

## Requirements

- **Python 3.12+** (required for FSD parsing)
- **PyYAML** - Install with: `python3.12 -m pip install pyyaml`

## Default Installation Paths

- **Windows**: `C:\CCP\EVE Frontier\stillness\code.ccp`
- **macOS**: `~/Library/Application Support/CCP/EVE Frontier/stillness/code.ccp`
- **Linux**: `~/.local/share/CCP/EVE Frontier/stillness/code.ccp`

## Extracted Data

### Solar Systems (`solarsystemcontent.json` - 389 MB)
- **24,426 systems** with coordinates, planets, stargates, security status
- **83,356 planets** with moons, stations, lagrange points
- **Star properties**: spectral class, luminosity, age, frost line

### Blueprints (`blueprints.json` - 115 KB)
- **263 blueprints** with manufacturing recipes
- Materials required and products created
- Production time and limits

## How It Works

1. Reads `resfileindex.txt` to locate data files
2. Extracts `.static` files from ResFiles hash storage
3. Loads Python modules from `code.ccp` (10,472 files)
4. Parses FSD binary format using game's official loaders
5. Converts to JSON and cleans up temporary files

## Troubleshooting

**macOS GUI issues**
- Use command line instead: `python extract_cli.py`
- Or install Python via Homebrew: `brew install python@3.12 python-tk@3.12`

**Python 3.12 not found**
- Install from [python.org](https://www.python.org/downloads/)
- Verify: `python3.12 --version`

**Files not found**
- Ensure EVE Frontier is installed and `code.ccp` path is correct

---

**Community tool** - Not affiliated with CCP Games  
**Repository**: [github.com/TwistedSD/FrontierData](https://github.com/TwistedSD/FrontierData)
