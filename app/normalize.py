"""Extrae el tamaño del nombre del producto y calcula el precio por unidad."""
import re
import unicodedata

_UNITS = {
    "kg": ("g", 1000), "kgs": ("g", 1000), "kilo": ("g", 1000), "kilos": ("g", 1000),
    "g": ("g", 1), "gr": ("g", 1), "grs": ("g", 1), "grm": ("g", 1), "grms": ("g", 1),
    "gramo": ("g", 1), "gramos": ("g", 1),
    "l": ("ml", 1000), "lt": ("ml", 1000), "lts": ("ml", 1000), "litro": ("ml", 1000), "litros": ("ml", 1000),
    "ml": ("ml", 1), "cc": ("ml", 1),
}
_NUM = r"(\d+(?:[.,]\d+)?)"
_SIZE_RE = re.compile(_NUM + r"\s*(" + "|".join(sorted(_UNITS, key=len, reverse=True)) + r")\b")
_PACK_WORD_RE = re.compile(r"(?:\bx\s*)?(\d+)\s*(?:und|unds|un|ud|uds|unid|unids|unidad|unidades|u)\b")
_PACK_X_RE = re.compile(r"(?:\bpack|\bpaquete|\bx)\s*x?\s*(\d+)\b")


def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def parse_size(name: str) -> tuple[float, str, str] | None:
    """Devuelve (cantidad, unidad base, etiqueta) o None. Unidad base: g, ml o und."""
    text = strip_accents(name)
    size = _SIZE_RE.search(text)
    rest = text[: size.start()] + " " + text[size.end():] if size else text
    pack_m = _PACK_WORD_RE.search(rest) or _PACK_X_RE.search(rest)
    pack = int(pack_m.group(1)) if pack_m else 1
    if pack <= 0 or pack > 200:
        pack = 1

    if size:
        value, unit = _num(size.group(1)), size.group(2)
        base, factor = _UNITS[unit]
        if value <= 0:
            return None
        label = f"{size.group(1).replace(',', '.')} {unit}"
        if pack > 1:
            label = f"{pack} x {label}"
        return value * factor * pack, base, label
    if pack_m:
        return float(pack), "und", f"{pack} und"
    return None


def unit_price(price: float, qty: float, unit: str) -> tuple[float, str]:
    """Precio por kg, por litro o por unidad."""
    if unit == "g":
        return price / qty * 1000, "kg"
    if unit == "ml":
        return price / qty * 1000, "L"
    return price / qty, "und"
