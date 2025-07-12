from typing import Dict
from langchain_core.tools import tool

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
