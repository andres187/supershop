from dataclasses import dataclass


@dataclass(frozen=True)
class Store:
    key: str
    name: str
    base_url: str
    search_path: str
    color: str
    # Enlace estándar de VTEX que agrega SKUs al carrito real de la tienda.
    cart_path: str = "/checkout/cart/add"


STORES = [
    Store("olimpica", "Olímpica", "https://www.olimpica.com", "/api/catalog_system/pub/products/search", "#e30613"),
    Store("exito", "Éxito", "https://www.exito.com", "/io/api/catalog_system/pub/products/search", "#f5c400",
          "/io/checkout/cart/add"),
    Store("jumbo", "Jumbo", "https://www.jumbocolombia.com", "/api/catalog_system/pub/products/search", "#00a650"),
]
