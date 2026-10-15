"""Schema dei dati estratti da una fattura, con validazione."""
from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

TOLERANCE = 0.02   # euro di tolleranza negli arrotondamenti


class LineItem(BaseModel):
    description: str = Field(description="Descrizione della riga, come scritta nel documento")
    quantity: int = Field(ge=1, description="Quantita'")
    unit_price: float = Field(ge=0, description="Prezzo unitario al netto di IVA")


class Invoice(BaseModel):
    invoice_number: str = Field(description="Numero della fattura (non il numero d'ordine)")
    issue_date: date = Field(description="Data di emissione, formato YYYY-MM-DD")
    due_date: date | None = Field(description="Data di scadenza del pagamento, YYYY-MM-DD; null se assente")
    supplier_name: str = Field(description="Ragione sociale del fornitore")
    supplier_vat: str | None = Field(description="Partita IVA del fornitore; null se assente")
    currency: str = Field(description="Codice ISO 4217 a 3 lettere, per esempio EUR")
    line_items: list[LineItem] = Field(description="Righe della fattura")
    net_total: float = Field(description="Imponibile totale")
    vat_amount: float = Field(description="Importo totale dell'IVA")
    total_amount: float = Field(description="Totale del documento, IVA inclusa")

    @field_validator("currency")
    @classmethod
    def currency_is_iso(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError(f"valuta non valida: {value!r}")
        return value

    @model_validator(mode="after")
    def totals_are_consistent(self) -> "Invoice":
        """Controllo semantico senza risposta attesa: i conti devono tornare."""
        items_sum = sum(item.quantity * item.unit_price for item in self.line_items)
        if abs(items_sum - self.net_total) > TOLERANCE:
            raise ValueError(
                f"la somma delle righe ({items_sum:.2f}) non coincide con l'imponibile ({self.net_total:.2f})"
            )
        if abs(self.net_total + self.vat_amount - self.total_amount) > TOLERANCE:
            raise ValueError("imponibile + IVA non coincide con il totale")
        return self