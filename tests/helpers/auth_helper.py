from utils.auth_client import AuthClient
from utils.logger_utils import LoggerUtils


class AuthHelper:
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.auth_client = AuthClient(api_client)
        self.logger = LoggerUtils.get_logger(__name__)
    
    def authenticate_rider(self) -> str:
        self.logger.info("Authenticating as rider")
        
        self.api_client.clear_session()
        
        auth_data = self.auth_client.login_rider()
        
        if not auth_data.get("cookie") or not auth_data.get("workspace_id"):
            raise ValueError("Rider authentication failed: Missing cookie or workspace ID")
        
        workspace_auth_data = self.auth_client.workspace_login_rider(
            auth_data["workspace_id"], 
            auth_data["cookie"]
        )
        
        rider_cookie = workspace_auth_data["cookie"]
        self.logger.info("✅ Rider authentication successful")
        
        return rider_cookie
