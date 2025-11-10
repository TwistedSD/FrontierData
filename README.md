# EVE Frontier Data Extractor

Extract game data from EVE Frontier using a GUI or command-line interface.

## Features

✅ **Three data types** - Solar systems (24,426), blueprints (263), and types (32,159)  
✅ **Cross-platform GUI** - Works on Windows, macOS, and Linux  
✅ **Command-line tool** - For automation and scripting  
✅ **Automatic extraction** - No manual file handling  
✅ **Clean output** - Formatted JSON with auto-cleanup

## Quick Start

### GUI (Recommended)

1. **Install Python 3.12+**:
   ```bash
   # Download from python.org
   ```

2. **Run the GUI**:
   ```bash
   python gui.py
   ```

3. **Extract data**:
   - Browse to `code.ccp` file (in `EVE Frontier/stillness/`)
   - Choose output folder
   - Select which data types to extract (all selected by default)
   - Click "Extract Selected Data"

### Command Line

```bash
# Extract types data
python extract.py --types

# Custom paths
python extract.py --types --game-path "C:\CCP\EVE Frontier\stillness" --output "./output"

# Help
python extract.py --help
```

## Requirements

- **Python 3.12+** (required for parsing EVE Frontier's binary data)
- No additional dependencies needed

## Default Installation Paths

- **Windows**: `C:\CCP\EVE Frontier\stillness\code.ccp`
- **macOS**: `~/Library/Application Support/CCP/EVE Frontier/stillness/code.ccp`
- **Linux**: `~/.local/share/CCP/EVE Frontier/stillness/code.ccp`

## Extracted Data

### Solar Systems (`solarsystemcontent.json` - 389 MB)
- **24,426 systems** with coordinates, planets, stargates, security status
- **83,356 planets** with moons, stations, lagrange points
- Star properties: spectral class, luminosity, age, frost line

### Blueprints (`blueprints.json` - 115 KB)
- **263 blueprints** with manufacturing recipes
- Materials required and products created
- Production time and limits

### Types (`types.json` - 10 MB)
- **32,159 item types** with properties
- Base price, capacity, mass, volume, radius
- Group ID, platform availability, published status

## How It Works

1. Reads `resfileindex.txt` to locate data files in ResFiles hash storage
2. Extracts binary data (`.static`, `.fsdbinary`) from ResFiles
3. Uses EVE Frontier's native loaders (`typesLoader.pyd`, `code.ccp`)
4. Converts to formatted JSON and cleans up temporary files

## Troubleshooting

**Python 3.12 not found**
- Install from [python.org](https://www.python.org/downloads/)
- Verify: `python --version` or `python3.12 --version`
- The GUI will automatically find Python 3.12

**Files not found**
- Ensure EVE Frontier is installed
- Verify `code.ccp` path is correct (in `stillness` folder)
- Check that `resfileindex.txt` exists in the same directory

**Extraction fails**
- Close EVE Frontier client if running
- Try running as administrator (Windows)
- Check available disk space (solar systems = 389 MB)

---

**Community tool** - Not affiliated with CCP Games  
**Repository**: [github.com/TwistedSD/FrontierData](https://github.com/TwistedSD/FrontierData)
