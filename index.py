"""
ZGZ Transport API - Backend para Vercel Functions
"""

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, FileResponse
import httpx
import asyncio

app = FastAPI()

API_BASE = "https://www.zaragoza.es/sede/servicio/urbanismo-infraestructuras"
TIMEOUT = 10.0
MAX_RETRIES = 3


async def fetch_with_retry(url: str, retries: int = MAX_RETRIES) -> dict | None:
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for attempt in range(retries):
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if "error" not in data:
                        return data
                if attempt < retries - 1:
                    await asyncio.sleep(0.5)
            except Exception:
                if attempt < retries - 1:
                    await asyncio.sleep(0.5)
                continue
    return None


# ============================================
# PÁGINAS ESTÁTICAS
# ============================================

@app.get("/")
@app.get("/bus")
@app.get("/bus/")
async def serve_bus():
    return FileResponse("bus.html")


@app.get("/tram")
@app.get("/tram/")
async def serve_tram():
    return FileResponse("tram.html")


@app.get("/style.css")
async def serve_css():
    return FileResponse("style.css", media_type="text/css")


# ============================================
# API - DEVUELVE HTML DIRECTAMENTE
# ============================================

@app.get("/api/bus", response_class=HTMLResponse)
async def get_bus(poste: str = Query(..., description="Número de poste")):
    poste_num = ''.join(filter(str.isdigit, poste))
    if not poste_num:
        return "<p class='err'>Introduce un número de poste válido</p>"
    
    url = f"{API_BASE}/transporte-urbano/poste-autobus/tuzsa-{poste_num}.json"
    data = await fetch_with_retry(url)
    
    if not data:
        return "<p class='err'>No se pudo obtener info. Comprueba el número o intenta de nuevo.</p>"
    
    # Extraer nombre de parada
    title = data.get("title", "")
    parada = title.split(" Líneas:")[0] if " Líneas:" in title else title
    
    destinos = data.get("destinos", [])
    if not destinos:
        return f"<p><b>{parada}</b></p><p>Sin datos en este momento</p>"
    
    html = f"<p><b>{parada}</b></p><ul>"
    for d in destinos:
        linea = d.get("linea", "?")
        primero = d.get("primero", "?")
        html += f"<li><b>{linea}</b> - {primero}</li>"
    html += "</ul>"
    
    return html


@app.get("/api/tranvia/paradas", response_class=HTMLResponse)
async def get_tranvia_paradas():
    url = f"{API_BASE}/transporte-urbano/parada-tranvia.json?rows=100"
    data = await fetch_with_retry(url)
    
    if not data or "result" not in data:
        return "<option value=''>Error cargando paradas</option>"
    
    paradas = []
    for p in data.get("result", []):
        paradas.append({
            "id": p.get("id"),
            "nombre": p.get("title", "")
        })
    
    paradas.sort(key=lambda x: x["nombre"])
    
    html = "<option value=''>-- Elige parada --</option>"
    for p in paradas:
        html += f"<option value='{p['id']}'>{p['nombre']}</option>"
    
    return html


@app.get("/api/tranvia/tiempos", response_class=HTMLResponse)
async def get_tranvia_tiempos(id: str = Query(..., description="ID de parada")):
    if not id:
        return "<p class='err'>Falta ID de parada</p>"
    
    url = f"{API_BASE}/transporte-urbano/parada-tranvia/{id}.json"
    data = await fetch_with_retry(url)
    
    if not data:
        return "<p class='err'>No se pudo obtener tiempos. Intenta de nuevo.</p>"
    
    destinos = data.get("destinos", [])
    if not destinos:
        return "<p>Sin tranvías en este momento</p>"
    
    html = "<ul>"
    for d in destinos:
        linea = d.get("linea", "L1")
        minutos = d.get("minutos", "?")
        html += f"<li><b>{linea}</b> - {minutos} min</li>"
    html += "</ul>"
    
    return html
