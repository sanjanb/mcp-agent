"""
MCP Server for HR Agent Tools.
Orchestrates multiple MCP tools and provides a unified interface.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
import os

# Add tools to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPServer:
    """Model Context Protocol Server for HR Agent Tools."""
    
    def __init__(self, host: str = "localhost", port: int = 8000):
        """
        Initialize the MCP Server.
        
        Args:
            host: Server host address
            port: Server port number
        """
        self.host = host
        self.port = port
        self.tools = {}
        self.audit_log = []
        
        # Register all available tools
        self._register_tools()
        
        logger.info(f"MCP Server initialized with {len(self.tools)} tools")
    
    def _register_tools(self):
        """Register all MCP tools with graceful degradation on import failure."""
        # Attempt to load HR Policy RAG tools
        try:
            from tools.policy_rag.mcp_tool import MCP_TOOLS as POLICY_TOOLS  # type: ignore
            for tool_name, tool_config in POLICY_TOOLS.items():
                self.tools[tool_name] = tool_config
                logger.info(f"Registered tool: {tool_name}")
        except Exception as e:
            logger.warning(f"Policy RAG tools not loaded: {e}")

        # Attempt to load Onboarding tools
        try:
            from tools.onboarding.mcp_tool import MCP_TOOLS as ONBOARDING_TOOLS  # type: ignore
            for tool_name, tool_config in ONBOARDING_TOOLS.items():
                if tool_name in self.tools:
                    logger.warning(f"Tool name conflict: {tool_name} already registered; skipping onboarding duplicate")
                    continue
                self.tools[tool_name] = tool_config
                logger.info(f"Registered tool: {tool_name}")
        except Exception as e:
            logger.warning(f"Onboarding tools not loaded: {e}")
    
    def get_tool_manifest(self) -> Dict[str, Any]:
        """
        Get the manifest of all available tools.
        
        Returns:
            Dictionary containing tool manifest
        """
        manifest = {
            "server_info": {
                "name": "HR Agent MCP Server",
                "version": "1.0.0",
                "description": "MCP Server for HR Assistant Agent tools",
                "host": self.host,
                "port": self.port
            },
            "tools": {}
        }
        
        for tool_name, tool_config in self.tools.items():
            manifest["tools"][tool_name] = {
                "description": tool_config["description"],
                "parameters": tool_config["parameters"]
            }
        
        return manifest
    
    def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a specific tool with given parameters.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Parameters to pass to the tool
            
        Returns:
            Tool execution result
        """
        call_id = f"call_{len(self.audit_log) + 1}"
        logger.info(f"Tool call {call_id}: {tool_name} with params {parameters}")
        
        # Log the call
        audit_entry = {
            "call_id": call_id,
            "tool_name": tool_name,
            "parameters": parameters,
            "timestamp": logger.handlers[0].formatter.formatTime(logger.handlers[0].record) if logger.handlers else "unknown"
        }
        
        try:
            # Validate tool exists
            if tool_name not in self.tools:
                error_msg = f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"
                logger.error(error_msg)
                audit_entry["status"] = "error"
                audit_entry["error"] = error_msg
                self.audit_log.append(audit_entry)
                return {
                    "success": False,
                    "error": error_msg,
                    "call_id": call_id
                }
            
            # Get tool function
            tool_function = self.tools[tool_name]["function"]
            
            # Call tool function
            if parameters:
                result = tool_function(**parameters)
            else:
                result = tool_function()
            
            # Parse JSON result if it's a string
            if isinstance(result, str):
                try:
                    parsed_result = json.loads(result)
                    result = parsed_result
                except json.JSONDecodeError:
                    # Keep as string if not valid JSON
                    pass
            
            # Log successful call
            audit_entry["status"] = "success"
            audit_entry["result_size"] = len(str(result))
            self.audit_log.append(audit_entry)
            
            logger.info(f"Tool call {call_id} completed successfully")
            
            return {
                "success": True,
                "result": result,
                "call_id": call_id,
                "tool_name": tool_name
            }
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            logger.error(f"Tool call {call_id} failed: {error_msg}")
            
            audit_entry["status"] = "error"
            audit_entry["error"] = error_msg
            self.audit_log.append(audit_entry)
            
            return {
                "success": False,
                "error": error_msg,
                "call_id": call_id,
                "tool_name": tool_name
            }
    
    def get_audit_log(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent audit log entries.
        
        Args:
            last_n: Number of recent entries to return
            
        Returns:
            List of recent audit log entries
        """
        return self.audit_log[-last_n:] if self.audit_log else []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform server health check.
        
        Returns:
            Health status information
        """
        try:
            # Test each tool
            tool_status = {}
            for tool_name in self.tools.keys():
                try:
                    # Try a simple call to test if tool is responsive
                    if tool_name == "policy_search":
                        test_result = self.call_tool(tool_name, {"query": "test", "top_k": 1})
                        tool_status[tool_name] = "healthy" if test_result["success"] else "error"
                    elif tool_name == "get_policy_stats":
                        test_result = self.call_tool(tool_name, {})
                        tool_status[tool_name] = "healthy" if test_result["success"] else "error"
                    else:
                        tool_status[tool_name] = "unknown"
                except Exception:
                    tool_status[tool_name] = "error"
            
            return {
                "server_status": "healthy",
                "total_tools": len(self.tools),
                "total_calls": len(self.audit_log),
                "tool_status": tool_status,
                "host": self.host,
                "port": self.port
            }
            
        except Exception as e:
            return {
                "server_status": "error",
                "error": str(e)
            }


class MCPRouter:
    """Routes MCP calls and handles authentication/authorization."""
    
    def __init__(self, server: MCPServer):
        """
        Initialize the router.
        
        Args:
            server: MCP Server instance
        """
        self.server = server
        logger.info("MCP Router initialized")
    
    def authenticate(self, auth_token: Optional[str] = None) -> bool:
        """
        Authenticate user (simplified for MVP).
        
        Args:
            auth_token: Authentication token
            
        Returns:
            True if authenticated, False otherwise
        """
        # For MVP, allow all requests
        # In production, implement proper authentication
        return True
    
    def authorize(self, user_id: Optional[str], tool_name: str) -> bool:
        """
        Authorize user for specific tool (simplified for MVP).
        
        Args:
            user_id: User identifier
            tool_name: Name of the tool being accessed
            
        Returns:
            True if authorized, False otherwise
        """
        # For MVP, allow all tools for all users
        # In production, implement RBAC
        return True
    
    def route_call(
        self, 
        tool_name: str, 
        parameters: Dict[str, Any], 
        auth_token: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Route and execute a tool call with authentication.
        
        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters
            auth_token: Authentication token
            user_id: User identifier
            
        Returns:
            Tool execution result with routing metadata
        """
        logger.info(f"Routing call: {tool_name} for user {user_id}")
        
        # Authenticate
        if not self.authenticate(auth_token):
            return {
                "success": False,
                "error": "Authentication failed",
                "tool_name": tool_name
            }
        
        # Authorize
        if not self.authorize(user_id, tool_name):
            return {
                "success": False,
                "error": f"User {user_id} not authorized for tool {tool_name}",
                "tool_name": tool_name
            }
        
        # Route to server
        result = self.server.call_tool(tool_name, parameters)
        
        # Add routing metadata
        result["routed_by"] = "MCP Router"
        result["user_id"] = user_id
        
        return result


# Example usage and testing
if __name__ == "__main__":
    print("\n=== MCP Server Test ===")
    
    # Initialize server and router
    server = MCPServer()
    router = MCPRouter(server)
    
    # Show manifest
    print("\n--- Tool Manifest ---")
    manifest = server.get_tool_manifest()
    print(json.dumps(manifest, indent=2))
    
    # Health check
    print("\n--- Health Check ---")
    health = server.health_check()
    print(json.dumps(health, indent=2))
    
    # Test tool calls
    print("\n--- Tool Call Tests ---")
    
    test_calls = [
        {
            "tool": "get_policy_stats",
            "params": {}
        },
        {
            "tool": "policy_search",
            "params": {"query": "vacation policy", "top_k": 2}
        }
    ]
    
    for i, test_call in enumerate(test_calls, 1):
        print(f"\nTest {i}: {test_call['tool']}")
        result = router.route_call(
            test_call["tool"], 
            test_call["params"],
            user_id="test_user"
        )
        
        if result["success"]:
            print(f"✓ Success: {test_call['tool']} completed")
            if "result" in result:
                print(f"  Result: {str(result['result'])[:200]}...")
        else:
            print(f"✗ Failed: {result.get('error', 'Unknown error')}")
    
    # Show audit log
    print("\n--- Recent Audit Log ---")
    audit_log = server.get_audit_log(5)
    for entry in audit_log:
        print(f"  {entry['call_id']}: {entry['tool_name']} - {entry['status']}")
    
    print(f"\nMCP Server ready on {server.host}:{server.port}")
    print(f"Total tools available: {len(server.tools)}")
    print(f"Tools: {', '.join(server.tools.keys())}")