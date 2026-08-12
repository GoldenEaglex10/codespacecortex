from __future__ import annotations

from dataclasses import dataclass
from typing import Any , Awaitable , Callable
ToolExecutor =  Callable[[dict[str, Any]] , Awaitable[Any]]



@dataclass
class ToolDefinition:
    """
    a single read only tool the tutor agent can call
    'input_schema' is what gets to the model(provider adapters translate this into whichever tool schema format that provider expects)
    """
    name:str
    description : str
    input_schema : dict[str , Any]
    executor : ToolExecutor


    def to_provider_schema(self) -> dict[str,Any]:
        return {
            "name":self.name,
            "description" : self.description,
            "input_schema" : self.input_schema
        }

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self ,  tool:ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self , name:str) -> ToolDefinition:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}'is not registered")
        return self._tools[name]

    def all(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def provider_schemas(self) -> list[dict[str , Any]]:
        return [t.to_provider_schema() for t in self._tools.values()]

    async def execute(self , name:str , tool_input:dict[str ,Any]) -> Any :
        tool = self.get(name)
        return await tool.executor(tool_input)

        


"""the lookup contract the other dev real search tool must satisfy
input {"query": str , "course_id":str | none}
output:list[{"content":str , "source":str, "score" : float}]"""

SEARCH_COURSE_CONTENT_SCHEMA = {
    "type": "object",
    "properties":{
        "query": {
            "type":"string",
            "description":"What the student is asking about , in plain terms",
        },
        "course_id":{
            "type":"string",
            "description": "The course to search within  , if known" , 
        } , 
         

    },
    "required":["query"],
}
def build_default_registry(search_executor : ToolExecutor) -> ToolRegistry:
    """wiring up the registry with whatever search implementation is passed in the real one """
    registry =  ToolRegistry()
    registry.register(
        ToolDefinition(
            name="search_course_content", 
            description=(
                "Search the student's course material for content relevant"
                "to their question . Use this before answering anything you"
                "are not certain is accurate for this specific course."
            ),
            input_schema=SEARCH_COURSE_CONTENT_SCHEMA,
            executor=search_executor
        )
    )
    return registry