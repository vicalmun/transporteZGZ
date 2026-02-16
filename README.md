# ZGZ Transport 🚌🚊

Web ultra-ligera para consultar tiempos de bus y tranvía en Zaragoza.
Diseñada para funcionar en dispositivos con KaiOS (Nokia 3300, etc).

## Características

- **HTML mínimo**: ~1.5KB por página
- **CSS mínimo**: ~800 bytes
- **JS vanilla**: Sin frameworks, ES5 compatible
- **Backend ligero**: FastAPI que procesa datos y maneja errores
- **Reintentos automáticos**: La API del Ayto es inestable, el backend reintenta 3 veces

## Estructura

```
├── api/
│   └── index.py          # Backend FastAPI (Vercel Functions)
├── public/
│   ├── index.html        # Redirect a /marquesina/
│   ├── style.css         # CSS compartido (~800 bytes)
│   ├── marquesina/
│   │   └── index.html    # Consulta de buses por nº de poste
│   └── tranvia/
│       └── index.html    # Lista de paradas + tiempos
├── requirements.txt
├── vercel.json
└── README.md
```

## Endpoints API

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/bus?poste=716` | Tiempos de buses en un poste |
| `GET /api/tranvia/paradas` | Lista de paradas de tranvía |
| `GET /api/tranvia/tiempos?id=XXX` | Tiempos en una parada |

## Deploy en Vercel

```bash
# Instalar Vercel CLI si no lo tienes
npm i -g vercel

# Deploy
cd zgz-transport
vercel
```

## Desarrollo local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Correr backend (en una terminal)
uvicorn api.index:app --reload --port 8000

# Servir estáticos (en otra terminal)
cd public && python -m http.server 3000
```

## API del Ayuntamiento

Este proyecto usa la API abierta del Ayuntamiento de Zaragoza:
- [Documentación](https://www.zaragoza.es/docs-api_sede/)
- **Nota**: La API puede ser inestable. El backend implementa reintentos automáticos.

## Licencia

MIT
