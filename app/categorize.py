"""Clasifica productos en tipos comparables (ej. "Detergente en polvo" vs "Detergente líquido").

Las categorías de VTEX no sirven: cada tienda usa un árbol distinto y a veces mal asignado,
así que se clasifica por palabras clave del nombre y por la unidad del tamaño.
"""
import re

from .normalize import strip_accents

# (patrón sobre el nombre sin tildes, tipo base). El orden importa: gana el primero que coincide.
_BASE_TYPES = [
    (r"\bkit\b|\bset\b", "Kits y sets"),
    # Antes que "Blanqueador": hay cremas dentales "blanqueadoras".
    (r"(pasta|crema|crem)\.?( gel)? ?(dental|dent|de dientes)", "Crema dental"),
    (r"lava ?platos?|lava ?loza|l/plato|lozamax|lavavajilla", "Lavaplatos"),
    (r"suavizante", "Suavizante"),
    (r"quitamanchas|desmanchador", "Quitamanchas"),
    (r"deterg|detrgente", "Detergente"),
    (r"blanq|limpido|cloro\b|hipoclorito", "Blanqueador"),
    (r"limpia ?pisos|limpiad|desinfectante|fabuloso", "Limpiador"),
    (r"enjuague bucal|enjuague", "Enjuague bucal"),
    (r"cepillo dental|cepillo de dientes", "Cepillo dental"),
    (r"jabon|jab\b", "Jabón"),
    (r"shampoo|champu", "Shampoo"),
    (r"acondicionador", "Acondicionador"),
    (r"desodorante|antitranspirante", "Desodorante"),
    (r"papel higienico", "Papel higiénico"),
    (r"crema corporal|locion corporal", "Crema corporal"),
]
# Tipos que se dividen por presentación.
_FORM_TYPES = {"Detergente", "Jabón", "Blanqueador", "Lavaplatos"}


def _form(base: str, text: str, unit: str | None) -> str | None:
    if re.search(r"\bgel\b", text) and base in {"Blanqueador", "Lavaplatos", "Jabón"}:
        return "gel"
    if re.search(r"\bpol(v|to|tvo)", text):
        return "en polvo"
    if re.search(r"\bbarra\b|\btocador\b", text):
        return "en barra"
    if re.search(r"\bliq", text) or unit == "ml":
        return "líquido"
    if unit == "g":
        return "en barra" if base == "Jabón" else "en polvo" if base == "Detergente" else "en crema"
    return None


def classify(name: str, unit: str | None) -> str:
    text = strip_accents(name)
    for pattern, base in _BASE_TYPES:
        if re.search(pattern, text):
            liquid = unit == "ml" or re.search(r"\bliq", text)
            if base == "Jabón" and re.search(r"\bcorporal\b|\bbano\b|body wash", text) and liquid:
                return "Jabón líquido corporal"
            form = _form(base, text, unit) if base in _FORM_TYPES else None
            return f"{base} {form}" if form else base
    return "Otros"
