# This file is a draft migration of the LangGraphAgent class to use Agno instead of LangGraph

from typing import Optional, AsyncGenerator
from openai import OpenAIError
from asgiref.sync import sync_to_async
from app.core.config import settings, Environment
from app.core.logging import logger
from app.core.prompts import SYSTEM_PROMPT
from app.core.metrics import llm_inference_duration_seconds
from app.core.langgraph.tools import tools
from app.schemas import Message
from app.utils import dump_messages, prepare_messages
from agno.agents import Agent
from agno.schema import ToolCall, ToolResponse
from agno.memory.postgres import PostgresMemory
from agno.callbacks.langfuse import LangfuseCallback


class AgnoAgent:
    def __init__(self):
        self.tools = tools
        self.agent: Optional[Agent] = None

    def _build_agent(self):
        memory = PostgresMemory(  # Optional: you can disable or mock this for dev
            postgres_url=settings.POSTGRES_URL,
            tables=settings.CHECKPOINT_TABLES
        )

        self.agent = Agent(
            model=settings.LLM_MODEL,
            tools=self.tools,
            memory=memory,
            config={
                "temperature": settings.DEFAULT_LLM_TEMPERATURE,
                "top_p": 0.95 if settings.ENVIRONMENT == Environment.PRODUCTION else 0.8,
                "presence_penalty": 0.1,
                "frequency_penalty": 0.1,
                "max_tokens": settings.MAX_TOKENS,
            },
            callbacks=[LangfuseCallback(environment=settings.ENVIRONMENT.value)],
        )

    async def get_response(self, messages: list[Message], session_id: str, user_id: Optional[str] = None) -> list[dict]:
        if self.agent is None:
            self._build_agent()

        try:
            with llm_inference_duration_seconds.labels(model=self.agent.model).time():
                response = await self.agent.arun(
                    messages=dump_messages(messages),
                    session_id=session_id,
                    user_id=user_id,
                )
            return self.__process_messages(response["messages"])
        except OpenAIError as e:
            logger.error("agno_llm_call_failed", error=str(e))
            raise

    async def get_stream_response(
        self, messages: list[Message], session_id: str, user_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        if self.agent is None:
            self._build_agent()

        try:
            async for token in self.agent.astream(
                messages=dump_messages(messages),
                session_id=session_id,
                user_id=user_id,
                stream_mode="messages",
            ):
                yield token.content
        except Exception as e:
            logger.error("agno_streaming_failed", error=str(e))
            raise

    async def get_chat_history(self, session_id: str) -> list[Message]:
        if self.agent is None:
            self._build_agent()

        memory = self.agent.memory
        if memory is None:
            return []

        messages = await sync_to_async(memory.load)(thread_id=session_id)
        return self.__process_messages(messages)

    async def clear_chat_history(self, session_id: str) -> None:
        if self.agent is None:
            self._build_agent()

        try:
            await self.agent.memory.aclear(thread_id=session_id)
        except Exception as e:
            logger.error("agno_clear_history_failed", error=str(e))
            raise

    def __process_messages(self, messages: list[dict]) -> list[Message]:
        return [
            Message(**msg) for msg in messages if msg["role"] in ["assistant", "user"] and msg["content"]
        ]