"""Implementação otimizada do AgnoAgent seguindo as melhores práticas da documentação oficial.

Este módulo implementa um agente de IA baseado no framework Agno com:
- Configuração correta de memória e storage
- Ferramentas customizadas seguindo padrões do Agno
- Tratamento robusto de erros com fallbacks
- Configurações otimizadas para performance
- Observabilidade e debugging aprimorados
"""

import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncGenerator
from datetime import datetime
import asyncio

# Agno imports - seguindo documentação oficial
from agno.agent import Agent
from agno.memory.v2.memory import Memory
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.storage.sqlite import SqliteStorage
from agno.models.openai import OpenAIChat
from agno.tools import Function, Toolkit

# Imports locais
from app.core.config import settings
from qdrant_client import QdrantClient
from app.services.whatsapp.client import WhatsAppClient

logger = logging.getLogger(__name__)

# Import condicional do Groq
try:
    from agno.models.groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    logger.warning("Groq não disponível. Usando apenas OpenAI.")
    Groq = None
    GROQ_AVAILABLE = False

# Configurações de paths
BASE_DIR = Path(__file__).parent.parent.parent.parent
MEMORY_DB_PATH = BASE_DIR / "data" / "agno_memory.db"
STORAGE_DB_PATH = BASE_DIR / "data" / "agno_storage.db"

