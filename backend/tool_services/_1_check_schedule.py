from datetime import datetime
from langchain_core.tools import tool

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