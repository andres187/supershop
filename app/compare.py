"""Filtra resultados irrelevantes y elige la mejor oferta por precio por unidad."""
import re
from collections import Counter

from .models import Offer
from .normalize import strip_accents

STOPWORDS = {"de", "del", "la", "el", "los", "las", "para", "con", "y", "en", "x", "and"}
# Las tiendas usan nombres distintos para lo mismo ("crema dental" = "pasta dental").
SYNONYMS = {"pasta": {"crema"}, "crema": {"pasta"}}
# Abreviaturas de marca que usan las tiendas en nombres y marcas (ej. Éxito: "Shampoo H&S").
BRAND_ALIASES = {r"\bh\s*&\s*s\b": "head shoulders"}


def _words(text: str) -> list[str]:
    text = strip_accents(text)
    for pattern, full in BRAND_ALIASES.items():
        text = re.sub(pattern, full, text)
    return re.findall(r"[a-z0-9]+", text)


def query_tokens(query: str) -> list[str]:
    return [w for w in _words(query) if w not in STOPWORDS]


def _word_matches(token: str, word: str) -> bool:
    # "jabon" ~ "jabones"; "detergente" ~ "deterg" (abreviaturas de Olímpica)
    return word.startswith(token) or (len(word) >= 4 and token.startswith(word))


def _token_in(token: str, words: list[str]) -> bool:
    options = {token} | SYNONYMS.get(token, set())
    return any(_word_matches(t, w) for t in options for w in words)


def relevant(offers: list[Offer], query: str) -> list[Offer]:
    tokens = query_tokens(query)
    if not tokens:
        return offers
    matching = [o for o in offers if all(_token_in(t, _words(o.name + " " + o.brand)) for t in tokens)]
    # Búsquedas de marca ("fab", "limpido"): si hay productos de esa marca, quedarse solo con ellos
    # para descartar coincidencias como "Plastilina Fab ... Faber Castell".
    by_brand = [o for o in matching if any(t in _words(o.brand) for t in tokens)]
    return by_brand or matching


def _sort_key(o: Offer):
    return (o.unit_price is None, o.unit_price or 0, o.price)


def _compare_group(product_type: str, offers: list[Offer]) -> dict:
    with_size = [o for o in offers if o.unit_price is not None]
    unit = None
    if with_size:
        # No se compara $/kg contra $/L: se usa la unidad más común del grupo.
        unit = Counter(o.unit_price_label for o in with_size).most_common(1)[0][0]
        best = min((o for o in with_size if o.unit_price_label == unit), key=_sort_key)
    else:
        best = min(offers, key=lambda o: o.price)

    by_store: dict[str, list[Offer]] = {}
    for o in offers:
        by_store.setdefault(o.store, []).append(o)
    best_by_store = {
        store: min(
            [o for o in items if o.unit_price_label == unit] or items,
            key=_sort_key if unit else (lambda o: o.price),
        )
        for store, items in by_store.items()
    }
    return {
        "type": product_type,
        "unit": unit,
        "best_offer": best,
        "best_by_store": best_by_store,
        "offers": offers,
    }


def compare(offers: list[Offer], query: str) -> dict:
    """Agrupa por tipo de producto y elige la mejor oferta dentro de cada grupo."""
    offers = sorted(relevant(offers, query), key=_sort_key)
    groups: dict[str, list[Offer]] = {}
    for o in offers:
        groups.setdefault(o.product_type, []).append(o)

    def group_rank(item):
        product_type, items = item
        # Primero los tipos presentes en más tiendas y con más productos; "Otros" al final.
        return (product_type == "Otros", -len({o.store for o in items}), -len(items))

    return {
        "query": query,
        "total": len(offers),
        "groups": [_compare_group(t, items) for t, items in sorted(groups.items(), key=group_rank)],
    }
