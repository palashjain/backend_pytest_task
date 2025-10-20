from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from utils.api_client import APIClient
from utils.auth_client import AuthClient
from utils.logger_utils import LoggerUtils


@dataclass
class SessionData:
    cookie: str
    workspace_id: str
    user_type: str
    login_response: Dict[str, Any]
    workspace_response: Dict[str, Any]
    
    def __post_init__(self):
        if not self.cookie or not self.workspace_id or not self.user_type:
            raise ValueError("Session data must contain cookie, workspace_id, and user_type")


class SessionManager:
    
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.auth_client = AuthClient(api_client)
        self.logger = LoggerUtils.get_logger(__name__)
        self._active_sessions: Dict[str, SessionData] = {}
    
    def create_session(self, user_type: str = "admin", 
                      username: Optional[str] = None, 
                      password: Optional[str] = None) -> SessionData:
        session_key = f"{user_type}_{id(self)}"
        
        try:
            self.logger.info(f"Creating {user_type} session...")
            
            self.api_client.clear_session()
            
            auth_data = self.auth_client.login(username, password, user_type)
            
            if not auth_data.get("cookie") or not auth_data.get("workspace_id"):
                raise ValueError(f"{user_type.title()} authentication failed: Missing cookie or workspace ID")
            
            workspace_auth_data = self.auth_client.workspace_login(
                auth_data["workspace_id"], 
                auth_data["cookie"],
                user_type
            )
            
            session_data = SessionData(
                cookie=workspace_auth_data["cookie"],
                workspace_id=auth_data["workspace_id"],
                user_type=user_type,
                login_response=auth_data["response_data"],
                workspace_response=workspace_auth_data["response_data"]
            )
            
            self._active_sessions[session_key] = session_data
            
            self.logger.info(f"✅ {user_type.title()} session created successfully")
            return session_data
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create {user_type} session: {str(e)}")
            raise
    
    def get_session(self, user_type: str = "admin") -> Optional[SessionData]:
        session_key = f"{user_type}_{id(self)}"
        return self._active_sessions.get(session_key)
    
    def logout_session(self, user_type: str = "admin") -> bool:
        session_key = f"{user_type}_{id(self)}"
        session_data = self._active_sessions.get(session_key)
        
        if not session_data:
            self.logger.warning(f"No active {user_type} session found to logout")
            return False
        
        try:
            self.logger.info(f"Logging out {user_type} session...")
            
            if user_type == "rider":
                self.auth_client.logout_rider(session_data.cookie)
            else:
                self.auth_client.logout(session_data.cookie)
            
            del self._active_sessions[session_key]
            
            self.logger.info(f"✅ {user_type.title()} logout completed successfully")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️  {user_type.title()} logout failed: {str(e)}")
            return False
    
    def is_session_active(self, user_type: str = "admin") -> bool:
        return self.get_session(user_type) is not None
