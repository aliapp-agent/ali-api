from typing import AsyncGenerator, Optional

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from asgiref.sync import sync_to_async
from openai import OpenAIError

from app.core.agno.tools import tools
from app.core.agno.tools.rag_search import rag_search_tool
from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import llm_inference_duration_seconds
from app.core.prompts import SYSTEM_PROMPT
from app.schemas import Message
from app.services.rag import RAGService
from app.shared.utils.graph import dump_messages

# Usar configuração do .env para o caminho do banco
db_file = settings.AGNO_MEMORY_PATH or "tmp/agent.db"

memory = Memory(
    model=OpenAIChat(
        id="gpt-4o-mini",
        api_key=settings.LLM_API_KEY,
        temperature=settings.DEFAULT_LLM_TEMPERATURE,
    ),
    db=SqliteMemoryDb(table_name="user_memories", db_file=db_file),
    delete_memories=False,  # Manter memórias para persistência
    clear_memories=False,  # Não limpar automaticamente
)

storage = SqliteStorage(table_name="agent_sessions", db_file=db_file)


class AgnoAgent:  # noqa: D101
    def __init__(self):  # noqa: D107
        self.tools = tools + [rag_search_tool]  # Adicionar RAG tool
        self.agent: Optional[Agent] = None
        self.rag_service = RAGService()

    async def initialize(self):
        """Inicializa o agente e o serviço RAG."""
        await self.rag_service.initialize_index()
        self._build_agent()

    def _build_agent(self):
        # Prompt atualizado para usar RAG
        enhanced_prompt = f"""
        {SYSTEM_PROMPT}
        
        ## Instruções RAG
        - Sempre que o usuário fizer uma pergunta, use a ferramenta 'rag_search' para buscar informações relevantes
        - Combine as informações encontradas com seu conhecimento para dar respostas mais precisas
        - Se não encontrar informações relevantes, informe ao usuário
        - Cite as fontes quando usar informações da base de conhecimento
        """

        self.agent = Agent(
            model=OpenAIChat(
                id=settings.LLM_MODEL,
                api_key=settings.LLM_API_KEY,
                temperature=settings.DEFAULT_LLM_TEMPERATURE,
            ),
            tools=self.tools,
            instructions=enhanced_prompt,
            description="Ali API Assistant com RAG - Assistente inteligente com acesso à base de conhecimento",
            memory=memory,
            storage=storage,
            add_history_to_messages=True,
            num_history_runs=3,
            enable_user_memories=True,
            markdown=True,
        )

    async def get_response(
        self,
        messages: list[Message],
        session_id: str,
        user_id: Optional[str] = None,
    ) -> list[dict]:
        """Get response from the agent for given messages."""
        if self.agent is None:
            self._build_agent()

        try:
            with llm_inference_duration_seconds.labels(
                model=self.agent.model
            ).time():
                response = await self.agent.arun(
                    messages=dump_messages(messages),
                    session_id=session_id,
                    user_id=user_id,
                )
            return self.__process_messages(response["messages"])
        except OpenAIError as e:
            logger.error("agno_llm_call_failed", error=str(e))
            raise

    async def get_stream_response(  # noqa: D102
        self,
        messages: list[Message],
        session_id: str,
        user_id: Optional[str] = None,
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

    async def get_chat_history(self, session_id: str) -> list[Message]:  # noqa: D102
        if self.agent is None:
            self._build_agent()

        memory = self.agent.memory
        if memory is None:
            return []

        messages = await sync_to_async(memory.load)(thread_id=session_id)
        return self.__process_messages(messages)

    async def clear_chat_history(self, session_id: str) -> None:  # noqa: D102
        if self.agent is None:
            self._build_agent()

        try:
            await self.agent.memory.aclear(thread_id=session_id)
        except Exception as e:
            logger.error("agno_clear_history_failed", error=str(e))
            raise

    async def health_check(self) -> dict:
        """Verifica se o agente está funcionando corretamente."""
        try:
            if self.agent is None:
                self._build_agent()

            # Teste simples
            await self.agent.arun(
                messages=[{"role": "user", "content": "Hello"}],
                session_id="health_check",
            )

            return {
                "status": "healthy",
                "agent_ready": True,
                "tools_count": len(self.tools),
                "memory_configured": self.agent.memory is not None,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "agent_ready": False,
            }

    def __process_messages(self, messages: list[dict]) -> list[Message]:
        processed = []
        for msg in messages:
            if msg.get("role") in ["assistant", "user"] and msg.get("content"):
                try:
                    processed.append(Message(**msg))
                except Exception as e:
                    logger.warning(f"Erro ao processar mensagem: {e}")
                    continue
        return processed
