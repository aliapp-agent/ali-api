from agno.tools.function import Function

from app.core.logging import logger
from app.services.rag import RAGService


async def rag_search(query: str, top_k: int = 5) -> str:
    """Busca informações na base de conhecimento usando RAG.

    Args:
        query: Consulta para buscar na base de conhecimento
        top_k: Número máximo de resultados (padrão: 5)

    Returns:
        str: Informações encontradas formatadas
    """
    try:
        rag_service = RAGService()
        results = await rag_service.search_similar(query, top_k)

        if not results:
            return "Nenhuma informação relevante encontrada na base de conhecimento."

        context = "Informações encontradas na base de conhecimento:\n\n"
        for i, result in enumerate(results, 1):
            context += f"{i}. **{result['title']}** (Score: {result['score']:.2f})\n"
            context += f"   {result['content'][:500]}...\n\n"

        return context

    except Exception as e:
        logger.error(f"Erro na busca RAG: {e}")
        return f"Erro ao buscar informações: {str(e)}"


rag_search_tool = Function(
    function=rag_search,
    name="rag_search",
    description="Busca informações na base de conhecimento usando RAG",
)
