import json
import re
from typing import Union

from langchain_core.agents import AgentAction, AgentActionMessageLog, AgentFinish
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.outputs import ChatGeneration, Generation


class FunctionCallAgentOutputParser(BaseOutputParser):
    def _parse_ai_message(
        self, message: BaseMessage
    ) -> Union[AgentAction, AgentFinish]:
        content = str(message.content)
        return self._parse_ai_text(content)

    def _parse_ai_text(self, text: str) -> Union[AgentAction, AgentFinish]:
        pattern = r'\{\s*"function_call":\s*\{.*?\}\s*\}\s*\}'
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            function_call = json.loads(matches[0])["function_call"]
            function_name = function_call["name"]
            tool_input = function_call["arguments"]
            content_msg = f"responded: {text}\n" if text else "\n"
            log = f"\nInvoking: `{function_name}` with `{tool_input}`\n{content_msg}\n"
            result = AgentActionMessageLog(
                tool=function_name,
                tool_input=tool_input,
                log=log,
                message_log=[AIMessage(content=text)],
            )

        else:
            result = AgentFinish(return_values={"output": text}, log=str(text))

        return result

    def parse_result(
        self, result: list[Generation], *, partial: bool = False
    ) -> Union[AgentAction, AgentFinish]:
        if isinstance(result[0], ChatGeneration):
            message = result[0].message
            return self._parse_ai_message(message)
        if isinstance(result[0], Generation):
            return self._parse_ai_text(result[0].text)

        raise ValueError(
            f"This output parser only works on ChatGeneration or Generation output (got {type(result[0])})"
        )

    def parse(self, _: str) -> Union[AgentAction, AgentFinish]:
        raise ValueError("Can only parse messages")
