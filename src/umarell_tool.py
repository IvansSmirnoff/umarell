"""
Umarell Inspector Tool for Open WebUI

This tool allows L'Umarell (the grumpy Milanese inspector) to inspect
building conditions by querying Neo4j for room information and InfluxDB
for sensor data.

Installation in Open WebUI:
1. Go to Settings > Tools > + (Add Tool)
2. Paste this entire file
3. Save and enable the tool

The tool will be available to the Umarell model to inspect the building.
"""

import os
import json
import requests
from typing import Optional


class Tools:
    """
    Open WebUI Tool class for Umarell Inspector
    """
    
    def __init__(self):
        self.citation = True  # Enable citations in Open WebUI
        
    def inspect_building(
        self,
        user_query: str,
        room_name: str,
        __user__: dict = {}
    ) -> str:
        """
        Inspect a building room and fetch sensor data.
        
        This tool helps L'Umarell inspect the building by:
        1. Finding the room in Neo4j using the room name
        2. Mapping the room to a sensor using sensor_config.json
        3. Fetching the latest sensor reading from InfluxDB
        
        :param user_query: The user's question (e.g., "What's the temperature in Room 101?")
        :param room_name: The name of the room to inspect (e.g., "Room 101", "Office A")
        :return: Sensor data with context for L'Umarell to analyze
        """
        
        try:
            # Step 1: Find the room's IFC ID in Neo4j using the LLM
            ifc_id = self._find_room_in_neo4j(room_name)
            if not ifc_id:
                return f"Ué! I cannot find any room called '{room_name}' in the building plans. Are you making things up, barlafus?"
            
            # Step 2: Map IFC ID to sensor ID
            sensor_id = self._map_room_to_sensor(ifc_id)
            if not sensor_id:
                return f"Room '{room_name}' (ID: {ifc_id}) exists, but no sensor is installed there. Va che l'è brutta! How can I monitor what I cannot measure?"
            
            # Step 3: Fetch sensor data from InfluxDB using the LLM
            sensor_data = self._fetch_sensor_data(sensor_id)
            if not sensor_data:
                return f"Sensor '{sensor_id}' is not responding. Ma va là! Either it's broken or someone forgot to turn it on."
            
            # Return raw facts for L'Umarell to interpret
            return self._format_result(room_name, ifc_id, sensor_id, sensor_data)
            
        except Exception as e:
            return f"Madòna! Something went wrong while inspecting: {str(e)}"
    
    def _ask_llm(self, prompt: str) -> str:
        """
        Ask the coding LLM (qwen2.5-coder:1.5b) to generate a query.
        Returns only the query text (Cypher or Flux).
        """
        ollama_url = os.environ.get('OLLAMA_BASE_URL', 'http://ollama:11434')
        
        try:
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": "qwen2.5-coder:1.5b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_predict": 512
                    }
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract the response text
            return result.get('response', '').strip()
            
        except Exception as e:
            raise Exception(f"LLM query failed: {str(e)}")
    
    def _find_room_in_neo4j(self, room_name: str) -> Optional[str]:
        """
        Use LLM to generate a Cypher query to find the room's IFC ID.
        """
        # Ask LLM to generate Cypher query
        prompt = f"""Generate a Neo4j Cypher query to find a room by name.
        
Room name/description: "{room_name}"

The database has Room nodes with properties:
- room_key (the IFC ID we need)
- name (the short room number, e.g. '001')
- longname (descriptive name)
- category_en (English category, e.g. 'Office', 'Meeting Room')
- category_it (Italian category, e.g. 'Ufficio', 'Sala Riunioni')
- storey (Floor ID, e.g. '002', '00S')

Return ONLY the Cypher query, nothing else. The query should match case-insensitively and return the room_key.
If searching by category, try to match either category_en or category_it.

Example: MATCH (r:Room) WHERE toLower(r.name) CONTAINS toLower('Room 101') OR toLower(r.category_en) CONTAINS 'meeting' RETURN r.room_key LIMIT 1
"""
        
        cypher_query = self._ask_llm(prompt)
        
        # Clean up the query (remove markdown formatting if present)
        cypher_query = cypher_query.replace('```cypher', '').replace('```', '').strip()
        
        # Execute query against Neo4j
        neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
        neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        neo4j_password = os.environ.get('NEO4J_PASSWORD', '')
        
        try:
            from neo4j import GraphDatabase
            
            driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            with driver.session() as session:
                result = session.run(cypher_query)
                record = result.single()
                if record:
                    return record[0]  # Return the room_key
            driver.close()
            
        except Exception as e:
            raise Exception(f"Neo4j query failed: {str(e)}")
        
        return None
    
    def _map_room_to_sensor(self, ifc_id: str) -> Optional[str]:
        """
        Load sensor_config.json and map IFC ID to sensor ID.
        """
        config_path = '/app/backend/data/sensor_config.json'
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            room_to_sensor = config.get('room_to_sensor_map', {})
            return room_to_sensor.get(ifc_id)
            
        except Exception as e:
            raise Exception(f"Failed to load sensor config: {str(e)}")
    
    def _fetch_sensor_data(self, sensor_id: str) -> Optional[dict]:
        """
        Use LLM to generate a Flux query and fetch data from InfluxDB.
        """
        # Get InfluxDB settings
        influx_host = os.environ.get('INFLUX_HOST')
        influx_token = os.environ.get('INFLUX_TOKEN')
        influx_org = os.environ.get('INFLUX_ORG')
        influx_bucket = os.environ.get('INFLUX_BUCKET')
        
        if not all([influx_host, influx_token, influx_org, influx_bucket]):
            raise Exception("InfluxDB configuration is missing")
        
        # Ask LLM to generate Flux query
        prompt = f"""Generate a Flux query to get the latest sensor reading.

Sensor ID: "{sensor_id}"
Bucket: "{influx_bucket}"

Return ONLY the Flux query, nothing else. Get the most recent value from the last 24 hours.

Example:
from(bucket: "my-bucket")
  |> range(start: -24h)
  |> filter(fn: (r) => r.sensor_id == "sensor_001_temp")
  |> last()
"""
        
        flux_query = self._ask_llm(prompt)
        
        # Clean up the query
        flux_query = flux_query.replace('```flux', '').replace('```', '').strip()
        
        # Execute query against InfluxDB
        try:
            from influxdb_client import InfluxDBClient
            
            client = InfluxDBClient(url=influx_host, token=influx_token, org=influx_org)
            query_api = client.query_api()
            
            tables = query_api.query(flux_query)
            
            # Extract the latest value
            for table in tables:
                for record in table.records:
                    value = record.get_value()
                    field = record.get_field()
                    time = record.get_time()
                    
                    client.close()
                    return {
                        'value': value,
                        'field': field,
                        'time': str(time),
                        'sensor_id': sensor_id
                    }
            
            client.close()
            
        except Exception as e:
            raise Exception(f"InfluxDB query failed: {str(e)}")
        
        return None
    
    def _format_result(self, room_name: str, ifc_id: str, sensor_id: str, sensor_data: dict) -> str:
        """
        Format the result for L'Umarell to interpret.
        Returns raw facts without personality - the Umarell model adds the attitude.
        """
        value = sensor_data.get('value')
        field = sensor_data.get('field', 'unknown')
        time = sensor_data.get('time', 'unknown')
        
        # Add context hints based on value
        context = ""
        if field.lower() in ['temperature', 'temp']:
            if isinstance(value, (int, float)):
                if value > 21:
                    context = "(HIGH - Wasting money)"
                elif value < 19:
                    context = "(LOW - Chilly)"
                else:
                    context = "(Acceptable)"
        
        result = f"""Room: {room_name}
IFC ID: {ifc_id}
Sensor: {sensor_id}
Measurement: {field}
Value: {value} {context}
Timestamp: {time}"""
        
        return result
