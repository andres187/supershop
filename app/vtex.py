"""Cliente para la API pública de catálogo VTEX (común a Olímpica, Éxito y Jumbo)."""
import re
import time
from urllib.parse import quote

import httpx

from .categorize import classify
from .compare import BRAND_ALIASES
from .models import Offer
from .normalize import parse_size, unit_price
from .stores import Store

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Accept": "application/json",
}
PAGE_SIZE = 50  # máximo que permite VTEX por request
CACHE_TTL = 600

_cache: dict[tuple[str, str], tuple[float, list[Offer]]] = {}


def _best_seller_offer(product: dict) -> tuple[dict, dict] | None:
    """El seller más barato con stock, entre todos los items (SKUs) del producto."""
    best = None
    for item in product.get("items", []):
        for seller in item.get("sellers", []):
            offer = seller.get("commertialOffer") or {}
            if offer.get("AvailableQuantity", 0) > 0 and offer.get("Price", 0) > 0:
                if best is None or offer["Price"] < best[1]["commertialOffer"]["Price"]:
                    best = (item, seller)
    return best


def parse_product(store: Store, product: dict) -> Offer | None:
    found = _best_seller_offer(product)
    if not found:
        return None
    item, seller = found
    co = seller["commertialOffer"]
    name = product.get("productName") or item.get("name") or ""
    images = item.get("images") or []
    offer = Offer(
        store=store.key,
        store_name=store.name,
        name=name,
        brand=product.get("brand") or "",
        price=float(co["Price"]),
        list_price=float(co.get("ListPrice") or co["Price"]),
        link=f"{store.base_url}/{product['linkText']}/p",
        image=images[0].get("imageUrl") if images else None,
        seller=seller.get("sellerName"),
        sku_id=item.get("itemId"),
        seller_id=seller.get("sellerId"),
    )
    size = parse_size(name)
    if size:
        offer.size_qty, offer.size_unit, offer.size_label = size
        offer.unit_price, offer.unit_price_label = unit_price(offer.price, offer.size_qty, offer.size_unit)
    offer.product_type = classify(name, offer.size_unit)
    return offer


async def search(client: httpx.AsyncClient, store: Store, query: str) -> list[Offer]:
    key = (store.key, query.lower().strip())
    cached = _cache.get(key)
    if cached and time.time() - cached[0] < CACHE_TTL:
        return cached[1]

    # VTEX rechaza (400) los espacios codificados como "+", por eso se arma la URL a mano con %20.
    # El "&" (ej. "head & shoulders") hace que Éxito devuelva resultados sin relación.
    term = query.lower()
    for pattern, full in BRAND_ALIASES.items():
        term = re.sub(pattern, full, term)
    term = " ".join(term.replace("&", " ").split())
    url = f"{store.base_url}{store.search_path}?ft={quote(term)}&_from=0&_to={PAGE_SIZE - 1}"
    resp = await client.get(
        url,
        headers=HEADERS,
        timeout=15,
        follow_redirects=True,
    )
    resp.raise_for_status()
    offers = [o for p in resp.json() if (o := parse_product(store, p))]
    _cache[key] = (time.time(), offers)
    return offers
