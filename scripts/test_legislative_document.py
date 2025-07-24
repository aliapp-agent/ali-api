from datetime import date
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag import rag_service
from app.schemas.rag import DocumentoLegislativo
from dotenv import load_dotenv

load_dotenv('.env.development')

def test_legislative_document():
    """Test adding and searching legislative document"""
    
    # Create test document
    documento = DocumentoLegislativo(
        id="pl_2023_045",
        source_type="projeto",
        title="Projeto de Lei 045/2023 - Institui o Programa Municipal de Saúde Mental",
        content="Art. 1º Fica instituído o Programa Municipal de Saúde Mental no âmbito do município de Água Clara-MS, com o objetivo de promover ações de prevenção, tratamento e reabilitação em saúde mental. Art. 2º O programa será desenvolvido através de parcerias com entidades públicas e privadas...",
        summary="Institui o Programa de Saúde Mental no município, com diretrizes de prevenção e atendimento.",
        date=date(2023, 8, 21),
        municipio="Água Clara-MS",
        legislatura="2021-2024",
        autor="Vereadora Maria Lúcia",
        categoria="saúde",
        status="em tramitação",
        tipo_documento="Projeto de Lei Ordinária",
        file_path="/docs/projetos/pl_2023_045.pdf"
    )
    
    print("🏛️  Testando sistema RAG para documentos legislativos...")
    
    # Test health check
    health = rag_service.health_check()
    print(f"Status: {health['status']}")
    
    # Create index
    if rag_service.create_index():
        print("✅ Índice criado/verificado com sucesso")
    
    # Add document
    if rag_service.add_legislative_document(documento):
        print(f"✅ Documento adicionado: {documento.id}")
    
    # Search documents
    print("\n🔍 Testando buscas...")
    
    # Search by content
    results = rag_service.search_legislative_documents(
        query="saúde mental prevenção",
        max_results=3
    )
    print(f"Busca por 'saúde mental': {len(results)} resultados")
    for result in results:
        print(f"  - {result.title} (score: {result.score:.3f})")
    
    # Search with filters
    results = rag_service.search_legislative_documents(
        query="programa municipal",
        categoria="saúde",
        status="em tramitação"
    )
    print(f"\nBusca filtrada (categoria=saúde): {len(results)} resultados")
    
    # Get categories
    categories = rag_service.get_categories()
    print(f"\nCategorias disponíveis: {categories}")
    
    # Get document by ID
    doc = rag_service.get_document_by_id("pl_2023_045")
    if doc:
        print(f"\n✅ Documento recuperado por ID: {doc['title']}")
    
    print("\n🎉 Teste concluído com sucesso!")

if __name__ == "__main__":
    test_legislative_document()