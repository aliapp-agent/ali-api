"""Agno Agent configuration and main class for AI interactions."""

from typing import (
    Any,
    AsyncGenerator,
    Dict,
    List,
    Optional,
)

from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.openai import OpenAIChat
from agno.storage.sqlite import SqliteStorage
from asgiref.sync import sync_to_async
from openai import OpenAIError

from app.core.agno.tools.rag_search import rag_search_tool
from app.core.agno.tools.whatsapp_tool import whatsapp_tool
from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import llm_inference_duration_seconds
from app.core.prompts import SYSTEM_PROMPT
from app.schemas import Message
from app.services import get_rag_service
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
        self.tools = [rag_search_tool, whatsapp_tool]  # Adicionar RAG tool e WhatsApp tool
        self.agent: Optional[Agent] = None
        self.rag_service = None  # Lazy initialization

    async def initialize(self):
        """Inicializa o agente e o serviço RAG."""
        self.rag_service = get_rag_service()
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

        try:
            self.agent = Agent(
                model=OpenAIChat(
                    id=settings.LLM_MODEL,
                    api_key=settings.LLM_API_KEY,
                    temperature=settings.DEFAULT_LLM_TEMPERATURE,
                ),
                tools=self.tools,  # type: ignore
                instructions=enhanced_prompt,
                description="Ali API Assistant com RAG - Assistente inteligente com acesso à base de conhecimento",
                memory=memory,
                storage=storage,
                add_history_to_messages=True,
                num_history_runs=3,
                enable_user_memories=True,
                markdown=True,
            )
        except Exception as e:
            logger.error("failed_to_build_agent", error=str(e))
            self.agent = None

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
            if self.agent and hasattr(self.agent, 'model'):
                with llm_inference_duration_seconds.labels(model=str(self.agent.model)).time():
                    response = await self.agent.arun(
                        messages=dump_messages(messages),
                        session_id=session_id,
                        user_id=user_id,
                    )
                return self.__process_messages(response.messages)
            else:
                logger.error("agent_not_available")
                return []
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
            if self.agent and hasattr(self.agent, 'arun'):
                # Use regular run since astream might not be available
                response = await self.agent.arun(
                    messages=dump_messages(messages),
                    session_id=session_id,
                    user_id=user_id,
                )
                # Yield the complete response
                for msg in response.messages:
                    if hasattr(msg, 'content'):
                        yield str(msg.content)
            else:
                logger.error("agent_not_available_for_streaming")
                yield "Desculpe, o agente não está disponível no momento."
        except Exception as e:
            logger.error("agno_streaming_failed", error=str(e))
            raise

    async def get_chat_history(self, session_id: str) -> list[Message]:  # noqa: D102
        if self.agent is None:
            self._build_agent()

        if self.agent and hasattr(self.agent, 'memory') and self.agent.memory:
            try:
                messages = await sync_to_async(lambda: [])(thread_id=session_id)  # Placeholder
                return self.__process_messages(messages)
            except Exception as e:
                logger.error("failed_to_load_chat_history", error=str(e))
                return []
        return []

    async def clear_chat_history(self, session_id: str) -> None:  # noqa: D102
        if self.agent is None:
            self._build_agent()

        try:
            if self.agent and hasattr(self.agent, 'memory') and self.agent.memory:
                # Use sync version since aclear might not exist
                await sync_to_async(lambda: None)(thread_id=session_id)  # Placeholder
        except Exception as e:
            logger.error("agno_clear_history_failed", error=str(e))
            raise

    async def process_message(
        self,
        message: str,
        session_id: str,
        metadata: Optional[dict] = None
    ) -> dict:
        """Processa mensagem única para WhatsApp.

        Args:
            message: Mensagem do usuário
            session_id: ID da sessão (ex: whatsapp_5511999999999)
            metadata: Metadados adicionais (source, phone_number, etc.)

        Returns:
            dict: Resposta processada com metadata
        """
        if self.agent is None:
            self._build_agent()

        try:
            # Criar mensagem no formato esperado
            user_message = Message(role="user", content=message)

            logger.info(
                "processing_whatsapp_message_with_agno",
                session_id=session_id,
                message_preview=message[:100] + "..." if len(message) > 100 else message,
                metadata=metadata or {}
            )

            # Processar com o agente
            if self.agent and hasattr(self.agent, 'model'):
                with llm_inference_duration_seconds.labels(model=str(self.agent.model)).time():
                    response = await self.agent.arun(
                        messages=[user_message.model_dump()],
                        session_id=session_id,
                        user_id=metadata.get('phone_number') if metadata else None,
                    )
            else:
                logger.error("agent_not_available_for_processing")
                return {
                    'response': 'Desculpe, o sistema não está disponível no momento.',
                    'session_id': session_id,
                    'error': 'Agent not available',
                    'metadata': metadata or {}
                }

            # Processar resposta
            processed_messages = self.__process_messages(response.messages)

            # Extrair última resposta do assistente
            assistant_response = ""
            for msg in processed_messages:
                if isinstance(msg, dict) and msg.get('role') == 'assistant':
                    assistant_response = msg.get('content', '')
                elif hasattr(msg, 'role') and msg.role == 'assistant':
                    assistant_response = getattr(msg, 'content', '')

            result = {
                'response': assistant_response,
                'session_id': session_id,
                'processed_messages': len(processed_messages),
                'metadata': metadata or {},
                'tools_used': self._extract_tool_calls(response.messages)
            }

            logger.info(
                "whatsapp_message_processed_successfully",
                session_id=session_id,
                response_length=len(assistant_response),
                tools_used=result['tools_used']
            )

            return result

        except Exception as e:
            logger.error(
                "error_processing_whatsapp_message",
                session_id=session_id,
                error=str(e),
                exc_info=True
            )
            # Retornar resposta de erro amigável
            return {
                'response': 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.',
                'session_id': session_id,
                'error': str(e),
                'metadata': metadata or {}
            }

    def _extract_tool_calls(self, messages: list) -> list[str]:
        """Extrai nomes das ferramentas chamadas nas mensagens."""
        tools_used = []
        for message in messages:
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    if hasattr(tool_call, 'function') and tool_call.function:
                        tools_used.append(str(tool_call.function.name))
        return tools_used

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

    def __process_messages(self, messages: list) -> list[Message]:
        processed = []
        for msg in messages:
            try:
                # Handle both dict and Agno Message objects
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    # It's an Agno Message object
                    if msg.role in ["assistant", "user"] and msg.content:
                        processed.append(Message(role=msg.role, content=msg.content))
                elif isinstance(msg, dict):
                    # It's a dictionary
                    if msg.get("role") in ["assistant", "user"] and msg.get("content"):
                        processed.append(Message(**msg))
            except Exception as e:
                logger.warning(f"Erro ao processar mensagem: {e}")
                continue
        return processed
