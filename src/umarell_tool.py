"""
Umarell Inspector Toolkit for Open WebUI

A robust, multi-purpose toolkit for L'Umarell (the grumpy Milanese inspector)
to inspect building conditions by querying Neo4j for topology information
and InfluxDB for sensor data.

Three main tools are exposed:
1. query_topology - Find building elements (rooms, windows, doors, etc.)
2. check_sensor_config - Check sensor configuration for a room
3. inspect_zone_metrics - Analyze sensor data across zones

Installation in Open WebUI:
1. Go to Settings > Tools > + (Add Tool)
2. Paste this entire file
3. Save and enable the tool
"""

import os
import json
import re
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

# Graceful imports for database clients
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    from influxdb_client import InfluxDBClient
    INFLUXDB_AVAILABLE = True
except ImportError:
    INFLUXDB_AVAILABLE = False


class Tools:
    """
    Open WebUI Tool class for Umarell Inspector Toolkit
    
    Provides three methods for building inspection:
    - query_topology: Search building elements by category, floor, or name
    - check_sensor_config: Check if a room has sensors configured
    - inspect_zone_metrics: Analyze sensor data across building zones
    """
    
    def __init__(self):
        self.citation = True  # Enable citations in Open WebUI
        self._sensor_config_cache = None
        self._sensor_config_load_time = None
        
    # =========================================================================
    # Configuration Loading
    # =========================================================================
    
    def _get_neo4j_connection(self):
        """
        Get Neo4j driver connection using environment variables.
        Returns tuple of (driver, error_message).
        """
        if not NEO4J_AVAILABLE:
            return None, "Ué! The Neo4j library is not installed. Someone forgot to pip install neo4j!"
        
        neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
        neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        neo4j_password = os.environ.get('NEO4J_PASSWORD', '')
        
        try:
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            # Test connection
            driver.verify_connectivity()
            return driver, None
        except Exception as e:
            return None, f"Ué! Cannot connect to Neo4j: {str(e)}. Ma che casino!"
    
    def _get_influxdb_client(self):
        """
        Get InfluxDB client using environment variables.
        Returns tuple of (client, bucket, error_message).
        """
        if not INFLUXDB_AVAILABLE:
            return None, None, "Ué! The InfluxDB library is not installed. Someone forgot to pip install influxdb-client!"
        
        influx_host = os.environ.get('INFLUX_HOST')
        influx_token = os.environ.get('INFLUX_TOKEN')
        influx_org = os.environ.get('INFLUX_ORG')
        influx_bucket = os.environ.get('INFLUX_BUCKET')
        
        if not all([influx_host, influx_token, influx_org, influx_bucket]):
            missing = []
            if not influx_host: missing.append('INFLUX_HOST')
            if not influx_token: missing.append('INFLUX_TOKEN')
            if not influx_org: missing.append('INFLUX_ORG')
            if not influx_bucket: missing.append('INFLUX_BUCKET')
            return None, None, f"Ué! InfluxDB configuration incomplete. Missing: {', '.join(missing)}. Va che l'è brutta!"
        
        try:
            client = InfluxDBClient(url=influx_host, token=influx_token, org=influx_org)
            return client, influx_bucket, None
        except Exception as e:
            return None, None, f"Ué! Cannot connect to InfluxDB: {str(e)}. Madòna!"
    
    def _load_sensor_config(self) -> Dict[str, Any]:
        """
        Load sensor configuration from JSON file.
        Uses caching to avoid repeated file reads.
        """
        # Check cache (reload every 5 minutes)
        now = datetime.now()
        if (self._sensor_config_cache is not None and 
            self._sensor_config_load_time is not None and
            (now - self._sensor_config_load_time).seconds < 300):
            return self._sensor_config_cache
        
        # Try multiple paths for the config file
        config_paths = [
            '/app/backend/data/sensor_config.json',  # Docker path
            '/app/config/sensor_config.json',         # Alternative Docker path
            os.path.join(os.path.dirname(__file__), '..', 'config', 'sensor_config.json'),  # Relative path
            'config/sensor_config.json',              # Workspace relative
        ]
        
        for config_path in config_paths:
            try:
                with open(config_path, 'r') as f:
                    self._sensor_config_cache = json.load(f)
                    self._sensor_config_load_time = now
                    return self._sensor_config_cache
            except FileNotFoundError:
                continue
            except json.JSONDecodeError as e:
                return {"error": f"Invalid JSON in sensor_config.json: {str(e)}"}
        
        return {"error": "sensor_config.json not found in any expected location"}
    
    def _sanitize_string(self, value: str) -> str:
        """
        Sanitize a string for use in Cypher queries.
        Removes dangerous characters to prevent injection.
        """
        if value is None:
            return ""
        # Remove quotes, backslashes, and other dangerous characters
        sanitized = re.sub(r'[\'\"\\;`]', '', str(value))
        # Limit length
        return sanitized[:100]
    
    def _sanitize_for_regex(self, value: str) -> str:
        """
        Sanitize a string for use in Flux regex patterns.
        Escapes regex special characters.
        """
        if value is None:
            return ""
        # Escape regex special characters
        return re.escape(str(value))[:100]
    
    # =========================================================================
    # Method A: Query Topology
    # =========================================================================
    
    def query_topology(
        self,
        category: str = None,
        floor: str = None,
        name_contains: str = None,
        __user__: dict = {}
    ) -> str:
        """
        Query the building topology to find elements matching the criteria.
        
        Use this tool to answer questions like:
        - "How many windows are on the second floor?"
        - "Is there a bathroom on every floor?"
        - "List all meeting rooms"
        - "What rooms are on floor 3?"
        
        :param category: Element category to search for (e.g., "window", "door", "bathroom", "office", "meeting room"). Searches both English and Italian categories.
        :param floor: Floor/storey identifier to filter by (e.g., "1", "2", "001", "00S" for basement).
        :param name_contains: Partial name match for room/element names.
        :return: JSON summary with count and list of matching elements.
        """
        
        # Validate that at least one filter is provided
        if not any([category, floor, name_contains]):
            return json.dumps({
                "error": "Ué! You need to tell me what to look for. Provide at least one filter: category, floor, or name_contains.",
                "count": 0,
                "items": []
            }, indent=2)
        
        # Get Neo4j connection
        driver, error = self._get_neo4j_connection()
        if error:
            return json.dumps({"error": error, "count": 0, "items": []}, indent=2)
        
        try:
            # Build dynamic Cypher query
            where_clauses = []
            
            if category:
                safe_category = self._sanitize_string(category).lower()
                # Search both English and Italian categories with fuzzy matching
                where_clauses.append(
                    f"(toLower(n.category_en) CONTAINS '{safe_category}' OR "
                    f"toLower(n.category_it) CONTAINS '{safe_category}' OR "
                    f"toLower(n.type) CONTAINS '{safe_category}')"
                )
            
            if floor:
                safe_floor = self._sanitize_string(floor)
                # Match floor with flexible patterns (001, 1, 01, etc.)
                where_clauses.append(
                    f"(n.storey = '{safe_floor}' OR "
                    f"n.storey ENDS WITH '{safe_floor}' OR "
                    f"n.floor = '{safe_floor}')"
                )
            
            if name_contains:
                safe_name = self._sanitize_string(name_contains).lower()
                where_clauses.append(
                    f"(toLower(n.name) CONTAINS '{safe_name}' OR "
                    f"toLower(n.longname) CONTAINS '{safe_name}')"
                )
            
            # Construct the full query
            # Try both Room and Element labels for flexibility
            where_clause = " AND ".join(where_clauses)
            
            cypher_query = f"""
            MATCH (n)
            WHERE (n:Room OR n:Element OR n:Space)
            AND {where_clause}
            RETURN 
                n.room_key AS id,
                n.name AS name,
                n.longname AS longname,
                n.category_en AS category_en,
                n.category_it AS category_it,
                n.storey AS floor,
                n.area AS area,
                n.type AS type
            ORDER BY n.storey, n.name
            LIMIT 100
            """
            
            # Execute query
            with driver.session() as session:
                result = session.run(cypher_query)
                records = list(result)
            
            driver.close()
            
            # Format results
            items = []
            floors_found = set()
            
            for record in records:
                item = {
                    "id": record.get("id"),
                    "name": record.get("name"),
                    "longname": record.get("longname"),
                    "category": record.get("category_en") or record.get("category_it") or record.get("type"),
                    "floor": record.get("floor"),
                    "area": record.get("area")
                }
                # Clean up None values
                item = {k: v for k, v in item.items() if v is not None}
                items.append(item)
                
                if item.get("floor"):
                    floors_found.add(item["floor"])
            
            response = {
                "query_filters": {
                    "category": category,
                    "floor": floor,
                    "name_contains": name_contains
                },
                "count": len(items),
                "floors_represented": sorted(list(floors_found)),
                "items": items
            }
            
            return json.dumps(response, indent=2, ensure_ascii=False)
            
        except Exception as e:
            driver.close() if driver else None
            return json.dumps({
                "error": f"Ué! Query failed: {str(e)}. Ma che disastro!",
                "count": 0,
                "items": []
            }, indent=2)
    
    # =========================================================================
    # Method B: Check Sensor Configuration
    # =========================================================================
    
    def check_sensor_config(
        self,
        room_name: str,
        __user__: dict = {}
    ) -> str:
        """
        Check if a room has sensors configured and list them.
        
        Use this tool to answer questions like:
        - "Is there a temperature sensor in Room 001?"
        - "What sensors does the Kitchen have?"
        - "Does the meeting room have CO2 monitoring?"
        
        :param room_name: The name or identifier of the room to check (e.g., "Room 001", "Kitchen", "Meeting Room A").
        :return: Description of sensors configured for the room, or confirmation that none exist.
        """
        
        if not room_name:
            return "Ué! You need to tell me which room to check. Give me a room name, barlafus!"
        
        # Step 1: Find the room in Neo4j
        driver, error = self._get_neo4j_connection()
        if error:
            return error
        
        room_id = None
        room_details = None
        
        try:
            safe_name = self._sanitize_string(room_name).lower()
            
            # Search for the room with flexible matching
            cypher_query = f"""
            MATCH (r:Room)
            WHERE toLower(r.name) CONTAINS '{safe_name}'
               OR toLower(r.longname) CONTAINS '{safe_name}'
               OR toLower(r.room_key) CONTAINS '{safe_name}'
               OR toLower(r.category_en) CONTAINS '{safe_name}'
               OR toLower(r.category_it) CONTAINS '{safe_name}'
            RETURN 
                r.room_key AS room_key,
                r.name AS name,
                r.longname AS longname,
                r.storey AS floor,
                r.category_en AS category
            LIMIT 5
            """
            
            with driver.session() as session:
                result = session.run(cypher_query)
                records = list(result)
            
            driver.close()
            
            if not records:
                return f"Ué! I cannot find any room matching '{room_name}' in the building plans. Are you making things up?"
            
            # Use the first match
            room_details = {
                "room_key": records[0].get("room_key"),
                "name": records[0].get("name"),
                "longname": records[0].get("longname"),
                "floor": records[0].get("floor"),
                "category": records[0].get("category")
            }
            room_id = room_details["room_key"]
            
            # If multiple matches, note them
            other_matches = []
            if len(records) > 1:
                other_matches = [r.get("name") or r.get("room_key") for r in records[1:]]
            
        except Exception as e:
            driver.close() if driver else None
            return f"Ué! Failed to search Neo4j: {str(e)}. Ma che casino!"
        
        # Step 2: Load sensor configuration
        sensor_config = self._load_sensor_config()
        
        if "error" in sensor_config:
            return f"Ué! {sensor_config['error']}"
        
        # Step 3: Look up sensors for this room
        room_to_sensor_map = sensor_config.get('room_to_sensor_map', {})
        sensor_types = sensor_config.get('sensor_types', {})
        
        # Check if the room has any sensors
        sensors_for_room = room_to_sensor_map.get(room_id, {})
        
        # Build response
        room_desc = room_details.get("longname") or room_details.get("name") or room_id
        floor_info = f" (Floor {room_details.get('floor')})" if room_details.get('floor') else ""
        
        response_lines = [
            f"**Room:** {room_desc}{floor_info}",
            f"**Room ID:** {room_id}",
            ""
        ]
        
        if not sensors_for_room:
            response_lines.append("**Sensors:** None configured")
            response_lines.append("")
            response_lines.append("Va che l'è brutta! This room has no sensors installed. How can I monitor what I cannot measure?")
        else:
            response_lines.append("**Configured Sensors:**")
            
            # Handle different config formats
            if isinstance(sensors_for_room, dict):
                for sensor_type, sensor_id in sensors_for_room.items():
                    sensor_info = sensor_types.get(sensor_type, {})
                    unit = sensor_info.get('unit', '')
                    response_lines.append(f"  - **{sensor_type}**: `{sensor_id}` {f'({unit})' if unit else ''}")
            elif isinstance(sensors_for_room, str):
                # Simple string mapping
                response_lines.append(f"  - **sensor**: `{sensors_for_room}`")
            elif isinstance(sensors_for_room, list):
                # List of sensor IDs
                for sensor_id in sensors_for_room:
                    response_lines.append(f"  - `{sensor_id}`")
        
        if other_matches:
            response_lines.append("")
            response_lines.append(f"*Note: Also found similar rooms: {', '.join(other_matches)}*")
        
        return "\n".join(response_lines)
    
    # =========================================================================
    # Method C: Inspect Zone Metrics
    # =========================================================================
    
    def inspect_zone_metrics(
        self,
        zone_description: str,
        measurement_type: str,
        analysis_goal: str = "report",
        time_range: str = "1h",
        __user__: dict = {}
    ) -> str:
        """
        Analyze sensor metrics across a building zone.
        
        Use this tool for complex analysis questions like:
        - "Where is the air quality worst on the first floor?"
        - "Which room is the hottest right now?"
        - "What's the average humidity in all offices?"
        - "Find the coldest meeting room"
        
        :param zone_description: Description of the zone to analyze (e.g., "first floor", "all offices", "whole building", "meeting rooms").
        :param measurement_type: Type of sensor measurement to analyze (e.g., "temperature", "temp", "co2", "humidity", "air_quality").
        :param analysis_goal: Analysis type - "report" for all values, "max" for highest, "min" for lowest, "avg" for average. Default is "report".
        :param time_range: Time range for data (e.g., "1h", "6h", "24h", "7d"). Default is "1h".
        :return: Analysis results with room-by-room data or the specific room meeting the goal criteria.
        """
        
        if not zone_description:
            return "Ué! Tell me which zone to inspect. The whole building? First floor? Offices?"
        
        if not measurement_type:
            return "Ué! What should I measure? Temperature? CO2? Humidity? Be specific!"
        
        # Normalize inputs
        measurement_type_lower = measurement_type.lower().strip()
        analysis_goal_lower = analysis_goal.lower().strip() if analysis_goal else "report"
        
        # Map common measurement names to standard names
        measurement_aliases = {
            "temp": "temperature",
            "temperatura": "temperature",
            "air": "co2",
            "air_quality": "co2",
            "air quality": "co2",
            "carbon dioxide": "co2",
            "umidità": "humidity",
            "humid": "humidity"
        }
        measurement_normalized = measurement_aliases.get(measurement_type_lower, measurement_type_lower)
        
        # =====================================================================
        # Step 1: Find all rooms matching the zone description
        # =====================================================================
        
        driver, error = self._get_neo4j_connection()
        if error:
            return error
        
        try:
            # Build zone query based on description
            zone_lower = zone_description.lower()
            where_clauses = []
            
            # Check for "whole building" or similar
            if any(kw in zone_lower for kw in ["whole", "entire", "all", "tutto", "intero"]):
                # No additional filter - get all rooms
                where_clauses.append("TRUE")
            else:
                # Parse floor references
                floor_match = re.search(r'(?:floor|piano|storey|level)\s*(\d+|[a-z])', zone_lower)
                if floor_match:
                    floor_num = floor_match.group(1)
                    where_clauses.append(
                        f"(r.storey = '{floor_num}' OR r.storey ENDS WITH '{floor_num}')"
                    )
                
                # Parse category references
                category_keywords = ["office", "ufficio", "meeting", "riunion", "bathroom", "bagno", 
                                     "kitchen", "cucina", "corridor", "corridoio", "storage", "magazzino"]
                for kw in category_keywords:
                    if kw in zone_lower:
                        safe_kw = self._sanitize_string(kw)
                        where_clauses.append(
                            f"(toLower(r.category_en) CONTAINS '{safe_kw}' OR "
                            f"toLower(r.category_it) CONTAINS '{safe_kw}')"
                        )
                        break
                
                # If no specific filter matched, try fuzzy match on the description
                if not where_clauses:
                    safe_zone = self._sanitize_string(zone_description).lower()
                    where_clauses.append(
                        f"(toLower(r.name) CONTAINS '{safe_zone}' OR "
                        f"toLower(r.longname) CONTAINS '{safe_zone}' OR "
                        f"toLower(r.category_en) CONTAINS '{safe_zone}' OR "
                        f"toLower(r.category_it) CONTAINS '{safe_zone}' OR "
                        f"toLower(r.storey) CONTAINS '{safe_zone}')"
                    )
            
            where_clause = " AND ".join(where_clauses) if where_clauses else "TRUE"
            
            cypher_query = f"""
            MATCH (r:Room)
            WHERE {where_clause}
            RETURN 
                r.room_key AS room_key,
                r.name AS name,
                r.longname AS longname,
                r.storey AS floor,
                r.category_en AS category
            ORDER BY r.storey, r.name
            LIMIT 200
            """
            
            with driver.session() as session:
                result = session.run(cypher_query)
                rooms = list(result)
            
            driver.close()
            
            if not rooms:
                return f"Ué! No rooms found matching '{zone_description}'. Are you sure that zone exists?"
            
            room_data = {
                record.get("room_key"): {
                    "name": record.get("name"),
                    "longname": record.get("longname"),
                    "floor": record.get("floor"),
                    "category": record.get("category")
                }
                for record in rooms if record.get("room_key")
            }
            
        except Exception as e:
            driver.close() if driver else None
            return f"Ué! Neo4j query failed: {str(e)}. Ma che disastro!"
        
        # =====================================================================
        # Step 2: Filter rooms that have sensors of the requested type
        # =====================================================================
        
        sensor_config = self._load_sensor_config()
        if "error" in sensor_config:
            return f"Ué! {sensor_config['error']}"
        
        room_to_sensor_map = sensor_config.get('room_to_sensor_map', {})
        
        # Find rooms with matching sensors
        rooms_with_sensors = {}
        
        for room_id, room_info in room_data.items():
            sensors = room_to_sensor_map.get(room_id, {})
            
            # Handle different config formats
            if isinstance(sensors, dict):
                # Look for matching measurement type
                for sensor_type, sensor_id in sensors.items():
                    if measurement_normalized in sensor_type.lower():
                        rooms_with_sensors[room_id] = {
                            **room_info,
                            "sensor_id": sensor_id,
                            "sensor_type": sensor_type
                        }
                        break
            elif isinstance(sensors, str):
                # Simple mapping - assume it matches if measurement type is in the ID
                if measurement_normalized in sensors.lower():
                    rooms_with_sensors[room_id] = {
                        **room_info,
                        "sensor_id": sensors,
                        "sensor_type": measurement_normalized
                    }
            elif isinstance(sensors, list):
                # List of sensor IDs - check if any match
                for sensor_id in sensors:
                    if measurement_normalized in sensor_id.lower():
                        rooms_with_sensors[room_id] = {
                            **room_info,
                            "sensor_id": sensor_id,
                            "sensor_type": measurement_normalized
                        }
                        break
        
        if not rooms_with_sensors:
            return (
                f"Found {len(room_data)} rooms in '{zone_description}', "
                f"but none have '{measurement_type}' sensors configured. "
                f"Va che l'è brutta! How can I analyze what isn't measured?"
            )
        
        # =====================================================================
        # Step 3: Batch query InfluxDB for all sensor data
        # =====================================================================
        
        client, bucket, error = self._get_influxdb_client()
        if error:
            return error
        
        try:
            # Build list of sensor IDs for regex
            sensor_ids = [info["sensor_id"] for info in rooms_with_sensors.values()]
            
            # Escape and join for regex
            escaped_ids = [self._sanitize_for_regex(sid) for sid in sensor_ids]
            regex_pattern = "^(" + "|".join(escaped_ids) + ")$"
            
            # Parse time range
            time_range_clean = time_range.strip() if time_range else "1h"
            if not re.match(r'^\d+[hdwm]$', time_range_clean):
                time_range_clean = "1h"
            
            # Build Flux query with regex filter for all sensors at once
            flux_query = f'''
            from(bucket: "{bucket}")
              |> range(start: -{time_range_clean})
              |> filter(fn: (r) => r["sensor_id"] =~ /{regex_pattern}/ or r["_measurement"] =~ /{regex_pattern}/)
              |> filter(fn: (r) => r["_field"] == "value" or r["_field"] =~ /{self._sanitize_for_regex(measurement_normalized)}/)
              |> last()
            '''
            
            query_api = client.query_api()
            tables = query_api.query(flux_query)
            
            # Parse results
            sensor_values = {}
            for table in tables:
                for record in table.records:
                    sensor_id = record.values.get("sensor_id") or record.get_measurement()
                    value = record.get_value()
                    time = record.get_time()
                    field = record.get_field()
                    
                    if sensor_id and value is not None:
                        sensor_values[sensor_id] = {
                            "value": value,
                            "time": str(time),
                            "field": field
                        }
            
            client.close()
            
        except Exception as e:
            client.close() if client else None
            return f"Ué! InfluxDB query failed: {str(e)}. The sensors are not talking to me!"
        
        # =====================================================================
        # Step 4: Aggregate and analyze results
        # =====================================================================
        
        # Merge sensor values with room info
        results = []
        for room_id, room_info in rooms_with_sensors.items():
            sensor_id = room_info["sensor_id"]
            sensor_data = sensor_values.get(sensor_id, {})
            
            room_name = room_info.get("longname") or room_info.get("name") or room_id
            floor = room_info.get("floor", "?")
            
            results.append({
                "room_id": room_id,
                "room_name": room_name,
                "floor": floor,
                "sensor_id": sensor_id,
                "value": sensor_data.get("value"),
                "timestamp": sensor_data.get("time"),
                "has_data": sensor_data.get("value") is not None
            })
        
        # Filter to only rooms with actual data
        results_with_data = [r for r in results if r["has_data"]]
        results_without_data = [r for r in results if not r["has_data"]]
        
        if not results_with_data:
            return (
                f"Found {len(rooms_with_sensors)} rooms with '{measurement_type}' sensors, "
                f"but none returned data in the last {time_range_clean}. "
                f"Ma va là! Either the sensors are broken or everyone forgot to turn them on."
            )
        
        # Get unit from config if available
        sensor_types = sensor_config.get('sensor_types', {})
        unit = sensor_types.get(measurement_normalized, {}).get('unit', '')
        
        # Perform analysis based on goal
        if analysis_goal_lower == "max":
            # Find maximum value
            max_result = max(results_with_data, key=lambda x: x["value"] if isinstance(x["value"], (int, float)) else float('-inf'))
            return (
                f"**Highest {measurement_type}** in '{zone_description}':\n\n"
                f"**Room:** {max_result['room_name']} (Floor {max_result['floor']})\n"
                f"**Value:** {max_result['value']} {unit}\n"
                f"**Sensor:** {max_result['sensor_id']}\n"
                f"**Time:** {max_result['timestamp']}\n\n"
                f"*Analyzed {len(results_with_data)} rooms with active sensors.*"
            )
        
        elif analysis_goal_lower == "min":
            # Find minimum value
            min_result = min(results_with_data, key=lambda x: x["value"] if isinstance(x["value"], (int, float)) else float('inf'))
            return (
                f"**Lowest {measurement_type}** in '{zone_description}':\n\n"
                f"**Room:** {min_result['room_name']} (Floor {min_result['floor']})\n"
                f"**Value:** {min_result['value']} {unit}\n"
                f"**Sensor:** {min_result['sensor_id']}\n"
                f"**Time:** {min_result['timestamp']}\n\n"
                f"*Analyzed {len(results_with_data)} rooms with active sensors.*"
            )
        
        elif analysis_goal_lower == "avg":
            # Calculate average
            numeric_values = [r["value"] for r in results_with_data if isinstance(r["value"], (int, float))]
            if numeric_values:
                avg_value = sum(numeric_values) / len(numeric_values)
                return (
                    f"**Average {measurement_type}** in '{zone_description}':\n\n"
                    f"**Average:** {avg_value:.2f} {unit}\n"
                    f"**Range:** {min(numeric_values):.2f} - {max(numeric_values):.2f} {unit}\n"
                    f"**Rooms analyzed:** {len(numeric_values)}\n\n"
                    f"*Based on data from the last {time_range_clean}.*"
                )
            else:
                return f"Ué! No numeric values found for averaging. The data is strange!"
        
        else:  # "report" - default
            # Full report of all values
            lines = [
                f"**{measurement_type.title()} Report** for '{zone_description}'",
                f"*Time range: last {time_range_clean} | Rooms with sensors: {len(rooms_with_sensors)} | With data: {len(results_with_data)}*",
                "",
                "| Room | Floor | Value | Sensor |",
                "|------|-------|-------|--------|"
            ]
            
            # Sort by value (descending)
            sorted_results = sorted(
                results_with_data, 
                key=lambda x: x["value"] if isinstance(x["value"], (int, float)) else 0,
                reverse=True
            )
            
            for r in sorted_results:
                value_str = f"{r['value']}" if r['value'] is not None else "N/A"
                lines.append(f"| {r['room_name'][:25]} | {r['floor']} | {value_str} {unit} | {r['sensor_id'][:20]} |")
            
            if results_without_data:
                lines.append("")
                lines.append(f"*{len(results_without_data)} rooms have sensors but no recent data.*")
            
            return "\n".join(lines)
