#/tutor-service/agents/agents.py the core tutor loop
from  __future__ import annotations
from dataclasses import dataclass
from agents.tutor.pedagogy import enforce_pedagogy
from agents.tutor.prompts import build_system_prompt
from context_engine.build_context import StudentContext
from context_engine.tool_registry import ToolRegistry
from llm.provider import LLMProvider , ToolCall

MAX_TOOL_ITERATIONS = 3

@dataclass

class TutorReplay:

    text: str
    tools_used  : list[str]


class TutorAgent:
    def __init__(self , provider: LLMProvider , tool_registry: ToolRegistry):
        self.provider = provider
        self.tool_registry = tool_registry

    async def respond(self , * ,  question:str , context:StudentContext) -> TutorReplay:
        system = build_system_prompt(context=context)
        messages : list[dict] = [{"role":"user" , "content":question}]
        tools_used =  list[str] =  []
        response = None


        for _ in range(MAX_TOOL_ITERATIONS):
            response = await self.provider.complete(system=system , messages=messages , tools=self.tool_registry.get_tools())
            if not response.wants_tool_call:
                final_text = enforce_pedagogy(response.text , context=context)
                return TutorReplay(text=final_text , tools_used=tools_used)


        #models wants to call one or more models
        messages.append({"role":"assistant" , "content":response.text or ""})
        for call in response.tool_calls:
            tools_used.append(call.tool_name)
            result = await self._run_tool_call(call=call , context=context)
            messages.append({"role":"user" ,  "content":f"Tool {call.tool_name} returned: {result}"})


        """ ran out of tool call iterations  return the last response  or the whatever text we have
        still pedagogy checked rather than looping forever"""
        fallback_text = (response.text if response else "") or ("I wasn't able to fully answer that could you rephrase")
        final_text =  enforce_pedagogy(fallback_text , context=context)
        return TutorReplay(text=final_text , tools_used=tools_used)


    async def _run_tool(self , call :ToolCall) -> str:
        try :  

            result = await self.tool_registry.run_tool(call.name  , call.input)
            return result
        except Exception as e:
            return f"Error running tool {call.name} : {str(e)}"