from app.categorize import classify
from app.compare import compare, relevant
from app.models import Offer
from app.normalize import parse_size, unit_price


def make(store, name, brand, price):
    o = Offer(store=store, store_name=store, name=name, brand=brand, price=price, list_price=price, link="x")
    size = parse_size(name)
    if size:
        o.size_qty, o.size_unit, o.size_label = size
        o.unit_price, o.unit_price_label = unit_price(price, o.size_qty, o.size_unit)
    o.product_type = classify(name, o.size_unit)
    return o


def test_brand_search_drops_noise():
    offers = [
        make("exito", "Plastilina Fab Jumbo FABER CASTELL", "FABER CASTELL", 9790),
        make("olimpica", "DETERG POLV FAB ULTRA BLANCO 2KG", "Fab", 30000),
    ]
    assert [o.store for o in relevant(offers, "fab")] == ["olimpica"]


def test_synonyms_and_abbreviations():
    offers = [
        make("jumbo", "Crema Dental Colgate 100 mL", "COLGATE", 10000),
        make("exito", "Dispensador de cepillos", "GENERICO", 5000),
    ]
    assert [o.store for o in relevant(offers, "pasta dental")] == ["jumbo"]
    assert relevant([make("olimpica", "DETERG POLV ARIEL 1KG", "Ariel", 1)], "detergente ariel")


def test_best_offer_uses_unit_price_within_type():
    offers = [
        make("olimpica", "Detergente Fab Polvo 1kg", "Fab", 12000),  # 12.000/kg
        make("jumbo", "Detergente Fab en Polvo 3kg", "FAB", 30000),  # 10.000/kg
        make("exito", "Jabón de barra FAB 300 gr", "FAB", 2338),  # 7.793/kg, pero es otro tipo
        make("exito", "Detergente Fab Liquido 1L", "FAB", 9000),
    ]
    groups = {g["type"]: g for g in compare(offers, "fab")["groups"]}
    assert set(groups) == {"Detergente en polvo", "Jabón en barra", "Detergente líquido"}
    polvo = groups["Detergente en polvo"]
    assert polvo["unit"] == "kg"
    assert polvo["best_offer"].store == "jumbo"
    assert groups["Detergente líquido"]["best_by_store"]["exito"].price == 9000


def test_groups_ranked_by_store_coverage():
    offers = [
        make("exito", "Jabón de barra FAB 300 gr", "FAB", 2338),
        make("exito", "Jabón de barra FAB 200 gr", "FAB", 1800),
        make("olimpica", "Detergente Fab Polvo 1kg", "Fab", 12000),
        make("jumbo", "Detergente Fab en Polvo 3kg", "FAB", 30000),
    ]
    assert compare(offers, "fab")["groups"][0]["type"] == "Detergente en polvo"


def test_head_and_shoulders_variants():
    offers = [
        make("olimpica", "Shampoo Head & Shoulders Anticomezón 1 L", "H & S", 40000),
        make("exito", "Shampoo H&S hidratación aceite de coco (375 ml)", "H&S", 20000),
        make("jumbo", "Shampoo Head Shoulders Anti-Comezón 375ml", "HEAD & SHOULDERS", 21000),
        make("jumbo", "Play Set Head Dino Play and Joy", "PLAY AND JOY", 50000),
    ]
    for query in ["head and shoulder", "head & shoulders", "head shoulders", "h&s"]:
        assert {o.store for o in relevant(offers, query)} == {"olimpica", "exito", "jumbo"}, query
        assert all("Dino" not in o.name for o in relevant(offers, query)), query
