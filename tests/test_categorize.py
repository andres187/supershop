import pytest

from app.categorize import classify


@pytest.mark.parametrize("name,unit,expected", [
    ("DETERG POLV FAB ULTRA BLANCO 2KG", "g", "Detergente en polvo"),
    ("Detergente Fab Ultra Flash en Poltvo 5kg", "g", "Detergente en polvo"),
    ("Detrgente Fab Ultra Flash Vibra Color en Polvo 2kg", "g", "Detergente en polvo"),
    ("Detergente Fab Ultra Flash Líquido 1.3lt", "ml", "Detergente líquido"),
    ("DETERG LIQ FAB ULTRA COLOR X 3000ML", "ml", "Detergente líquido"),
    ("Pack x2 Detergente en polvo FAB 5kg", "g", "Detergente en polvo"),
    ("Jabón de barra FAB ultra flash floral (300  gr)", "g", "Jabón en barra"),
    ("Jabon Fab Barra Ultraflash Arrancagrasa Limon x300grs", "g", "Jabón en barra"),
    ("Lava Plato Fab Lozamax Limón Botella 700 ML", "ml", "Lavaplatos líquido"),
    ("L/PLATO FAB LOZAMAX DW CITRUS BOT 700", None, "Lavaplatos"),
    ("Limpia Pisos Fabuloso Antibacterial Lavanda 5 lt", "ml", "Limpiador"),
    ("BLANQ LIMPIDO BOT GEL 1000ML", "ml", "Blanqueador gel"),
    ("Blanqueador Multiusos Límpido Limón x1800ml", "ml", "Blanqueador líquido"),
    ("Crema Dental Oral B Extra Blancura con Bicarbonato 150 ml", "ml", "Crema dental"),
    ("Pasta Dental Con Propoleo Atomy 200 Grms", "g", "Crema dental"),
    ("Jabón Líquido Corporal Palmolive Café 390 Ml", "ml", "Jabón líquido corporal"),
    ("Jabón corporal Dove liquido moisture x591ml", "ml", "Jabón líquido corporal"),
    ("Jabon de Tocador Dove Original 90 g", "g", "Jabón en barra"),
    ("Crema Dental Oral-B 3D White Blanqueadora, 2 Uds, 67 mL", "ml", "Crema dental"),
    ("Crema Gel Dental Sin Fluor Combo 3 Unidades", "und", "Crema dental"),
    ("Jabón Liquido Corporal Disney Princesas", None, "Jabón líquido corporal"),
    ("Jabon Barra Piel Sensible con Crema Corporal con Serum Pantenol", None, "Jabón en barra"),
    ("Plastilina Fab Jumbo FABER CASTELL", None, "Otros"),
])
def test_classify(name, unit, expected):
    assert classify(name, unit) == expected
