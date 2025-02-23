from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

def custom_openapi() -> Dict[str, Any]:
    """Customize OpenAPI documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Movie Generator API",
        version="0.1.0",
        description="""
        The Movie Generator API provides endpoints for automated movie generation using a multi-agent system.
        
        ## Authentication
        
        This API supports two authentication methods:
        - OAuth2 with JWT tokens
        - API Key authentication
        
        ## WebSocket Support
        
        Real-time updates are available through WebSocket connections:
        - `/ws/projects/{project_id}` - Project-specific updates
        - `/ws/system` - System metrics updates
        
        ## Rate Limits
        
        - 100 requests per minute for authenticated users
        - 1000 requests per day for free tier
        """,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "token",
                    "scopes": {
                        "read": "Read access",
                        "write": "Write access"
                    }
                }
            }
        },
        "APIKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    }
    
    # Add security requirement to all operations
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [
                {"OAuth2": ["read", "write"]},
                {"APIKey": []}
            ]
    
    # Add custom examples
    openapi_schema["components"]["examples"] = {
        "ProjectCreate": {
            "value": {
                "title": "Forest Adventure",
                "description": "A short animated story about woodland creatures",
                "type": "animation",
                "requirements": {
                    "style": "animated",
                    "duration": 60,
                    "target_audience": "children",
                    "theme": "nature",
                    "mood": "cheerful"
                }
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Update main.py to use custom OpenAPI schema
app.openapi = custom_openapi 