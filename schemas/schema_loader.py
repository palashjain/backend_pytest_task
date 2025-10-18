import json
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logger_utils import LoggerUtils


class SchemaLoader:
    _logger = LoggerUtils.get_logger(__name__)
    _schemas_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load_schema(cls, schema_name: str) -> Dict[str, Any]:
        if schema_name in cls._schemas_cache:
            cls._logger.debug(f"Loading schema '{schema_name}' from cache")
            return cls._schemas_cache[schema_name]
        
        schema_path = Path(__file__).parent / f"{schema_name}.json"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as file:
                schema = json.load(file)
                cls._schemas_cache[schema_name] = schema
                cls._logger.info(f"Successfully loaded schema: {schema_name}")
                return schema
                
        except json.JSONDecodeError as e:
            cls._logger.error(f"Invalid JSON in schema file {schema_path}: {str(e)}")
            raise
        except Exception as e:
            cls._logger.error(f"Error loading schema {schema_name}: {str(e)}")
            raise

    @classmethod
    def get_shipment_schema(cls) -> Dict[str, Any]:
        return cls.load_schema("create_shipment_schema")
    
    @classmethod
    def get_schema_by_name(cls, schema_name: str) -> Dict[str, Any]:
        return cls.load_schema(schema_name)

    @classmethod
    def clear_cache(cls) -> None:
        cls._schemas_cache.clear()
        cls._logger.debug("Schema cache cleared")

    @classmethod
    def list_available_schemas(cls) -> list:
        schemas_dir = Path(__file__).parent
        schema_files = list(schemas_dir.glob("*.json"))
        schema_names = [f.stem for f in schema_files]
        cls._logger.debug(f"Available schemas: {schema_names}")
        return schema_names
