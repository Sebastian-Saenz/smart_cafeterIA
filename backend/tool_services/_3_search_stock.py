from typing import List, Dict
from langchain_core.tools import tool
from models.product import StockRequest
from .store import retriever_stock, reindex_stock_csv


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
