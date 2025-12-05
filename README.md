# EVE Frontier Data Extractor

Extract game data from EVE Frontier using a GUI or command-line interface.

## Features

✅ **Five data types** - Solar systems, blueprints, types, ships with dogma, frontier types  
✅ **Cross-platform GUI** - Works on Windows, macOS, and Linux  
✅ **Command-line tool** - For automation and scripting  
✅ **Dynamic hash reading** - Automatically handles game updates (reads from `resfileindex.txt`)  
✅ **Full ship stats** - All 54 dogma attributes including slots, power, HP, resistances  
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
# Extract everything
python extract.py --all

# Extract specific data types
python extract.py --types --blueprints --ships

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

### Solar Systems (`solarsystemcontent.json` - 389 MB)
- **24,426 systems** with coordinates, planets, stargates, security status
- **83,356 planets** with moons, stations, lagrange points
- Star properties: spectral class, luminosity, age, frost line

### Blueprints (`blueprints.json` - ~150 KB)
- **265 blueprints** with manufacturing recipes
- Materials required and products created
- Production time and limits

### Types (`types.json` - 10 MB)
- **32,177 item types** with properties
- Base price, capacity, mass, volume, radius
- Group ID, platform availability, published status

### Types Frontier (`types_frontier.json` - 216 KB)
- **527 types** referenced in blueprints only
- Filtered subset of types used in EVE Frontier gameplay

### Ships (`ships.json` - 140 KB)
- **14 ships** with full dogma attributes
- **54 stats** per ship: slots (H/M/L/E), hardpoints, power, CPU, HP, velocity, warp speed
- Quick access stats + full dogma attribute data
- Ships: TADES, Forlorn, Skiff, Foreman, Marshal, Echon, Rover, Carrier, Barge, Lurcher, Dreamer, Epoch, Carom, Stride

## How It Works

1. **Dynamically reads `resfileindex.txt`** to locate data files in ResFiles hash storage
2. Extracts binary data (`.static`, `.fsdbinary`) from ResFiles  
3. Uses EVE Frontier's native loaders (`typesLoader.pyd`, `typeDogmaLoader.pyd`, `code.ccp`)
4. Converts to formatted JSON and cleans up temporary files

**Game Updates:** When EVE Frontier patches, file hashes change. The extractor automatically handles this by reading fresh hashes from `resfileindex.txt` on every run - no code changes needed!

## Selective Extraction with Dependencies

Use `extract_selective.py` to select specific types and automatically include their manufacturing dependencies:

```bash
# Search for types
python extract_selective.py --search "TADES"

# Show all dependencies for a type
python extract_selective.py --deps 81808

# Show full manufacturing chain
python extract_selective.py --chain 81808

# List types in a category
python extract_selective.py --list-category modules

# Export ships with all manufacturing dependencies
python extract_selective.py --category ships --output ships_full.json

# Export specific types with dependencies
python extract_selective.py --types 82094,82095 --output disintegrators.json

# Export without dependencies (just the types themselves)
python extract_selective.py --types 82094 --no-deps --output single.json

# Interactive mode
python extract_selective.py --interactive
```

### Categories

| Category | Description |
|----------|-------------|
| `ships` | All 14 flyable ships |
| `modules` | Weapons, shields, armor, propulsion, mining (~142 items) |
| `ammo` | Charges and ammunition |
| `components` | Craftable intermediate items |
| `materials` | Raw and processed materials |
| `ores` | Mineable ores and minerals |
| `fuel` | Ship fuel types |
| `blueprints` | All manufacturing blueprints |

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