# Garantir que o diretório data existe
MEMORY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class RAGSearchTool(Function):
    """Ferramenta de busca RAG seguindo padrões do Agno."""
    
    def __init__(self, qdrant_client, collection_name: str = "documents"):
        """Inicializa a ferramenta RAG.
        
        Args:
            qdrant_client: Cliente Qdrant configurado
            collection_name: Nome da collection no Qdrant
        """
        super().__init__(
            name="rag_search",
            description="Busca informações na base de conhecimento usando RAG"
        )
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.embedding_model = None
        
        # Inicializar modelo de embedding se disponível
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Modelo de embedding carregado")
        except ImportError:
            logger.warning("sentence-transformers não disponível")
    
    def run(self, query: str, limit: int = 5) -> str:
        """Executa busca RAG.
        
        Args:
            query: Consulta de busca
            limit: Número máximo de resultados
            
        Returns:
            Resultados da busca formatados
        """
        try:
            if not self.embedding_model:
                return "Modelo de embedding não disponível"
            
            # Gerar embedding da query
            query_vector = self.embedding_model.encode(query).tolist()
            
            # Buscar no Qdrant
            results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            
            if not results:
                return "Nenhum resultado encontrado"
            
            # Formatar resultados
            formatted_results = []
            for result in results:
                payload = result.payload or {}
                formatted_results.append(
                    f"Score: {result.score:.3f} - {payload.get('content', 'Sem conteúdo')}"
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            logger.error(f"Erro na busca RAG: {e}")
            return f"Erro na busca: {str(e)}"


class WhatsAppTool(Function):
    """Ferramenta de integração WhatsApp seguindo padrões do Agno."""
    
    def __init__(self, whatsapp_client: WhatsAppClient):
        super().__init__(
            name="whatsapp_integration",
            description="Integração com WhatsApp para envio de mensagens"
        )
        self.whatsapp_client = whatsapp_client
    
    def run(self, action: str, **kwargs) -> str:
        """Executa ações do WhatsApp.
        
        Args:
            action: Ação a ser executada (send_message, get_status, etc.)
            **kwargs: Parâmetros específicos da ação
            
        Returns:
            Resultado da ação formatado
        """
        try:
            if action == "send_message":
                result = self.whatsapp_client.send_message(
                    phone_number=kwargs.get("phone_number"),
                    message=kwargs.get("message")
                )
                return f"Mensagem enviada com sucesso: {result}"
            elif action == "get_status":
                result = self.whatsapp_client.get_status()
                return f"Status do WhatsApp: {result}"
            else:
                return f"Ação não suportada: {action}"
            
        except Exception as e:
            logger.error(f"Erro na integração WhatsApp: {e}")
            return f"Erro na integração WhatsApp: {str(e)}"


class OptimizedAgnoAgent:
    """Agente Agno otimizado seguindo melhores práticas da documentação oficial."""
    
    def __init__(self, session_id: str = "default_session"):
        self.session_id = session_id
        self.agent: Optional[Agent] = None
        self.memory: Optional[Memory] = None
        self.storage: Optional[SqliteStorage] = None
        self.tools: List[Function] = []
        
        # Inicializar componentes
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Inicializa todos os componentes do agente com tratamento robusto de erros."""
        try:
            self._setup_memory()
            self._setup_storage()
            self._setup_tools()
            self._create_agent()
            
            logger.info("AgnoAgent inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Falha na inicialização completa: {e}")
            self._create_fallback_agent()
    
    def _setup_memory(self) -> None:
        """Configura memória otimizada seguindo padrões oficiais do Agno."""
        try:
            # Modelo para criação de memórias (modelo mais barato e rápido)
            memory_model = OpenAIChat(id="gpt-4o-mini")
            
            # Database de memória
            memory_db = SqliteMemoryDb(
                table_name="user_memories",
                db_file=str(MEMORY_DB_PATH)
            )
            
            # Configuração otimizada da memória
            self.memory = Memory(
                model=memory_model,
                db=memory_db,
                # Configurações de performance
                create_user_memories=True,
                update_user_memories=True,
                # Limitar número de memórias para performance
                num_memories=50
            )
            
            logger.info("Memória otimizada configurada com sucesso")
            
        except Exception as e:
            logger.error(f"Erro na configuração da memória: {e}")
            # Fallback: memória básica sem persistência
            try:
                # Garantir que OPENAI_API_KEY está configurada
                if settings.LLM_API_KEY:
                    os.environ["OPENAI_API_KEY"] = settings.LLM_API_KEY
                
                self.memory = Memory(
                    model=OpenAIChat(
                        id="gpt-4o-mini",
                        api_key=settings.LLM_API_KEY if settings.LLM_API_KEY else None
                    )
                )
                logger.warning("Usando memória básica como fallback")
            except Exception as fallback_error:
                logger.error(f"Falha no fallback de memória: {fallback_error}")
                self.memory = None
    
    def _setup_storage(self) -> None:
        """Configura storage otimizado para persistência de sessões."""
        try:
            self.storage = SqliteStorage(
                table_name="agent_sessions",
                db_file=str(STORAGE_DB_PATH)
            )
            
            # Configurar índices para melhor performance
            self._optimize_storage_indexes()
            
            logger.info("Storage otimizado configurado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro na configuração do storage: {e}")
            # Fallback: storage em memória temporário
            try:
                from agno.storage.memory import MemoryStorage
                self.storage = MemoryStorage()
                logger.warning("Usando storage em memória como fallback")
            except Exception as fallback_error:
                logger.error(f"Falha no fallback de storage: {fallback_error}")
                self.storage = None
    
    def _optimize_storage_indexes(self) -> None:
        """Otimiza índices do storage para melhor performance."""
        try:
            if self.storage and hasattr(self.storage, 'db'):
                # Criar índices para consultas frequentes
                db = self.storage.db
                if hasattr(db, 'execute'):
                    # Índice para session_id (consultas por sessão)
                    db.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON agent_sessions(session_id)")
                    # Índice para timestamp (consultas por data)
                    db.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON agent_sessions(created_at)")
                    # Commit das mudanças
                    if hasattr(db, 'commit'):
                        db.commit()
                    logger.info("Índices de storage otimizados")
        except Exception as e:
            logger.warning(f"Falha ao otimizar índices: {e}")
    
    def _setup_tools(self) -> None:
        """Configura ferramentas customizadas."""
        try:
            # RAG Search Tool
            if (hasattr(settings, 'QDRANT_URL') and settings.QDRANT_URL and 
                hasattr(settings, 'QDRANT_API_KEY') and settings.QDRANT_API_KEY):
                try:
                    qdrant_client = QdrantClient(
                        url=settings.QDRANT_URL,
                        api_key=settings.QDRANT_API_KEY
                    )
                    rag_tool = RAGSearchTool(
                        qdrant_client=qdrant_client,
                        collection_name=getattr(settings, 'QDRANT_COLLECTION_NAME', 'documents')
                    )
                    self.tools.append(rag_tool)
                    logger.info("RAG Search Tool configurada")
                except Exception as e:
                    logger.warning(f"Falha ao configurar RAG Tool: {e}")
            
            # WhatsApp Tool
            if (hasattr(settings, 'WHATSAPP_TOKEN') and settings.WHATSAPP_TOKEN and
                hasattr(settings, 'WHATSAPP_PHONE_ID') and settings.WHATSAPP_PHONE_ID):
                try:
                    whatsapp_client = WhatsAppClient()
                    whatsapp_tool = WhatsAppTool(whatsapp_client)
                    self.tools.append(whatsapp_tool)
                    logger.info("WhatsApp Tool configurada")
                except Exception as e:
                    logger.warning(f"Falha ao configurar WhatsApp Tool: {e}")
            
            logger.info(f"Total de {len(self.tools)} ferramentas configuradas")
            
        except Exception as e:
            logger.error(f"Erro na configuração das ferramentas: {e}")
            self.tools = []
    
    def _get_optimized_instructions(self) -> str:
        """Retorna instruções otimizadas para o agente seguindo melhores práticas."""
        return """
Você é um assistente de IA especializado, otimizado e confiável.

DIRETRIZES PRINCIPAIS:
1. Seja preciso, direto e útil nas respostas
2. Use as ferramentas disponíveis de forma inteligente
3. Mantenha contexto e personalize interações usando memória
4. Seja proativo em sugerir soluções relevantes
5. Trate erros com elegância e forneça alternativas

FERRAMENTAS DISPONÍVEIS:
- RAG Search: Para buscar informações precisas em documentos
- WhatsApp: Para comunicação e verificação de status
- Memória: Para lembrar preferências e contexto do usuário

COMPORTAMENTO OTIMIZADO:
- Confirme ações importantes antes da execução
- Forneça explicações claras e estruturadas
- Use memória para personalização contínua
- Gerencie erros graciosamente com fallbacks
- Mantenha respostas concisas mas completas

QUALIDADE:
- Priorize precisão sobre velocidade
- Valide informações antes de compartilhar
- Adapte o tom à preferência do usuário
"""
    
    def _create_agent(self) -> None:
        """Cria o agente principal com configurações otimizadas."""
        try:
            # Modelo principal (mais poderoso para respostas)
            main_model = self._get_main_model()
            
            # Configuração completa do agente
            self.agent = Agent(
                model=main_model,
                memory=self.memory,
                storage=self.storage,
                tools=self.tools,
                instructions=self._get_optimized_instructions(),
                
                # Configurações otimizadas para memória
                add_history_to_messages=True,
                num_history_runs=5,  # Aumentado para melhor contexto
                enable_agentic_memory=True,  # Permite ao agente gerenciar memórias
                read_chat_history=True,      # Ferramenta para ler histórico
                # Otimizações de performance
                  tool_call_limit=10,
                 response_model=None,  # Permite respostas mais flexíveis
                 
                 # Configurações de UX
                markdown=True,
                show_tool_calls=settings.DEBUG,
                debug_mode=settings.DEBUG,
                
                # Configurações de sessão
                session_id=self.session_id,
                
                # Configurações de streaming (desabilitado por padrão)
                stream=False
            )
            
            logger.info("Agente principal criado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro na criação do agente principal: {e}")
            raise
    
    def _get_main_model(self):
        """Retorna o modelo principal baseado na configuração."""
        try:
            # Configurar OPENAI_API_KEY a partir de LLM_API_KEY
            if settings.LLM_API_KEY:
                os.environ["OPENAI_API_KEY"] = settings.LLM_API_KEY
                logger.info(f"OPENAI_API_KEY configurada a partir de LLM_API_KEY")
            
            # Priorizar Groq se disponível (mais rápido)
            if GROQ_AVAILABLE and hasattr(settings, 'GROQ_API_KEY') and settings.GROQ_API_KEY:
                return Groq(id="llama-3.1-70b-versatile")
            
            # Usar OpenAI com a configuração correta
            elif settings.LLM_API_KEY:
                return OpenAIChat(
                    id=settings.LLM_MODEL,
                    api_key=settings.LLM_API_KEY,
                    temperature=settings.DEFAULT_LLM_TEMPERATURE,
                    max_tokens=settings.MAX_TOKENS
                )
            
            else:
                raise ValueError("LLM_API_KEY não encontrada nas configurações")
                
        except Exception as e:
            logger.error(f"Erro na configuração do modelo: {e}")
            # Fallback para modelo básico com configuração mínima
            if settings.LLM_API_KEY:
                os.environ["OPENAI_API_KEY"] = settings.LLM_API_KEY
                return OpenAIChat(id="gpt-4o-mini", api_key=settings.LLM_API_KEY)
            else:
                raise ValueError("Impossível configurar modelo: LLM_API_KEY ausente")
    
    def _create_fallback_agent(self) -> None:
        """Cria agente básico como fallback."""
        try:
            logger.warning("Criando agente fallback básico")
            
            # Garantir que OPENAI_API_KEY está configurada
            if settings.LLM_API_KEY:
                os.environ["OPENAI_API_KEY"] = settings.LLM_API_KEY
            
            self.agent = Agent(
                model=OpenAIChat(
                    id="gpt-4o-mini",
                    api_key=settings.LLM_API_KEY if settings.LLM_API_KEY else None
                ),
                instructions="Você é um assistente de IA básico. Responda de forma útil e concisa.",
                markdown=True,
                session_id=self.session_id
            )
            
            logger.info("Agente fallback criado com sucesso")
            
        except Exception as e:
            logger.error(f"Falha crítica na criação do agente fallback: {e}")
            self.agent = None
    
    def is_available(self) -> bool:
        """Verifica se o agente está disponível."""
        return self.agent is not None
    
    def get_response(self, message: str, user_id: str = None) -> Optional[str]:
        """Obtém resposta do agente de forma síncrona com tratamento robusto de erros.
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário (opcional)
            
        Returns:
            Resposta do agente ou None em caso de erro
        """
        if not self.is_available():
            logger.warning("Agente não está disponível, usando resposta de fallback")
            return "Agente não está disponível no momento. Tente novamente em alguns instantes."
        
        try:
            logger.info(f"Processando mensagem para usuário {user_id or 'anônimo'}: {message[:50]}...")
            
            # Configurar contexto do usuário se fornecido
            if user_id:
                self.agent.user_id = user_id
            
            # Obter resposta síncrona (sem streaming)
            response = self.agent.run(message, stream=False)
            
            # Extrair conteúdo da resposta
            if hasattr(response, 'content'):
                result = response.content
            elif hasattr(response, 'text'):
                result = response.text
            else:
                result = str(response)
            
            logger.info(f"Resposta gerada com sucesso ({len(result)} chars)")
            return result
                
        except Exception as e:
            logger.error(f"Erro ao obter resposta para usuário {user_id or 'anônimo'}: {e}", exc_info=True)
            return "Desculpe, ocorreu um erro interno. Nossa equipe foi notificada e está trabalhando na correção."
    
    async def get_stream_response(self, message: str, user_id: str = None) -> AsyncGenerator[str, None]:
        """Obtém resposta em streaming do agente.
        
        Args:
            message: Mensagem do usuário
            user_id: ID do usuário (opcional)
            
        Yields:
            Chunks da resposta em streaming
        """
        if not self.is_available():
            logger.error("Agente não está disponível")
            yield "Erro: Agente não disponível"
            return
        
        try:
            # Configurar contexto do usuário se fornecido
            if user_id:
                self.agent.user_id = user_id
            
            # Stream da resposta usando run_response
            response = self.agent.run(message, stream=True)
            
            # Verificar se é um generator/iterator
            if hasattr(response, '__iter__'):
                for chunk in response:
                    if hasattr(chunk, 'content') and chunk.content:
                        yield chunk.content
                    elif isinstance(chunk, str):
                        yield chunk
            else:
                # Fallback para resposta não-streaming
                if hasattr(response, 'content'):
                    yield response.content
                else:
                    yield str(response)
                    
        except Exception as e:
            logger.error(f"Erro no streaming: {e}")
            yield f"Erro no streaming: {str(e)}"
    
    def get_chat_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtém histórico de chat.
        
        Args:
            limit: Número máximo de mensagens
            
        Returns:
            Lista com histórico de mensagens
        """
        if not self.is_available() or not self.storage:
            return []
        
        try:
            # Implementar busca no storage
            sessions = self.storage.read_sessions(
                session_id=self.session_id,
                limit=limit
            )
            
            return [{
                "role": session.get("role", "unknown"),
                "content": session.get("content", ""),
                "timestamp": session.get("created_at", "")
            } for session in sessions]
            
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {e}")
            return []
    
    def clear_chat_history(self) -> bool:
        """Limpa histórico de chat.
        
        Returns:
            True se bem-sucedido, False caso contrário
        """
        if not self.is_available() or not self.storage:
            return False
        
        try:
            # Limpar sessões do storage
            self.storage.delete_sessions(session_id=self.session_id)
            
            # Limpar memória se disponível
            if self.memory:
                self.memory.clear()
            
            logger.info(f"Histórico limpo para sessão: {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar histórico: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do agente com diagnóstico detalhado.
        
        Returns:
            Dict com status dos componentes
        """
        try:
            # Verificações básicas
            agent_ok = self.is_available()
            memory_ok = self.memory is not None
            storage_ok = self.storage is not None
            tools_count = len(self.tools)
            
            # Verificações avançadas
            model_ok = False
            if agent_ok and hasattr(self.agent, 'model'):
                model_ok = self.agent.model is not None
            
            # Determinar status geral
            if agent_ok and model_ok:
                overall_status = "healthy"
            elif agent_ok:
                overall_status = "degraded"
            else:
                overall_status = "critical"
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "agent_available": agent_ok,
                "model_available": model_ok,
                "memory_configured": memory_ok,
                "storage_configured": storage_ok,
                "tools_count": tools_count,
                "session_id": self.session_id,
                "status": overall_status,
                "version": "1.0.0"
            }
            
            logger.info(f"Health check completo: {overall_status}")
            return status
            
        except Exception as e:
            logger.error(f"Erro crítico no health check: {e}", exc_info=True)
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e),
                "session_id": self.session_id,
                "version": "1.0.0"
            }


# Instância global do agente (singleton pattern)
_agno_agent_instance: Optional[OptimizedAgnoAgent] = None


def get_agno_agent(session_id: str = "default_session") -> OptimizedAgnoAgent:
    """Obtém instância do agente Agno (singleton).
    
    Args:
        session_id: ID da sessão
        
    Returns:
        Instância do OptimizedAgnoAgent
    """
    global _agno_agent_instance
    
    if _agno_agent_instance is None or _agno_agent_instance.session_id != session_id:
        logger.info(f"Criando nova instância do AgnoAgent para sessão: {session_id}")
        _agno_agent_instance = OptimizedAgnoAgent(session_id=session_id)
    
    return _agno_agent_instance


# Funções de conveniência para compatibilidade com código existente
def get_response(message: str, user_id: str = None, session_id: str = "default_session") -> Optional[str]:
    """Função de conveniência para obter resposta."""
    agent = get_agno_agent(session_id)
    return agent.get_response(message, user_id)


async def get_stream_response(message: str, user_id: str = None, session_id: str = "default_session") -> AsyncGenerator[str, None]:
    """Função de conveniência para streaming."""
    agent = get_agno_agent(session_id)
    async for chunk in agent.get_stream_response(message, user_id):
        yield chunk


def health_check(session_id: str = "default_session") -> Dict[str, Any]:
    """Função de conveniência para health check."""
    agent = get_agno_agent(session_id)
    return agent.health_check()