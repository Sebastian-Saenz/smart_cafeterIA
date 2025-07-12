import csv
from typing import List
from langchain_core.tools import tool
from config import Config
from .store import store_stock

config = Config()

@tool
def get_recommendation(out_of_stock: List[str]) -> str:
    """Sugiere o recomienda alternativas para productos sin stock basadas en la misma categoría"""
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
            try:
                sugg_name = result.metadata["name"].lower().strip()
                print(f"\t↳ Sugerencia: {sugg_name}")
                if sugg_name == name:
                    continue # Si es el mismo, salir de bucle
                sugg_category = result.metadata["category"]
                answer = f"Sugerencia de {name}: {sugg_name}. "
                print(f"\t↳ Producto recomendado: '{sugg_name}' ({sugg_category})")
                suggestions.append(answer)
                break
            except Exception as e:
                print(f"\t↳ Error al procesar resultado: {e}")

    # 4. Formatear respuesta
    if not suggestions:
        resp = "Lo siento, no tengo recomendaciones por ahora 😕"
    else:
        resp = f"Recomendamos probar: {', '.join(suggestions)}"
    print(f"\t↳ Respuesta={resp}")
    return resp
