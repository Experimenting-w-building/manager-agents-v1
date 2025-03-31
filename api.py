from fastapi import FastAPI
from pydantic import BaseModel

from main import query_manager_agent

# Initialize FastAPI app
app = FastAPI()

# Sample data model
class Query(BaseModel):
    query: str


@app.post("/query")
async def get_items(req: Query):
    result = await query_manager_agent(req.query)
    return {"result": result}
