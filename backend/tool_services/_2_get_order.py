from typing import List, Dict
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utils import get_prompt

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
