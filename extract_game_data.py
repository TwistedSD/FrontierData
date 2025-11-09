"""
EVE Frontier Game Data Extractor
Extracts data from game files using the resfileindex.txt
"""

import os
import struct
import json
from pathlib import Path

class GameDataExtractor:
    def __init__(self, game_path):
        """
        Initialize the extractor with the game installation path
        
        Args:
            game_path: Path to the game directory (e.g., C:\\CCP\\EVE Frontier\\stillness)
        """
        self.game_path = Path(game_path)
        self.index_file = self.game_path / "resfileindex.txt"
        self.index_data = {}
        
    def parse_index_file(self):
        """Parse the entire resfileindex.txt file"""
        print(f"Reading index file: {self.index_file}")
        
        if not self.index_file.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_file}")
        
        with open(self.index_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                parts = line.split(',')
                if len(parts) >= 5:
                    resource_path = parts[0]
                    self.index_data[resource_path] = {
                        'resource_path': resource_path,
                        'hash_path': parts[1],
                        'file_hash': parts[2],
                        'offset': int(parts[3]),
                        'size': int(parts[4]),
                        'line_number': line_num
                    }
        
        print(f"Parsed {len(self.index_data)} entries from index file")
        return self.index_data
    
    def find_entry(self, search_term):
        """Find entries matching a search term"""
        matches = []
        for key, value in self.index_data.items():
            if search_term.lower() in key.lower():
                matches.append(value)
        return matches
    
    def locate_data_file(self, entry):
        """
        Locate the actual data file using the hash information
        The index file points to ResFiles directory with hash-based structure
        """
        hash_path = entry['hash_path']
        file_hash = entry['file_hash']
        
        # Primary location: ResFiles directory with hash structure
        # Format: ResFiles/{first_part}/{full_hash_path}
        resfiles_base = self.game_path.parent / "ResFiles"
        
        possible_paths = [
            # Primary: ResFiles directory structure
            resfiles_base / hash_path,
            resfiles_base / file_hash[:2] / f"{hash_path.split('/')[-1]}",
            
            # Also try within game directory
            self.game_path / "ResFiles" / hash_path,
            self.game_path / "cache" / hash_path.split('/')[0] / hash_path.split('/')[-1],
            self.game_path / "cache" / file_hash[:2] / file_hash,
            self.game_path / "cache" / hash_path,
            self.game_path / "data" / file_hash[:2] / file_hash,
            self.game_path / "data" / hash_path,
            self.game_path / hash_path,
            self.game_path / file_hash,
        ]
        
        # Also check for packed archive files as fallback
        for archive_name in ["code.ccp", "resfile.cache", "resfile.dat", "cache.dat", "data.pack"]:
            possible_paths.append(self.game_path / archive_name)
        
        for path in possible_paths:
            if path.exists():
                print(f"Found data file: {path}")
                return path
        
        # List what's actually in the game directory
        print(f"\nSearching in: {self.game_path}")
        if self.game_path.exists():
            print("Contents of game directory:")
            for item in self.game_path.iterdir():
                print(f"  {item.name} {'(dir)' if item.is_dir() else ''}")
        
        return None
    
    def extract_data(self, entry, output_path=None):
        """
        Extract the binary data for a specific entry
        
        Args:
            entry: Dictionary with offset and size information
            output_path: Optional path to save the extracted data
        """
        print(f"\nExtracting: {entry['resource_path']}")
        print(f"Hash path: {entry['hash_path']}")
        print(f"Index offset value: {entry['offset']}, Index size value: {entry['size']}")
        
        data_file = self.locate_data_file(entry)
        
        if not data_file:
            print("ERROR: Could not locate data file")
            return None
        
        # Get actual file size
        file_size = data_file.stat().st_size
        print(f"Actual file size: {file_size} bytes")
        
        # Read the entire file (ResFiles are individual files, not archives)
        with open(data_file, 'rb') as f:
            data = f.read()
        
        print(f"Extracted {len(data)} bytes")
        
        # Save to file if requested
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(data)
            print(f"Saved to: {output_path}")
        
        return data
    
    def analyze_data(self, data):
        """Attempt to identify the data structure"""
        if not data:
            return
        
        print("\n--- Data Analysis ---")
        print(f"Size: {len(data)} bytes")
        print(f"First 64 bytes (hex): {data[:64].hex()}")
        print(f"First 64 bytes (raw): {data[:64]}")
        
        # Check for common file signatures
        signatures = {
            b'PK\x03\x04': 'ZIP archive',
            b'\x1f\x8b': 'GZIP compressed',
            b'BZ': 'BZIP2 compressed',
            b'\x50\x4b': 'PKWare archive',
            b'{': 'JSON (possibly)',
            b'<': 'XML (possibly)',
        }
        
        for sig, desc in signatures.items():
            if data.startswith(sig):
                print(f"Detected format: {desc}")
                break
        
        # Try to parse as various formats
        try:
            # Try JSON
            text = data.decode('utf-8')
            json_data = json.loads(text)
            print("Successfully parsed as JSON!")
            return json_data
        except:
            pass
        
        try:
            # Try as UTF-8 text
            text = data.decode('utf-8')
            if text.isprintable():
                print("Appears to be text data")
                print(f"Preview: {text[:200]}")
                return text
        except:
            pass
        
        print("Binary data - may require specific parser")
        return data


def main():
    """Main extraction routine"""
    print("EVE Frontier Data Extractor")
    print("=" * 50)
    
    # Configuration - can be overridden by environment variables
    game_path = os.environ.get('GAME_PATH', r"C:\CCP\EVE Frontier\stillness")
    output_path = os.environ.get('OUTPUT_PATH', os.path.join('extracted_data', 'solarsystemcontent.json'))
    output_dir = Path(os.path.dirname(output_path) or 'extracted_data')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize extractor
    extractor = GameDataExtractor(game_path)
    
    # Parse the index
    extractor.parse_index_file()
    
    # Find the solar system content
    search_term = "solarsystemcontent.static"
    matches = extractor.find_entry(search_term)
    
    print(f"\nFound {len(matches)} matches for '{search_term}':")
    for match in matches:
        print(f"  - {match['resource_path']}")
        print(f"    Offset: {match['offset']}, Size: {match['size']}")
        print(f"    Hash: {match['file_hash']}")
    
    # Extract the first match
    if matches:
        entry = matches[0]
        output_file = output_dir / "solarsystemcontent.static"
        data = extractor.extract_data(entry, output_file)
        
        if data:
            # Analyze the extracted data
            result = extractor.analyze_data(data)
            
            # Save analysis report
            report_file = output_dir / "analysis_report.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"Extraction Report\n")
                f.write(f"=" * 50 + "\n")
                f.write(f"Resource: {entry['resource_path']}\n")
                f.write(f"Offset: {entry['offset']}\n")
                f.write(f"Size: {entry['size']}\n")
                f.write(f"Hash: {entry['file_hash']}\n")
                f.write(f"\nExtracted to: {output_file}\n")
            
            print(f"\nReport saved to: {report_file}")
    else:
        print(f"No entries found for '{search_term}'")


if __name__ == "__main__":
    main()
