import pytest

from app.normalize import parse_size, unit_price


@pytest.mark.parametrize("name,qty,unit", [
    ("DETERG POLV FAB ULTRA BLANCO 2KG", 2000, "g"),
    ("BLANQ LIMPIDO BOT GEL 1000ML", 1000, "ml"),
    ("Limpido Gel 1000 ml", 1000, "ml"),
    ("Detergente Fab Ultra Flash Líquido 1.3lt", 1300, "ml"),
    ("Detergente 1,5 Kg", 1500, "g"),
    ("Pasta Dental Oral-B Protección 100% de tu Boca* Cuidada 3 Und de 66 mL", 198, "ml"),
    ("Pasta Dental Con Flúor Oral-B Complete 4En1 x6und x80g c-u", 480, "g"),
    ("Crema Dental Oral-B 3D White Blanqueadora, 2 Uds, 67 mL", 134, "ml"),
    ("Crema Dental Oral-B Extra Blancura con Bicarbonato, 3 Unidades de 100 mL", 300, "ml"),
    ("Pasta Dental Oral-B Kids Minnie/Mickey, 1 Ud, 50 g", 50, "g"),
    ("Crema Dental Fluocardent Triple Acción Max 50ml Gratis 22ml", 50, "ml"),
    ("Jabón líquido DOVE deep moisture corporal (591  ml)", 591, "ml"),
    ("Pasta Dental Con Propoleo Atomy 200 Grms", 200, "g"),
    ("Jabón corporal Dove liquido moisture x325ml", 325, "ml"),
    ("Pasta Dental ORAL B 3Dw X24It SRP (67  ml)", 67, "ml"),
    ("Pasta Dental Oral-B Protección Cuidada 3 Und", 3, "und"),
    ("Jabon Rey x3", 3, "und"),
])
def test_parse_size(name, qty, unit):
    parsed = parse_size(name)
    assert parsed is not None
    assert parsed[0] == pytest.approx(qty)
    assert parsed[1] == unit


def test_parse_size_unknown():
    assert parse_size("Pasta Dental De Turmalina Negra Hgw 100% Natural") is None


def test_unit_price():
    assert unit_price(20000, 2000, "g") == (10000, "kg")
    assert unit_price(7400, 1000, "ml") == (7400, "L")
    assert unit_price(9000, 3, "und") == (3000, "und")
