"""
ZGZ Transport API - Backend para Vercel Functions
Maneja todas las llamadas a la API del Ayuntamiento de Zaragoza
"""

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import httpx
import asyncio

app = FastAPI()

# Config
API_BASE = "https://www.zaragoza.es/sede/servicio/urbanismo-infraestructuras"
TIMEOUT = 10.0
MAX_RETRIES = 3


async def fetch_with_retry(url: str, retries: int = MAX_RETRIES) -> dict | None:
    """Fetch con reintentos - la API del Ayto es inestable"""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for attempt in range(retries):
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    # La API a veces devuelve {"error": "..."} con status 200
                    if "error" not in data:
                        return data
                # Esperar un poco antes de reintentar
                if attempt < retries - 1:
                    await asyncio.sleep(0.5)
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(0.5)
                continue
    return None


@app.get("/api/bus")
async def get_bus(poste: str = Query(..., description="Número de poste")):
    """
    Obtiene tiempos de llegada de buses para un poste dado.
    Limpia y simplifica la respuesta para el cliente.
    """
    # Limpiar input (solo números)
    poste_num = ''.join(filter(str.isdigit, poste))
    if not poste_num:
        return JSONResponse({"error": "Introduce un número de poste válido"}, status_code=400)
    
    url = f"{API_BASE}/transporte-urbano/poste-autobus/tuzsa-{poste_num}.json"
    data = await fetch_with_retry(url)
    
    if not data:
        return JSONResponse({
            "error": "No se pudo obtener info. Comprueba el número o intenta de nuevo."
        }, status_code=502)
    
    # Extraer y limpiar datos
    destinos = []
    for d in data.get("destinos", []):
        destinos.append({
            "linea": d.get("linea", "?"),
            "destino": d.get("destino", ""),
            "primero": d.get("primero", "?"),
            "segundo": d.get("segundo")
        })
    
    # Extraer nombre de parada del title: "(716) P. Fernando El Católico N.º 70 Líneas: Ci1, 42"
    title = data.get("title", "")
    parada = title.split(" Líneas:")[0] if " Líneas:" in title else title
    
    return {
        "parada": parada,
        "destinos": destinos
    }


@app.get("/api/tranvia/paradas")
async def get_tranvia_paradas():
    """
    Obtiene lista de paradas de tranvía (solo id y nombre).
    Se cachea en el cliente porque cambia muy poco.
    """
    url = f"{API_BASE}/transporte-urbano/parada-tranvia.json?rows=100"
    data = await fetch_with_retry(url)
    
    if not data or "result" not in data:
        return JSONResponse({
            "error": "No se pudo obtener lista de paradas"
        }, status_code=502)
    
    paradas = []
    for p in data.get("result", []):
        paradas.append({
            "id": p.get("id"),
            "nombre": p.get("title", "")
        })
    
    # Ordenar por nombre
    paradas.sort(key=lambda x: x["nombre"])
    
    return paradas


@app.get("/api/tranvia/tiempos")
async def get_tranvia_tiempos(id: str = Query(..., description="ID de parada")):
    """
    Obtiene tiempos de llegada para una parada de tranvía específica.
    """
    if not id:
        return JSONResponse({"error": "Falta ID de parada"}, status_code=400)
    
    url = f"{API_BASE}/transporte-urbano/parada-tranvia/{id}.json"
    data = await fetch_with_retry(url)
    
    if not data:
        return JSONResponse({
            "error": "No se pudo obtener tiempos. Intenta de nuevo."
        }, status_code=502)
    
    destinos = []
    for d in data.get("destinos", []):
        destinos.append({
            "linea": d.get("linea", "L1"),
            "destino": d.get("destino", ""),
            "minutos": d.get("minutos", "?")
        })
    
    return {
        "parada": data.get("title", ""),
        "destinos": destinos
    }
