import os, csv
from datetime import datetime
from langchain.docstore.document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from config import Config

config = Config()

# inicializa stores y retrievers
store_stock = ElasticsearchStore(
    es_url=config.ES_URL,
    es_user=config.ES_USER,
    es_password=config.ES_PASSWORD,
    index_name="stock",
    embedding=OpenAIEmbeddings(),
)
retriever_stock = store_stock.as_retriever(search_kwargs={"k": 1})


# Funcion de reindexacion [RAG]
def reindex_stock_csv():
    print("[RAG Stock CSV]")
    try:
        mtime = os.path.getmtime(config.CSV_STOCK_PATH)
        if getattr(store_stock, "_last_mtime", None) != mtime:
            print(f"\t↳ CSV modificado. Reindexando... (mtime={mtime})")
            if store_stock.client.indices.exists(index="stock"):
                store_stock.client.indices.delete(index="stock")
                print("\t↳ Índice 'stock' eliminado")
            docs = []
            with open(config.CSV_STOCK_PATH, encoding="utf-8", newline="") as f:
                for r in csv.DictReader(f):
                    docs.append(
                        Document(
                            page_content=r["name"],
                            metadata={
                                "name": r["name"],
                                "category": r["category"],
                                "description": r["description"],
                                "price": float(r["price"]),
                                "stock": int(float(r["stock"])),
                            },
                        )
                    )
            store_stock.add_documents(docs)
            store_stock._last_mtime = mtime
            print(f"\t↳ Añadidos {len(docs)} documentos al índice 'stock'")
        else:
            print("\t↳ No hay cambios en CSV, no reindexa")
    except Exception as e:
        print(f"\t↳ Rag error: {e}")
