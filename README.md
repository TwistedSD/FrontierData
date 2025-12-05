# EVE Frontier Data Extractor

Extract game data from EVE Frontier using a GUI or command-line interface.

## Features

- **7 extraction options** - Galaxy, Ships, Modules, Blueprints, Ammo, Fuel, Materials
- **Full dogma attributes** - Stats for ships, modules, ammo (damage, CPU, power, etc.)
- **Clean focused exports** - Each file contains only its specific category
- **Cross-platform GUI** - Works on Windows, macOS, and Linux
- **Command-line tool** - For automation and scripting
- **Dynamic hash reading** - Automatically handles game updates (reads from `resfileindex.txt`)

## Quick Start

### GUI (Recommended)

1. **Install Python 3.12+** (required for binary data extraction):
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
   - Select data types: Galaxy, Ships, Modules, Blueprints, Ammo, Fuel, Materials
   - Click "Extract Selected Data"

### Command Line

```bash
# Extract everything
python extract.py --all

# Extract specific data types
python extract.py --types --blueprints --ships

# Extract dogma for all frontier types
python extract.py --dogma

# Custom paths
python extract.py --types --game-path "C:\CCP\EVE Frontier\stillness" --output "./output"

# Create types_frontier.json (only types used in blueprints)
python extract.py --frontier-only

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

### Galaxy (`Galaxy.json` - ~389 MB)
- **24,426 solar systems** with coordinates, planets, stargates, security status
- **83,356 planets** with moons, stations, lagrange points
- Star properties: spectral class, luminosity, age, frost line

### Ships (`Ships.json` - ~128 KB)
- **14 ships** with full dogma attributes
- **54 stats** per ship: slots (H/M/L/E), hardpoints, power, CPU, HP, velocity, warp speed
- Ships: TADES, Forlorn, Skiff, Foreman, Marshal, Echon, Rover, Carrier, Barge, Lurcher, Dreamer, Epoch, Carom, Stride

### Modules (`Modules.json` - ~195 KB)
- **142 modules** with dogma attributes
- Weapons, shields, armor, propulsion, mining equipment
- Stats: CPU, power grid, damage, bonuses

### Blueprints (`Blueprints.json` - ~130 KB)
- **265 blueprints** with manufacturing recipes
- Materials required and products created
- Production time and limits

### Ammo (`Ammo.json` - ~36 KB)
- **23 ammo types** with damage stats
- EM, explosive, kinetic, thermal damage values

### Fuel (`Fuel.json` - ~6 KB)
- **10 fuel types** for ships and stations

### Materials (`Materials.json` - ~59 KB)
- **157 materials** - ores, components, resources

## How It Works

1. **Dynamically reads `resfileindex.txt`** to locate data files in ResFiles hash storage
2. Extracts binary data (`.static`, `.fsdbinary`) from ResFiles  
3. Uses EVE Frontier's native loaders (`typesLoader.pyd`, `typeDogmaLoader.pyd`, `code.ccp`)
4. Converts to formatted JSON with dogma attributes
5. Cleans up temporary files

**Game Updates:** When EVE Frontier patches, file hashes change. The extractor automatically handles this by reading fresh hashes from `resfileindex.txt` on every run - no code changes needed!

## Selective Extraction (Advanced)

Use `extract_selective.py` for category-based exports with dogma data:

```bash
# Export specific categories
python extract_selective.py --category ships --output Ships.json
python extract_selective.py --category modules --output Modules.json
python extract_selective.py --category ammo --output Ammo.json
python extract_selective.py --category fuel --output Fuel.json
python extract_selective.py --category materials --output Materials.json
python extract_selective.py --category blueprints --output Blueprints.json

# Search for types
python extract_selective.py --search "TADES"

# Show dependencies for a type
python extract_selective.py --deps 81808

# Interactive mode
python extract_selective.py --interactive
```

### Categories

| Category | Count | Description |
|----------|-------|-------------|
| `ships` | 14 | All flyable ships with full dogma stats |
| `modules` | 142 | Weapons, shields, armor, propulsion, mining |
| `ammo` | 23 | Charges and ammunition with damage stats |
| `fuel` | 10 | Ship and station fuel types |
| `materials` | 157 | Raw and processed materials |
| `blueprints` | 265 | All manufacturing recipes |

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
