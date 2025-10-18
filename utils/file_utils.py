import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Union
from config.configmanager import ConfigManager
from utils.base_utils import BaseClassUtils


class FileUtils(BaseClassUtils):
    _config_manager = ConfigManager()

    @classmethod
    def get_test_data_path(cls, file_name: str, file_type: str = "json") -> Path:
        test_data_dir = Path(cls._config_manager.test_data_dir)
        
        if file_type.lower() == "json":
            return test_data_dir / "json" / file_name
        elif file_type.lower() == "csv":
            return test_data_dir / "csv" / file_name
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @classmethod
    def load_test_data(cls, file_name: str, file_type: str = "json") -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        file_path = cls.get_test_data_path(file_name, file_type)
        
        if file_type.lower() == "json":
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    cls.get_logger().debug(f"Successfully read JSON file: {file_path}")
                    return data
            except Exception as e:
                cls.get_logger().error(f"Error reading JSON file {file_path}: {str(e)}")
                raise
        elif file_type.lower() == "csv":
            try:
                data = []
                with open(file_path, 'r', encoding='utf-8') as file:
                    csv_reader = csv.DictReader(file)
                    for row in csv_reader:
                        data.append(row)
                cls.get_logger().debug(f"Successfully read CSV file: {file_path}")
                return data
            except Exception as e:
                cls.get_logger().error(f"Error reading CSV file {file_path}: {str(e)}")
                raise
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    @classmethod
    def get_parametrize_data_from_csv(cls, csv_filename: str, columns: List[str] = None) -> List[tuple]:
        csv_path = cls.get_test_data_path(csv_filename, "csv")
        return cls._read_csv_for_parametrize(csv_path, columns)

    @classmethod
    def _read_csv_for_parametrize(cls, csv_path: Path, columns: List[str] = None) -> List[tuple]:
        try:
            if not csv_path.exists():
                raise FileNotFoundError(f"CSV file not found: {csv_path}")
            
            data = []
            with open(csv_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                
                if columns is None:
                    columns = csv_reader.fieldnames
                
                for row in csv_reader:
                    tuple_data = [cls._convert_csv_value(row.get(col, '')) for col in columns]
                    data.append(tuple(tuple_data))
            
            cls.get_logger().debug(f"Successfully read CSV file for parametrize: {csv_path}")
            return data
        except Exception as e:
            cls.get_logger().error(f"Error reading CSV file for parametrize {csv_path}: {str(e)}")
            raise

    @classmethod
    def _convert_csv_value(cls, value: str) -> Union[str, int, float]:
        if not value:
            return value
        
        try:
            if '.' not in value and 'e' not in value.lower():
                return int(value)
        except ValueError:
            pass
        
        try:
            return float(value)
        except ValueError:
            pass
        
        return value
