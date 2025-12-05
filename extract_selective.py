"""
EVE Frontier Selective Type Extractor with Dependency Resolution
Allows selecting specific types and automatically includes their dependencies.
"""

import json
import argparse
import os
from pathlib import Path
from collections import defaultdict


class DependencyResolver:
    """Resolves type dependencies from blueprint data"""
    
    def __init__(self, extracted_data_path):
        self.data_path = Path(extracted_data_path)
        self.blueprints = {}
        self.types = {}
        self.ships = {}
        
        # Dependency mappings
        self.type_to_blueprint = {}  # product typeID -> blueprint
        self.blueprint_materials = {}  # blueprintTypeID -> [material typeIDs]
        self.blueprint_products = {}  # blueprintTypeID -> [product typeIDs]
        
        # Categories for filtering
        self.categories = {
            'ships': set(),
            'modules': set(),
            'ammo': set(),
            'materials': set(),
            'components': set(),
            'blueprints': set(),
            'ores': set(),
            'fuel': set(),
        }
        
        self._load_data()
        self._build_dependency_graph()
        self._categorize_types()
    
    def _load_data(self):
        """Load extracted data files"""
        # Load blueprints - try raw cache format first, then processed format
        bp_file = self.data_path / "blueprints.json"
        if bp_file.exists():
            with open(bp_file, 'r', encoding='utf-8') as f:
                bp_data = json.load(f)
            
            # Handle both formats
            if 'cache' in bp_data:
                # Raw SQLite cache format
                for entry in bp_data['cache']:
                    bp = json.loads(entry['value'])
                    self.blueprints[bp['blueprintTypeID']] = bp
            elif 'blueprints' in bp_data:
                # Processed format from previous export
                for bp_id, bp in bp_data['blueprints'].items():
                    self.blueprints[int(bp_id)] = bp
            else:
                # Direct dict format (bp_id -> bp_data)
                for bp_id, bp in bp_data.items():
                    if bp_id.isdigit():
                        self.blueprints[int(bp_id)] = bp
            
            print(f"[OK] Loaded {len(self.blueprints)} blueprints")
        
        # Load types (prefer frontier, fall back to full)
        types_file = self.data_path / "types_frontier.json"
        if not types_file.exists():
            types_file = self.data_path / "types.json"
        
        if types_file.exists():
            with open(types_file, 'r', encoding='utf-8') as f:
                self.types = json.load(f)
            print(f"[OK] Loaded {len(self.types)} types from {types_file.name}")
        
        # Load ships (try ships_with_deps.json first as it has full dogma data)
        ships_file = self.data_path / "ships_with_deps.json"
        if not ships_file.exists():
            ships_file = self.data_path / "ships.json"
        
        if ships_file.exists():
            with open(ships_file, 'r', encoding='utf-8') as f:
                ships_data = json.load(f)
            
            # Handle both formats
            if 'ships' in ships_data:
                # Exported format with 'ships' key
                self.ships = ships_data['ships']
            else:
                # Direct format (ship_id -> ship_data)
                self.ships = ships_data
            
            # Count only actual ships (numeric keys)
            ship_count = sum(1 for k in self.ships.keys() if str(k).isdigit())
            print(f"[OK] Loaded {ship_count} ships from {ships_file.name}")
        
        # Load dogma data for all types (if available)
        self.all_dogma = {}
        dogma_file = self.data_path / "all_dogma.json"
        if dogma_file.exists():
            with open(dogma_file, 'r', encoding='utf-8') as f:
                self.all_dogma = json.load(f)
            print(f"[OK] Loaded dogma for {len(self.all_dogma)} types")
    
    def _build_dependency_graph(self):
        """Build dependency graph from blueprints"""
        for bp_id, bp in self.blueprints.items():
            activities = bp.get('activities', {})
            
            # Add blueprint itself
            self.categories['blueprints'].add(bp_id)
            
            for activity_name, activity in activities.items():
                # Map products to their blueprint
                products = activity.get('products', [])
                for prod in products:
                    self.type_to_blueprint[prod['typeID']] = bp_id
                
                # Store materials for each blueprint
                materials = activity.get('materials', [])
                if bp_id not in self.blueprint_materials:
                    self.blueprint_materials[bp_id] = set()
                    self.blueprint_products[bp_id] = set()
                
                for mat in materials:
                    self.blueprint_materials[bp_id].add(mat['typeID'])
                
                for prod in products:
                    self.blueprint_products[bp_id].add(prod['typeID'])
        
        print(f"[OK] Built dependency graph: {len(self.type_to_blueprint)} products from blueprints")
    
    def _categorize_types(self):
        """Categorize types based on their properties and names"""
        # Ship groups
        ship_groups = {25, 26, 31, 237, 419, 420}  # Frigate, Cruiser, Shuttle, Corvette, Industrial, Destroyer
        
        for tid_str, type_data in self.types.items():
            tid = int(tid_str)
            group_id = type_data.get('groupID', 0)
            type_name = str(type_data.get('typeName', ''))
            
            # Ships
            if group_id in ship_groups:
                self.categories['ships'].add(tid)
                continue
            
            # Blueprints
            if 'Blueprint' in type_name:
                self.categories['blueprints'].add(tid)
                continue
            
            # Ores and Minerals (raw materials from mining)
            if any(x in type_name for x in ['Ore', 'Mineral', 'Young Crude', 'Feral Echo', 'Salvaged', 'Aestasium']):
                self.categories['ores'].add(tid)
                continue
            
            # Fuel
            if any(x in type_name for x in ['Fuel', 'SOF', 'Smart Fuel']):
                self.categories['fuel'].add(tid)
                continue
            
            # Ammo/Charges
            if any(x in type_name for x in ['Charge', 'Missile', 'Ammo', 'Round']):
                self.categories['ammo'].add(tid)
                continue
            
            # Weapons
            if any(x in type_name for x in ['Disintegrator', 'Beam', 'Torpedo', 'Launcher', 'Turret', 'Cannon', 'Blaster', 'Railgun', 'Artillery']):
                self.categories['modules'].add(tid)
                continue
            
            # Shields/Defense
            if any(x in type_name for x in ['Field Array', 'Shield', 'Armor', 'Hull Repair', 'Hardener', 'Repairer', 'Plates']):
                self.categories['modules'].add(tid)
                continue
            
            # Propulsion
            if any(x in type_name for x in ['Afterburner', 'Microwarpdrive', 'MWD', 'Engine', 'Propulsion', 'Thruster']):
                self.categories['modules'].add(tid)
                continue
            
            # Electronic/Utility
            if any(x in type_name for x in ['Sensor', 'Scanner', 'Scrambler', 'Disruptor', 'Web', 'ECM', 'ECCM', 'Tracking', 'Target']):
                self.categories['modules'].add(tid)
                continue
            
            # Mining/Industrial modules
            if any(x in type_name for x in ['Mining Lens', 'Mining Gel', 'Miner', 'Strip', 'Harvester', 'Tractor', 'Cargo Grid']):
                self.categories['modules'].add(tid)
                continue
            
            # Everything else - check if craftable or raw
            if tid in self.type_to_blueprint:
                # It's a craftable product (component)
                self.categories['components'].add(tid)
            else:
                # It's a raw material
                self.categories['materials'].add(tid)
        
        # Add ships from ships.json (skip non-numeric keys like 'meta')
        for tid_str in self.ships:
            if tid_str.isdigit():
                self.categories['ships'].add(int(tid_str))
        
        print(f"\n=== Type Categories ===")
        for cat, items in self.categories.items():
            print(f"  {cat}: {len(items)} types")
    
    def get_dependencies(self, type_id, depth=10, visited=None):
        """
        Get all dependencies for a type recursively.
        Returns a set of type IDs needed to manufacture this type.
        """
        if visited is None:
            visited = set()
        
        if depth <= 0 or type_id in visited:
            return set()
        
        visited.add(type_id)
        dependencies = {type_id}
        
        # Check if this type is craftable (has a blueprint)
        if type_id in self.type_to_blueprint:
            bp_id = self.type_to_blueprint[type_id]
            
            # Add the blueprint itself
            dependencies.add(bp_id)
            
            # Add all materials
            materials = self.blueprint_materials.get(bp_id, set())
            for mat_id in materials:
                dependencies.add(mat_id)
                # Recursively get dependencies of materials
                sub_deps = self.get_dependencies(mat_id, depth - 1, visited)
                dependencies.update(sub_deps)
        
        return dependencies
    
    def get_full_chain(self, type_id):
        """
        Get the full manufacturing chain for a type.
        Returns a dict with the type and all its dependencies organized by level.
        """
        chain = {
            'target': type_id,
            'target_name': self._get_type_name(type_id),
            'levels': []
        }
        
        visited = set()
        current_level = {type_id}
        
        while current_level:
            level_data = []
            next_level = set()
            
            for tid in current_level:
                if tid in visited:
                    continue
                visited.add(tid)
                
                type_info = {
                    'typeID': tid,
                    'typeName': self._get_type_name(tid),
                    'craftable': tid in self.type_to_blueprint,
                    'materials': []
                }
                
                if tid in self.type_to_blueprint:
                    bp_id = self.type_to_blueprint[tid]
                    materials = self.blueprint_materials.get(bp_id, set())
                    
                    for mat_id in materials:
                        mat_info = {
                            'typeID': mat_id,
                            'typeName': self._get_type_name(mat_id),
                            'craftable': mat_id in self.type_to_blueprint
                        }
                        type_info['materials'].append(mat_info)
                        if mat_id not in visited:
                            next_level.add(mat_id)
                
                level_data.append(type_info)
            
            if level_data:
                chain['levels'].append(level_data)
            current_level = next_level
        
        return chain
    
    def _get_type_name(self, type_id):
        """Get type name from types or ships"""
        tid_str = str(type_id)
        
        if tid_str in self.ships and isinstance(self.ships[tid_str], dict):
            return self.ships[tid_str].get('typeName', f'Type {type_id}')
        elif tid_str in self.types:
            return self.types[tid_str].get('typeName', f'Type {type_id}')
        else:
            return f'Type {type_id}'
    
    def search_types(self, query):
        """Search for types by name"""
        query_lower = query.lower()
        results = []
        
        # Search in types
        for tid_str, type_data in self.types.items():
            name = type_data.get('typeName', '')
            if name and query_lower in name.lower():
                results.append({
                    'typeID': int(tid_str),
                    'typeName': name,
                    'groupID': type_data.get('groupID'),
                    'source': 'types'
                })
        
        # Search in ships
        for tid_str, ship_data in self.ships.items():
            name = ship_data.get('typeName', '')
            if name and query_lower in name.lower():
                # Check if already in results
                if not any(r['typeID'] == int(tid_str) for r in results):
                    results.append({
                        'typeID': int(tid_str),
                        'typeName': name,
                        'groupID': ship_data.get('groupID'),
                        'groupName': ship_data.get('groupName'),
                        'source': 'ships'
                    })
        
        return sorted(results, key=lambda x: x['typeName'])
    
    def export_selection(self, type_ids, output_file, include_dependencies=True):
        """
        Export selected types (with optional dependencies) to a JSON file.
        """
        selected = set(type_ids)
        
        if include_dependencies:
            for tid in type_ids:
                deps = self.get_dependencies(tid)
                selected.update(deps)
        
        # Build output
        output = {
            'meta': {
                'selected_count': len(type_ids),
                'total_with_dependencies': len(selected),
                'include_dependencies': include_dependencies
            },
            'types': {},
            'ships': {},
            'blueprints': {}
        }
        
        for tid in selected:
            tid_str = str(tid)
            
            # Add to ships if it's a ship
            if tid_str in self.ships:
                output['ships'][tid_str] = self.ships[tid_str]
            
            # Add to types
            if tid_str in self.types:
                output['types'][tid_str] = self.types[tid_str]
            
            # Add blueprint if it produces this type
            if tid in self.type_to_blueprint:
                bp_id = self.type_to_blueprint[tid]
                output['blueprints'][str(bp_id)] = self.blueprints[bp_id]
        
        # Save
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        file_size = output_path.stat().st_size
        print(f"\n[OK] Exported to {output_file}")
        print(f"  Types: {len(output['types'])}")
        print(f"  Ships: {len(output['ships'])}")
        print(f"  Blueprints: {len(output['blueprints'])}")
        print(f"  File size: {file_size / 1024:.1f} KB")
        
        return output
    
    def list_category(self, category):
        """List all types in a category"""
        if category not in self.categories:
            print(f"Unknown category: {category}")
            print(f"Available: {', '.join(self.categories.keys())}")
            return []
        
        items = []
        for tid in self.categories[category]:
            items.append({
                'typeID': tid,
                'typeName': self._get_type_name(tid)
            })
        
        return sorted(items, key=lambda x: x['typeName'])
    
    def export_category(self, category, output_file, include_dependencies=True):
        """Export all types in a category - focused output with only that category's data"""
        if category not in self.categories:
            print(f"Unknown category: {category}")
            return None
        
        # Each category exports only its own data type
        if category == 'blueprints':
            return self.export_blueprints_only(output_file)
        elif category == 'ships':
            return self.export_ships_only(output_file)
        elif category == 'modules':
            return self.export_modules_only(output_file)
        else:
            # For other categories, export just the types
            type_ids = list(self.categories[category])
            return self.export_types_only(type_ids, category, output_file)
    
    def export_ships_only(self, output_file):
        """Export only ships with their stats - no other types"""
        output = {}
        
        for tid in self.categories['ships']:
            tid_str = str(tid)
            if tid_str in self.ships:
                output[tid_str] = self.ships[tid_str]
            elif tid_str in self.types:
                # Ship might be in types if no dogma data
                output[tid_str] = self.types[tid_str]
        
        # Save
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        file_size = output_path.stat().st_size
        print(f"\n[OK] Exported to {output_file}")
        print(f"  Ships: {len(output)}")
        print(f"  File size: {file_size / 1024:.1f} KB")
        
        return output
    
    def export_modules_only(self, output_file):
        """Export only modules with their stats and dogma attributes"""
        output = {}
        dogma_count = 0
        
        for tid in self.categories['modules']:
            tid_str = str(tid)
            if tid_str in self.types:
                module_data = dict(self.types[tid_str])  # Copy
                # Add dogma if available
                if tid_str in self.all_dogma:
                    module_data['dogmaAttributes'] = self.all_dogma[tid_str]
                    dogma_count += 1
                output[tid_str] = module_data
        
        # Save
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        file_size = output_path.stat().st_size
        print(f"\n[OK] Exported to {output_file}")
        print(f"  Modules: {len(output)} ({dogma_count} with dogma)")
        print(f"  File size: {file_size / 1024:.1f} KB")
        
        return output
    
    def export_blueprints_only(self, output_file):
        """Export only blueprint data - no types"""
        # Save
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.blueprints, f, indent=2, ensure_ascii=False)
        
        file_size = output_path.stat().st_size
        print(f"\n[OK] Exported to {output_file}")
        print(f"  Blueprints: {len(self.blueprints)}")
        print(f"  File size: {file_size / 1024:.1f} KB")
        
        return self.blueprints
    
    def export_types_only(self, type_ids, category_name, output_file):
        """Export only types for a given category with dogma attributes"""
        output = {}
        dogma_count = 0
        
        for tid in type_ids:
            tid_str = str(tid)
            if tid_str in self.types:
                type_data = dict(self.types[tid_str])  # Copy
                # Add dogma if available
                if tid_str in self.all_dogma:
                    type_data['dogmaAttributes'] = self.all_dogma[tid_str]
                    dogma_count += 1
                output[tid_str] = type_data
        
        # Save
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        file_size = output_path.stat().st_size
        print(f"\n[OK] Exported to {output_file}")
        print(f"  {category_name.title()}: {len(output)} ({dogma_count} with dogma)")
        print(f"  File size: {file_size / 1024:.1f} KB")
        
        return output

    def export_all_blueprints(self, output_file, include_dependencies=True):
        """Export all blueprints with their products and materials"""
        # Collect all types referenced in blueprints
        all_types = set()
        
        for bp_id, bp in self.blueprints.items():
            all_types.add(bp_id)  # Blueprint itself
            activities = bp.get('activities', {})
            for activity_name, activity in activities.items():
                for prod in activity.get('products', []):
                    all_types.add(prod['typeID'])
                for mat in activity.get('materials', []):
                    all_types.add(mat['typeID'])
        
        # Include dependencies for all types if requested
        if include_dependencies:
            expanded = set()
            for tid in all_types:
                deps = self.get_dependencies(tid)
                expanded.update(deps)
            all_types = expanded
        
        # Build output
        output = {
            'meta': {
                'blueprint_count': len(self.blueprints),
                'total_types': len(all_types),
                'include_dependencies': include_dependencies
            },
            'blueprints': self.blueprints,  # All blueprints
            'types': {},
            'ships': {}
        }
        
        for tid in all_types:
            tid_str = str(tid)
            
            if tid_str in self.ships and isinstance(self.ships[tid_str], dict):
                output['ships'][tid_str] = self.ships[tid_str]
            
            if tid_str in self.types:
                output['types'][tid_str] = self.types[tid_str]
        
        # Save
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        file_size = output_path.stat().st_size
        print(f"\n[OK] Exported to {output_file}")
        print(f"  Blueprints: {len(output['blueprints'])}")
        print(f"  Types: {len(output['types'])}")
        print(f"  Ships: {len(output['ships'])}")
        print(f"  File size: {file_size / 1024:.1f} KB")
        
        return output


