#!/usr/bin/env python3
"""
llm_router_tool.py

A Python tool compatible with Open WebUI's Python Tools system that routes
natural language building queries to Neo4j (structural/semantic) or to InfluxDB
for time-series data. Uses an Ollama instance as the LLM endpoint.

Requirements:
  pip install requests neo4j influxdb-client

Environment variables used:
  - OLLAMA_URL (default: http://ollama:11434)
  - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
  - INFLUX_HOST, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET

"""

import json
import os
import re
from typing import Dict, Any, List

import requests
from neo4j import GraphDatabase

try:
    from influxdb_client import InfluxDBClient
except Exception:
    InfluxDBClient = None


class LLMRouterTool:
    def __init__(self, sensor_config_path: str = 'sensor_config.json'):
        self.ollama_url = os.environ.get('OLLAMA_URL', 'http://ollama:11434')
        self.ollama_generate = f"{self.ollama_url}/api/generate"

        # Neo4j
        neo_uri = os.environ.get('NEO4J_URI', 'bolt://neo4j:7687')
        neo_user = os.environ.get('NEO4J_USER', 'neo4j')
        neo_pass = os.environ.get('NEO4J_PASSWORD', 'test')
        self.neo_driver = GraphDatabase.driver(neo_uri, auth=(neo_user, neo_pass))

        # InfluxDB client
        influx_host = os.environ.get('INFLUX_HOST')
        influx_token = os.environ.get('INFLUX_TOKEN')
        influx_org = os.environ.get('INFLUX_ORG')
        influx_bucket = os.environ.get('INFLUX_BUCKET')
        self.influx_bucket = influx_bucket

        if influx_host and influx_token and InfluxDBClient is not None:
            self.influx_client = InfluxDBClient(url=influx_host, token=influx_token, org=influx_org)
            self.influx_query_api = self.influx_client.query_api()
        else:
            self.influx_client = None
            self.influx_query_api = None

        # Sensor config
        with open(sensor_config_path, 'r', encoding='utf-8') as f:
            self.sensor_config = json.load(f)

    def ask_llm_for_query(self, prompt: str, model: str, context: Dict[str, Any] = None) -> str:
        """Call Ollama generate endpoint and return a single text response.

        The function asks the coding LLM to produce only the requested query text
        (plain Cypher or Flux) and returns that string.
        """
        payload = {
            'model': model,
            'prompt': prompt,
            'max_tokens': 1024,
            'temperature': 0.0,
        }
        if context:
            payload['context'] = context

        resp = requests.post(self.ollama_generate, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Ollama responses can be shaped differently depending on version; attempt robust parsing
        text = None
        # Common: data['result'] or data['output'] or data['choices']
        if isinstance(data, dict):
            if 'result' in data and isinstance(data['result'], str):
                text = data['result']
            elif 'output' in data and isinstance(data['output'], list):
                # find first text entry
                for o in data['output']:
                    if isinstance(o, dict) and 'content' in o:
                        text = o['content']
                        break
            elif 'choices' in data and isinstance(data['choices'], list):
                choice = data['choices'][0]
                text = choice.get('message', {}).get('content') if isinstance(choice, dict) else None

        if text is None:
            # Fallback to raw text
            text = data.get('text') if isinstance(data, dict) else str(data)

        # Clean common code fences
        text = re.sub(r"^```(cypher|flux)?\n", '', text.strip())
        text = re.sub(r"\n```$", '', text)

        return text.strip()

    def _run_cypher(self, cypher: str) -> List[Dict[str, Any]]:
        with self.neo_driver.session() as session:
            res = session.run(cypher)
            records = [dict(r) for r in res]
            return records

    def _run_flux(self, flux: str) -> List[Dict[str, Any]]:
        if not self.influx_query_api:
            raise RuntimeError('InfluxDB client not configured (check INFLUX_* env vars)')
        tables = self.influx_query_api.query(flux)
        results = []
        for table in tables:
            for record in table.records:
                results.append({'_time': record.get_time().isoformat() if record.get_time() else None,
                                **{k: v for k, v in record.values.items() if k != '_time'}})
        return results

    def ask_building_data(self, natural_language_query: str, room_name: str = None):
        """
        Routes the incoming query to Neo4j or InfluxDB based on intent keywords.

        Intent A (Neo4j structural/semantic): keywords like "connected to", "on the same floor", "next to".
        Intent B (Time-series / InfluxDB): keywords like "temperature", "history", "value", "average".
        """
        q = natural_language_query.lower()
        structural_kw = ['connected to', 'on the same floor', 'next to', 'adjacent', 'connected']
        timeseries_kw = ['temperature', 'history', 'value', 'avg', 'average', 'min', 'max', 'reading']

        # Simple intent detection
        if any(kw in q for kw in structural_kw):
            # Ask the coder model to produce a Cypher query for the structural query
            prompt = (
                "You are an expert at writing Cypher queries for a Neo4j schema where rooms are labeled `Room` "
                "and have properties like `room_key`, `name`, `long_name`, `globalid`.\n"
                f"User request: {natural_language_query}\n"
                "Return ONLY the Cypher query (no explanation)."
            )
            cypher = self.ask_llm_for_query(prompt, model='qwen2.5-coder:1.5b')
            return self._run_cypher(cypher)

        if any(kw in q for kw in timeseries_kw):
            if not room_name:
                raise ValueError('room_name is required for time-series queries')

            # Step 1: semantic lookup - ask LLM to produce a Cypher query that finds room_key by room name
            prompt_room = (
                "Write a Cypher query that finds the Room.node property `room_key` given a room name. "
                "The database has nodes with label `Room` and properties `room_key`, `name`, `long_name`. "
                f"User-provided room name (may be in different languages): {room_name}\n"
                "Return ONLY the Cypher query; it should return the `room_key` property as `room_key`."
            )
            cypher_room = self.ask_llm_for_query(prompt_room, model='qwen2.5-coder:1.5b')
            rows = self._run_cypher(cypher_room)
            if not rows:
                raise RuntimeError('No room_key found for provided room name')
            # Expect first row to have room_key
            room_key = None
            if isinstance(rows[0], dict):
                # rows may be like { 'room_key': 'ifc_id_122131' }
                room_key = rows[0].get('room_key') or next(iter(rows[0].values()), None)

            if not room_key:
                raise RuntimeError('Could not extract room_key from Neo4j result')

            # Step 2: lookup sensor key in local config
            sensor_map = self.sensor_config.get('room_to_sensor_map', {})
            sensor_key = sensor_map.get(room_key)
            if not sensor_key:
                raise RuntimeError(f'No sensor mapping found for room_key {room_key}')

            # Step 3: ask LLM to produce a Flux query using the sensor_key and user's natural language constraints
            prompt_flux = (
                "You are a Flux query writer. The InfluxDB bucket is the environment variable `INFLUX_BUCKET`. "
                "Write a Flux query that retrieves measurements for the given sensor identifier. "
                "Use the variable `bucket` as the bucket name. Return only the Flux query.\n"
                f"Sensor identifier: {sensor_key}\n"
                f"User time constraint: {natural_language_query}\n"
                "Assume measurement field names are typical (e.g. `_value`) and include time."
            )

            flux_query = self.ask_llm_for_query(prompt_flux, model='qwen2.5-coder:1.5b')
            # Replace placeholder bucket if present
            if 'bucket' in flux_query and self.influx_bucket:
                flux_query = flux_query.replace('bucket', f'"{self.influx_bucket}"')

            return self._run_flux(flux_query)

        # Default: attempt to run a semantic lookup in Neo4j
        prompt_default = (
            "User query appears ambiguous. If this is asking about room relationships, return a Cypher query. "
            f"User: {natural_language_query}\nReturn only a Cypher query."
        )
        cypher = self.ask_llm_for_query(prompt_default, model='qwen2.5-coder:1.5b')
        return self._run_cypher(cypher)


if __name__ == '__main__':
    # Tiny interactive demo
    tool = LLMRouterTool()
    import sys

    if len(sys.argv) < 2:
        print('Usage: llm_router_tool.py "natural language query" [room_name]')
        sys.exit(1)

    q = sys.argv[1]
    room = sys.argv[2] if len(sys.argv) > 2 else None
    out = tool.ask_building_data(q, room)
    print(json.dumps(out, indent=2, ensure_ascii=False))
