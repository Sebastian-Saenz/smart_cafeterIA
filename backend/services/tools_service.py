import os
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel
from langchain.docstore.document import Document
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_elasticsearch import ElasticsearchStore
from langchain_core.prompts import ChatPromptTemplate
from models.product import StockRequest
from utils import get_prompt

# Configuración global
config = __import__("config").Config()

###### STORES por dominio ######
# -> Índice de stock <-
print("[ToolService] Inicializando store_stock")
store_stock = ElasticsearchStore(
    es_url=config.ES_URL,
    es_user=config.ES_USER,
    es_password=config.ES_PASSWORD,
    index_name="stock",
    embedding=OpenAIEmbeddings(),
)
retriever_stock = store_stock.as_retriever(search_kwargs={"k": 1})

# -> Índice de órdenes históricas <-
print("[ToolService] Inicializando store_orders")
store_orders = ElasticsearchStore(
    es_url=config.ES_URL,
    es_user=config.ES_USER,
    es_password=config.ES_PASSWORD,
    index_name="orders",
    embedding=OpenAIEmbeddings(),
)
# retriever_orders = store_orders.as_retriever(search_kwargs={"k": 1})

# -> Índice de datos de clientes <-
print("[ToolService] Inicializando store_clients")
store_clients = ElasticsearchStore(
    es_url=config.ES_URL,
    es_user=config.ES_USER,
    es_password=config.ES_PASSWORD,
    index_name="clients",
    embedding=OpenAIEmbeddings(),
)
# retriever_clients = store_clients.as_retriever(search_kwargs={"k": 1})


# — Reindexación stock —
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


# — Tool: check_schedule —
@tool
def check_schedule() -> str:
    """Responde 'abierto' o 'cerrado' según el horario de atención"""
    print("[Tool Check Schedule]:")
    ahora = datetime.strptime("18:00", "%H:%M").time()  # datetime.now().time()
    apertura = datetime.strptime("14:00", "%H:%M").time()
    cierre = datetime.strptime("21:30", "%H:%M").time()
    state = "abierto" if apertura <= ahora <= cierre else "cerrado"
    print(f"\t↳ Estado horario: {state} (hora actual: {ahora})")
    return state


# — Tool: get_order —
llm = ChatOpenAI(model="gpt-4.1-2025-04-14", temperature=0)


@tool
def get_order(msg: str) -> List[Dict[str, int]]:
    """Extrae lista de productos y cantidades del mensaje"""
    print(f"[Tool Get Order]")
    print(f"\t↳ Mensaje: {msg}")
    prompt = ChatPromptTemplate.from_template(get_prompt("get_order.txt"))
    result = (prompt | llm).invoke({"msg": msg})
    print(f"\t↳ LLM output: {result.content}")
    try:
        order_list = eval(result.content)
        print(f"\t↳ Orden parseada: {order_list}")
        return order_list
    except Exception as e:
        print(f"\t↳ Error al parsear orden: {e}")
        return []


# — Tool: search_stock —
@tool("search_stock", args_schema=StockRequest)
def search_stock(products: List[str]) -> List[Dict[str, int]]:
    """Consulta stock de múltiples productos"""
    print(f"[Tool Search Stock]")
    print(f"\t↳ Consultado stock de: {products}")
    reindex_stock_csv()
    res = []
    for name in products:
        docs = retriever_stock.invoke(name)
        stock = docs[0].metadata.get("stock", 0) if docs else 0
        print(f"\t↳ Producto: {name}, stock: {stock}")
        res.append({"name": name, "stock": stock})
    print(f"\t↳ Resultado: {res}")
    return res


def get_product(name: str):
    name = name.lower().strip()
    category = None
    description = None

    print(f"===== Para {name} =====")
    # 1. Leer solo la fila necesaria
    with open(config.CSV_STOCK_PATH, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["name"].lower().strip() == name:
                category = r["category"]
                description = r["description"]

    print(f"\t↳ Realizando Rag semantico para '{name}' ({category}):")
    print(f"\t↳ Desc: {description}")
    retriever = store_stock.as_retriever(search_kwargs={"k": 2})
    results = retriever.invoke(description)
    print(
        f"\t↳ Producto recomendado: '{results[1].metadata["name"]}' ({results[1].metadata["category"]})"
    )


# get_product("Empanada de pollo")


# — Tool: get_recommendation —
@tool
def get_recommendation(out_of_stock: List[str]) -> str:
    """Sugiere alternativas para productos sin stock basadas en la misma categoría"""
    print(f"[Tool Recommendario]")
    print(f"\t↳ Productos sin stock: {out_of_stock}")

    suggestions = []
    # 1. Buscamos sugerencias para cada producto en out_of_stock
    for name in out_of_stock:
        name = name.lower().strip()
        category = None
        description = None

        print(f"\t↳ Buscando sugerencia para {name}")
        with open(config.CSV_STOCK_PATH, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if r["name"].lower().strip() == name:
                    category = r["category"]
                    description = r["description"]

        print(f"\t↳ Realizando Rag semantico para '{name}' ({category}):")
        print(f"\t↳ Desc: {description}")
        retriever = store_stock.as_retriever(search_kwargs={"k": 2})
        results = retriever.invoke(description)
        print(f"\t↳ Resultados obtenidos: {results}")

        for result in results:
            sugg_name = result.metadata["name"].lower().strip()
            print(f"\t↳ Sugerencia: {sugg_name}")
            if sugg_name == name:
                continue # Si es el mismo, salir de bucle
            sugg_category = doc.metadata["category"]
            answer = f"Sugerencia de {name}: {sugg_name}. "
            print(f"\t↳ Producto recomendado: '{sugg_name}' ({sugg_category})")
            suggestions.append(answer)
            break

    # 4. Formatear respuesta
    if not suggestions:
        resp = "Lo siento, no tengo recomendaciones por ahora 😕"
    else:
        resp = f"Recomendamos probar: {', '.join(suggestions)}"
    print(f"\t↳ Respuesta={resp}")
    return resp


# — Tool: get_client_data —
@tool
def get_client_data(thread_id: str) -> Dict[str, str]:
    """Retorna address y phone del cliente desde Elasticsearch"""
    print(f"[Tool Data Client] get_client_data llamado con thread_id: {thread_id}")
    print(f"\t↳ Obteniendo direccion y telefono del cliente para delivery")
    # retriever = store_clients.as_retriever(search_kwargs={"k": 1})
    # docs = retriever.invoke(thread_id)
    # if docs:
    #     data = {
    #         "address": docs[0].metadata.get("address", ""),
    #         "phone": docs[0].metadata.get("phone", ""),
    #     }
    #     print(f"[Tool] Datos cliente: {data}")
    #     return data
    # print("[Tool] No se encontraron datos de cliente")
    return {"address": "Jr. Union 123", "phone": "930 552 355"}