def interactive_mode(resolver):
    """Interactive mode for selecting types"""
    print("\n" + "="*70)
    print("INTERACTIVE TYPE SELECTOR")
    print("="*70)
    print("\nCommands:")
    print("  search <query>     - Search for types by name")
    print("  deps <typeID>      - Show dependencies for a type")
    print("  chain <typeID>     - Show full manufacturing chain")
    print("  list <category>    - List types in category")
    print("  categories         - Show all categories")
    print("  select <typeID>    - Add type to selection")
    print("  remove <typeID>    - Remove type from selection")
    print("  show               - Show current selection")
    print("  export <filename>  - Export selection to file")
    print("  export-cat <cat>   - Export entire category")
    print("  clear              - Clear selection")
    print("  quit               - Exit")
    print()
    
    selection = set()
    
    while True:
        try:
            cmd = input(f"[{len(selection)} selected] > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not cmd:
            continue
        
        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        
        if action == 'quit' or action == 'exit':
            break
        
        elif action == 'search':
            if not arg:
                print("Usage: search <query>")
                continue
            results = resolver.search_types(arg)
            print(f"\nFound {len(results)} results:")
            for r in results[:20]:
                print(f"  {r['typeID']:>6}: {r['typeName']}")
            if len(results) > 20:
                print(f"  ... and {len(results) - 20} more")
        
        elif action == 'deps':
            if not arg:
                print("Usage: deps <typeID>")
                continue
            try:
                tid = int(arg)
                deps = resolver.get_dependencies(tid)
                print(f"\n{resolver._get_type_name(tid)} requires {len(deps)} types:")
                for d in sorted(deps):
                    name = resolver._get_type_name(d)
                    craftable = "📦" if d in resolver.type_to_blueprint else "⛏️"
                    print(f"  {craftable} {d:>6}: {name}")
            except ValueError:
                print("Invalid typeID")
        
        elif action == 'chain':
            if not arg:
                print("Usage: chain <typeID>")
                continue
            try:
                tid = int(arg)
                chain = resolver.get_full_chain(tid)
                print(f"\nManufacturing chain for {chain['target_name']}:")
                for i, level in enumerate(chain['levels']):
                    indent = "  " * i
                    for item in level:
                        craftable = "📦" if item['craftable'] else "⛏️"
                        print(f"{indent}{craftable} {item['typeName']}")
                        if item['materials']:
                            for mat in item['materials']:
                                mat_craft = "📦" if mat['craftable'] else "⛏️"
                                print(f"{indent}  └─ {mat_craft} {mat['typeName']}")
            except ValueError:
                print("Invalid typeID")
        
        elif action == 'list':
            if not arg:
                print("Usage: list <category>")
                print(f"Categories: {', '.join(resolver.categories.keys())}")
                continue
            items = resolver.list_category(arg)
            print(f"\n{arg.upper()} ({len(items)} items):")
            for item in items[:30]:
                print(f"  {item['typeID']:>6}: {item['typeName']}")
            if len(items) > 30:
                print(f"  ... and {len(items) - 30} more")
        
        elif action == 'categories':
            print("\nCategories:")
            for cat, items in resolver.categories.items():
                print(f"  {cat}: {len(items)} types")
        
        elif action == 'select':
            if not arg:
                print("Usage: select <typeID>")
                continue
            try:
                tid = int(arg)
                selection.add(tid)
                print(f"Added {resolver._get_type_name(tid)}")
            except ValueError:
                print("Invalid typeID")
        
        elif action == 'remove':
            if not arg:
                print("Usage: remove <typeID>")
                continue
            try:
                tid = int(arg)
                selection.discard(tid)
                print(f"Removed {resolver._get_type_name(tid)}")
            except ValueError:
                print("Invalid typeID")
        
        elif action == 'show':
            print(f"\nCurrent selection ({len(selection)} types):")
            for tid in sorted(selection):
                deps = resolver.get_dependencies(tid)
                print(f"  {tid:>6}: {resolver._get_type_name(tid)} (+{len(deps)-1} deps)")
        
        elif action == 'export':
            if not arg:
                arg = "selected_types.json"
            resolver.export_selection(list(selection), arg)
        
        elif action == 'export-cat':
            if not arg:
                print("Usage: export-cat <category>")
                continue
            output_name = f"{arg}_types.json"
            resolver.export_category(arg, output_name)
        
        elif action == 'clear':
            selection.clear()
            print("Selection cleared")
        
        else:
            print(f"Unknown command: {action}")


def main():
    parser = argparse.ArgumentParser(
        description='EVE Frontier Selective Type Extractor with Dependency Resolution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python extract_selective.py
  
  # Search for types
  python extract_selective.py --search "TADES"
  
  # Show dependencies for a type
  python extract_selective.py --deps 91101
  
  # Export a category with dependencies
  python extract_selective.py --category ships --output ships_full.json
  
  # Export specific types
  python extract_selective.py --types 91101,91102,91103 --output selected.json
  
  # Export without dependencies
  python extract_selective.py --types 91101 --no-deps --output single.json
        """
    )
    
    parser.add_argument('--data-path', '-d',
                       help='Path to extracted_data folder',
                       default='extracted_data')
    parser.add_argument('--search', '-s',
                       help='Search for types by name')
    parser.add_argument('--deps',
                       help='Show dependencies for a typeID',
                       type=int)
    parser.add_argument('--chain',
                       help='Show full manufacturing chain for a typeID',
                       type=int)
    parser.add_argument('--category', '-c',
                       help='Export all types in a category',
                       choices=['ships', 'modules', 'ammo', 'materials', 'components', 'blueprints', 'ores', 'fuel'])
    parser.add_argument('--list-category', '-l',
                       help='List types in a category',
                       choices=['ships', 'modules', 'ammo', 'materials', 'components', 'blueprints', 'ores', 'fuel'])
    parser.add_argument('--types', '-t',
                       help='Comma-separated list of typeIDs to export')
    parser.add_argument('--output', '-o',
                       help='Output file for export',
                       default='selected_types.json')
    parser.add_argument('--no-deps',
                       action='store_true',
                       help='Export without dependencies')
    parser.add_argument('--interactive', '-i',
                       action='store_true',
                       help='Start interactive mode')
    
    args = parser.parse_args()
    
    print("="*70)
    print("EVE FRONTIER SELECTIVE TYPE EXTRACTOR")
    print("="*70)
    print()
    
    # Initialize resolver
    resolver = DependencyResolver(args.data_path)
    
    # Handle commands
    if args.search:
        results = resolver.search_types(args.search)
        print(f"\nSearch results for '{args.search}':")
        for r in results:
            src = f"[{r['source']}]" if 'source' in r else ""
            print(f"  {r['typeID']:>6}: {r['typeName']} {src}")
    
    elif args.deps:
        deps = resolver.get_dependencies(args.deps)
        name = resolver._get_type_name(args.deps)
        print(f"\nDependencies for {name} (ID: {args.deps}):")
        print(f"Total: {len(deps)} types needed\n")
        for d in sorted(deps):
            dep_name = resolver._get_type_name(d)
            craftable = "📦 (craftable)" if d in resolver.type_to_blueprint else "⛏️ (raw)"
            print(f"  {d:>6}: {dep_name} {craftable}")
    
    elif args.chain:
        chain = resolver.get_full_chain(args.chain)
        print(f"\nManufacturing chain for {chain['target_name']}:\n")
        for i, level in enumerate(chain['levels']):
            if i == 0:
                print("TARGET:")
            else:
                print(f"\nLEVEL {i} (materials):")
            
            for item in level:
                craftable = "📦" if item['craftable'] else "⛏️"
                print(f"  {craftable} {item['typeID']:>6}: {item['typeName']}")
    
    elif args.list_category:
        items = resolver.list_category(args.list_category)
        print(f"\n{args.list_category.upper()} ({len(items)} items):\n")
        for item in items:
            print(f"  {item['typeID']:>6}: {item['typeName']}")
    
    elif args.category:
        output_file = args.output if args.output != 'selected_types.json' else f"{args.category}_export.json"
        resolver.export_category(args.category, output_file, not args.no_deps)
    
    elif args.types:
        type_ids = [int(t.strip()) for t in args.types.split(',')]
        resolver.export_selection(type_ids, args.output, not args.no_deps)
    
    elif args.interactive or not any([args.search, args.deps, args.chain, args.list_category, args.category, args.types]):
        interactive_mode(resolver)
    
    print()


if __name__ == "__main__":
    main()
