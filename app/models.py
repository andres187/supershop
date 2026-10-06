from dataclasses import asdict, dataclass


@dataclass
class Offer:
    store: str
    store_name: str
    name: str
    brand: str
    price: float
    list_price: float
    link: str
    image: str | None = None
    seller: str | None = None
    sku_id: str | None = None
    seller_id: str | None = None
    size_qty: float | None = None  # en g, ml o und
    size_unit: str | None = None  # "g" | "ml" | "und"
    size_label: str | None = None
    unit_price: float | None = None  # $ por kg, L o und
    unit_price_label: str | None = None
    product_type: str = "Otros"

    @property
    def discount_pct(self) -> int:
        if self.list_price and self.list_price > self.price:
            return round((1 - self.price / self.list_price) * 100)
        return 0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["discount_pct"] = self.discount_pct
        return d
