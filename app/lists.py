"""Listas de compra guardadas en un archivo JSON local (data/lists.json).

Dos tipos: "lista" (guardada a mano con un nombre) y "compra" (se guarda sola al pasar
el carrito a una tienda), para poder repetirlas después con los precios del día.
"""
import json
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

DATA_FILE = Path(os.environ.get("LISTS_FILE", Path(__file__).resolve().parent.parent / "data" / "lists.json"))
MAX_LISTS = 200
_lock = threading.Lock()


class ListItem(BaseModel):
    query: str = Field(min_length=1, max_length=200)  # lo que se buscó, para volver a buscarlo
    type: str = Field(max_length=100)  # tipo de producto, ej. "Detergente en polvo"
    qty: int = Field(ge=1, le=999)
    name: str = Field(max_length=300)  # producto escogido esa vez
    store: str = Field(max_length=50)
    price: float = Field(ge=0)  # precio unitario pagado esa vez
    size_qty: float | None = None  # tamaño en g, ml o und (para mantener la misma cantidad)
    size_unit: str | None = None
    unit_price: float | None = None
    unit_price_label: str | None = None


class ShoppingList(BaseModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["lista", "compra"] = "lista"
    items: list[ListItem] = Field(min_length=1, max_length=100)
    total: float = Field(ge=0)
    savings: float = 0
    created_at: str | None = None
    updated_at: str | None = None


def _read() -> list[dict]:
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []


def _write(lists: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Escritura atómica: un archivo temporal y luego reemplazo, para no dejar el JSON a medias.
    fd, tmp = tempfile.mkstemp(dir=DATA_FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(lists, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def all_lists() -> list[dict]:
    with _lock:
        return sorted(_read(), key=lambda l: l.get("updated_at") or "", reverse=True)


def upsert(item: ShoppingList) -> dict:
    """Crea o reemplaza (mismo id) una lista. Conserva la fecha de creación original."""
    now = datetime.now().isoformat(timespec="seconds")
    with _lock:
        lists = _read()
        old = next((l for l in lists if l["id"] == item.id), None)
        data = item.model_dump()
        data["created_at"] = (old or {}).get("created_at") or item.created_at or now
        data["updated_at"] = now
        lists = [l for l in lists if l["id"] != item.id] + [data]
        # Si hay demasiadas, se descartan las compras automáticas más viejas (nunca las listas con nombre).
        while len(lists) > MAX_LISTS:
            compras = sorted((l for l in lists if l["kind"] == "compra"), key=lambda l: l["updated_at"])
            if not compras:
                break
            lists.remove(compras[0])
        _write(lists)
        return data


def delete(list_id: str) -> bool:
    with _lock:
        lists = _read()
        kept = [l for l in lists if l["id"] != list_id]
        if len(kept) == len(lists):
            return False
        _write(kept)
        return True
