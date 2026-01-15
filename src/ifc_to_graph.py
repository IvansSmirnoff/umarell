#!/usr/bin/env python3
"""
ifc_to_graph.py

Import IfcSpace (rooms) into Neo4j with semantic data (Storey, Area, Psets).
"""

import argparse
import json
import os
import re
from neo4j import GraphDatabase

try:
    import ifcopenshell
    import ifcopenshell.util.element  # <--- NEW: Required for extracting semantics
except Exception:
    ifcopenshell = None


def load_config(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize(text):
    if not text:
        return ''
    text = str(text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()


def main(ifc_path, config_path):
    if ifcopenshell is None:
        raise RuntimeError("ifcopenshell is required. Install with `pip install ifcopenshell`.")

    config = load_config(config_path)
    room_keys = set(config.get('room_to_sensor_map', {}).keys())

    print(f"Loaded {len(room_keys)} room keys from config")

    model = ifcopenshell.open(ifc_path)
    spaces = model.by_type('IfcSpace')
    print(f"Found {len(spaces)} IfcSpace entities")

    # Neo4j connection
    uri = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'test')
    driver = GraphDatabase.driver(uri, auth=(user, password))

    matched_keys = set()

    with driver.session() as session:
        for space in spaces:
            # 1. Basic Attributes
            name = getattr(space, 'Name', None)
            longname = getattr(space, 'LongName', None)
            globalid = getattr(space, 'GlobalId', None)
            
            # 2. Semantic: Object Type (often contains 'Office', 'Corridor', etc.)
            obj_type = getattr(space, 'ObjectType', None)

            # 3. Semantic: Hierarchy (The Storey)
            # finding the 'parent' container (IfcBuildingStorey)
            container = ifcopenshell.util.element.get_container(space)
            storey_name = container.Name if container and container.is_a('IfcBuildingStorey') else None

            # 4. Semantic: Properties (Psets)
            psets = ifcopenshell.util.element.get_psets(space)
            
            # Extract standard properties
            space_common = psets.get('Pset_SpaceCommon', {})
            area = space_common.get('GrossPlannedArea') or space_common.get('NetPlannedArea') or space_common.get('Area')
            is_external = space_common.get('IsExternal')

            # Extract Custom 'IFC_Locali' properties (Project Specific)
            ifc_locali = psets.get('IFC_Locali', {})
            # Storey from 'PBSs_III_PIANO' (e.g. '00S', '01') or fallback to container name
            custom_storey = ifc_locali.get('PBSs_III_PIANO')
            final_storey = custom_storey if custom_storey else storey_name

            # Category from 'SBSm_CATEGORIA_DESCRIZIONE' (e.g. 'UFFICI')
            category_it = ifc_locali.get('SBSm_CATEGORIA_DESCRIZIONE')
            
            # Simple IT -> EN Mapping for common categories
            category_map = {
                'UFFICI': 'Office',
                'AULE': 'Classroom',
                'AULA': 'Classroom',
                'SERVIZI': 'Restroom',
                'WC': 'Restroom',
                'CIRC.ORIZ': 'Corridor',
                'CONNETTIVO': 'Corridor',
                'SCALE': 'Stairs',
                'DEPOSITI': 'Storage',
                'DEPOSITO': 'Storage',
                'TECNICI': 'Technical Room',
                'LOCALE TECNICO': 'Technical Room',
                'LABORATORI': 'Laboratory',
                'LABORATORIO': 'Laboratory',
                'RISTORO': 'Break Room',
                'SPAZI COMPLEMENTARI': 'Support Space',
                'SALA RIUNIONI': 'Meeting Room',
                'SALA STUDIO': 'Study Room'
            }
            # Attempt to map, mostly matching prefix if needed
            category_en = None
            if category_it:
                # Direct match or partial match (e.g. 'UFFICI' in 'UFFICI DOCENTI')
                for k_it, v_en in category_map.items():
                    if k_it in category_it.upper():
                        category_en = v_en
                        break
            
            # Serialize ALL semantics to a single JSON string property
            full_attributes_json = json.dumps(psets, default=str)

            # --- Matching Logic (Same as before) ---
            p_name = normalize(name)
            p_long = normalize(longname)
            p_global = normalize(globalid)
            p_combined_1 = normalize(f"{longname} {name}")
            p_combined_2 = normalize(f"{name} {longname}")

            found_key = None
            for key in room_keys:
                k = normalize(key)
                # Exact match against fields
                if k in [p_global, p_name, p_long, p_combined_1, p_combined_2]:
                    found_key = key
                    break
                # Composite fuzzy match (strict)
                if k in p_combined_1 or k in p_combined_2:
                    found_key = key
                    break
                if p_combined_1 in k or p_combined_2 in k:
                    found_key = key
                    break

            final_key = found_key
            
            # If not matched, create auto-key if you still want the node
            if not final_key and globalid:
                final_key = f"ifc_auto_{globalid}"

            if final_key:
                if found_key:
                    matched_keys.add(found_key)

                # Prepare properties for Neo4j
                props = {
                    'room_key': final_key,
                    'name': name,
                    'long_name': longname,
                    'globalid': globalid,
                    'type': obj_type,
                    'storey': final_storey,       # Now using custom prop if avail
                    'area': float(area) if area else None,
                    'is_external': is_external,
                    'category_it': category_it,   # NEW
                    'category_en': category_en,   # NEW
                    'all_props': full_attributes_json
                }

                cypher = (
                    "MERGE (r:Room {room_key: $room_key})\n"
                    "SET r.name = $name, \n"
                    "    r.long_name = $long_name, \n"
                    "    r.globalid = $globalid, \n"
                    "    r.type = $type, \n"
                    "    r.storey = $storey, \n"
                    "    r.area = $area, \n"
                    "    r.is_external = $is_external, \n"
                    "    r.category_it = $category_it, \n"
                    "    r.category_en = $category_en, \n"
                    "    r.all_properties = $all_props"
                )
                session.run(cypher, props)
                print(f"Upserted Room: {final_key} | Storey: {final_storey} | Cat: {category_it}/{category_en}")

        # Ensure unmapped config keys exist (placeholders)
        for key in room_keys - matched_keys:
            session.run("MERGE (r:Room {room_key: $room_key}) SET r.type='Placeholder'", {'room_key': key})

    driver.close()
    print("IFC import complete.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import IfcSpace with Semantics')
    parser.add_argument('--ifc', required=True, help='Path to IFC file')
    parser.add_argument('--config', default='sensor_config.json', help='Path to sensor_config.json')
    args = parser.parse_args()

    main(args.ifc, args.config)
