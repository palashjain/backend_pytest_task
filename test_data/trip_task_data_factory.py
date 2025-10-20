from typing import Dict, Any, List
from datetime import datetime


class TripTaskDataFactory:
    
    @staticmethod
    def create_trip_data(shipment_ids: List[str], rider_id: int = 254, vehicle_id: int = 866) -> Dict[str, Any]:
        tasks = []
        
        for index, shipment_id in enumerate(shipment_ids):
            tasks.append({
                "index": index * 2,
                "job_id": int(shipment_id),
                "job_type": "shipment",
                "task_type": "pickup"
            })
            tasks.append({
                "index": index * 2 + 1,
                "job_id": int(shipment_id),
                "job_type": "shipment",
                "task_type": "drop"
            })
        
        trip_data = {
            "data": [
                {
                    "trip_index": 1,
                    "rider_id": rider_id,
                    "vehicle_id": vehicle_id,
                    "provisional_trip_id": "36b99ed9-ba95-4a7b-98d4-ffb7dcc152d2",
                    "tasks": tasks,
                    "estimated_distance": 55496,
                    "estimated_travel_time": 6020,
                    "route_polyline": None,
                    "merge_trips": True
                }
            ]
        }
        
        return trip_data
    
    @staticmethod
    def create_trip_status_data(trip_id: str, event: str = "start", 
                              latitude: float = 19.160079, longitude: float = 72.844977) -> Dict[str, Any]:
        trip_status_data = {
            "data": [
                {
                    "trip_id": int(trip_id),
                    "event": event,
                    "location": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "distance_covered": 4123,
                    "route_polyline": "abjkbhkajbkbbab000hhjhjbaj___cv"
                }
            ]
        }
        
        return trip_status_data
    
    @staticmethod
    def create_task_status_data(task_id: str, event: str, 
                              latitude: float = 18.93068, longitude: float = 72.83209,
                              notes: str = "Task completion notes") -> Dict[str, Any]:
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+04:00"
        
        task_status_data = {
            "data": [
                {
                    "event": event,
                    "event_time": current_time,
                    "image_filenames": [
                        "210912324-1760683341788.jpg"
                    ],
                    "location": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "notes": notes,
                    "task_id": int(task_id)
                }
            ]
        }
        
        return task_status_data
    
    @staticmethod
    def create_task_otp_data(latitude: float = 18.93068, longitude: float = 72.83209,
                           otp: str = "939345", task_action: str = "completion") -> Dict[str, Any]:
        otp_data = {
            "latitude": latitude,
            "longitude": longitude,
            "otp": otp,
            "task_action": task_action
        }
        
        return otp_data
