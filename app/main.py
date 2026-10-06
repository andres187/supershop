import asyncio
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates

from . import lists, vtex
from .compare import compare
from .stores import STORES

app = FastAPI(title="Comparador de precios")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"stores": STORES})


async def _search_one(client: httpx.AsyncClient, query: str) -> dict:
    results = await asyncio.gather(*(vtex.search(client, s, query) for s in STORES), return_exceptions=True)
    offers, errors = [], {}
    for store, res in zip(STORES, results):
        if isinstance(res, Exception):
            errors[store.key] = f"{type(res).__name__}: {res}"
        else:
            offers.extend(res)
    result = compare(offers, query)
    return {
        "query": query,
        "total": result["total"],
        "groups": [
            {
                "type": g["type"],
                "unit": g["unit"],
                "best_offer": g["best_offer"].to_dict(),
                "best_by_store": {k: v.to_dict() for k, v in g["best_by_store"].items()},
                "offers": [o.to_dict() for o in g["offers"]],
            }
            for g in result["groups"]
        ],
        "errors": errors,
    }


@app.get("/api/search")
async def api_search(q: str = Query(..., description="Uno o varios productos separados por coma")):
    # Hasta 30 productos (una lista guardada puede ser larga); se limitan las conexiones simultáneas.
    queries = list(dict.fromkeys(part.strip() for part in q.split(",") if part.strip()))[:30]
    async with httpx.AsyncClient(limits=httpx.Limits(max_connections=12)) as client:
        results = await asyncio.gather(*(_search_one(client, query) for query in queries))
    return {"results": results}


@app.get("/api/lists")
def get_lists():
    return {"lists": lists.all_lists()}


@app.put("/api/lists/{list_id}")
def put_list(list_id: str, item: lists.ShoppingList):
    if item.id != list_id:
        raise HTTPException(400, "El id no coincide")
    return lists.upsert(item)


@app.delete("/api/lists/{list_id}")
def delete_list(list_id: str):
    if not lists.delete(list_id):
        raise HTTPException(404, "Lista no encontrada")
    return {"ok": True}
