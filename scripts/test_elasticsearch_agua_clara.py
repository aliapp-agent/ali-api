import os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv(".env.development")


def test_agua_clara_connection():
    """Test connection to Elasticsearch Serverless"""
    try:
        client = Elasticsearch(
            "https://my-elasticsearch-project-c53447.es.us-central1.gcp.elastic.cloud:443",
            api_key="T2d5S09aZ0JSdWh5aVRpUzRXRzI6bk1kZ1FKRWNGS1FKRnpLcE50ZHhOQQ==",
        )

        # Test connection
        if client.ping():
            print("✅ Conexão com Elasticsearch Serverless bem-sucedida!")

            # Get cluster info
            info = client.info()
            print(f"Cluster: {info['cluster_name']}")
            print(f"Version: {info['version']['number']}")

            # Check if agua-clara-ms index exists
            index_name = "agua-clara-ms"
            if client.indices.exists(index=index_name):
                print(f"✅ Índice '{index_name}' encontrado!")

                # Use count API instead of stats for serverless
                try:
                    count_response = client.count(index=index_name)
                    doc_count = count_response["count"]
                    print(f"Documentos no índice: {doc_count}")
                except Exception as e:
                    print(
                        f"⚠️  Não foi possível obter contagem de documentos: {e}"
                    )

                # Test a simple search
                try:
                    search_response = client.search(
                        index=index_name,
                        body={"query": {"match_all": {}}, "size": 1},
                    )
                    print("✅ Busca de teste bem-sucedida!")
                    print(
                        f"Total de hits: {search_response['hits']['total']['value']}"
                    )
                except Exception as e:
                    print(f"⚠️  Erro na busca de teste: {e}")

            else:
                print(
                    f"⚠️  Índice '{index_name}' não encontrado. Será criado automaticamente."
                )

        else:
            print("❌ Falha na conexão")

    except Exception as e:
        print(f"❌ Erro: {e}")


if __name__ == "__main__":
    test_agua_clara_connection()
