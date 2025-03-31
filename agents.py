import requests

ELIZAOS_API_ENDPOINT = "http://localhost:8000/elizaOS-eliza"
TRON_API_ENDPOINT = "http://localhost:8000/elizaOS-eliza"
GOOSE_API_ENDPOINT = "http://localhost:8000/block-goose"

# API keys for the framework endpoints
ELIZAOS_API_KEY = "your-elizaos-api-key-here"
TRON_API_KEY = "your-tron-api-key-here"
GOOSE_API_KEY = "your-goose-api-key-here"

class BaseAgent:
    def __init__(self, api_endpoint: str, api_key: str):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
        
    def process(self, query: str) -> dict:
        """Send query to API and get response"""
        try:
            headers = {
                # "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {"query": query}
            response = requests.post(self.api_endpoint, headers=headers, json=payload)
            response.raise_for_status()
            return {"success": True, "result": response.json()["result"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

class ElizaOSAgent(BaseAgent):
    def __init__(self):
        super().__init__(ELIZAOS_API_ENDPOINT, ELIZAOS_API_KEY)

class TronAgent(BaseAgent):
    def __init__(self):
        super().__init__(TRON_API_ENDPOINT, TRON_API_KEY)

class GooseAgent(BaseAgent):
    def __init__(self):
        super().__init__(GOOSE_API_ENDPOINT, GOOSE_API_KEY)