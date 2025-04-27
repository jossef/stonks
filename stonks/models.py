"""Data models for the Stonks application."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SymbolTrackInfo:
    """Information about a tracked symbol."""
    id: str
    symbol: str
    currency: str
    source: str
    type: Optional[str] = None
    price: Optional[float] = None
    price_date: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'SymbolTrackInfo':
        """Create a SymbolTrackInfo instance from a dictionary."""
        return cls(
            id=data['id'],
            symbol=data['symbol'],
            currency=data['currency'],
            source=data['source'],
            type=data.get('type'),
            price=data.get('price'),
            price_date=data.get('price_date')
        )

    def to_dict(self) -> dict:
        """Convert the instance to a dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'currency': self.currency,
            'source': self.source,
            'type': self.type,
            'price': self.price,
            'price_date': self.price_date
        }

@dataclass
class PriceData:
    """Price data for a symbol."""
    symbol: str
    price: float
    currency: str
    date: datetime
    source: str

    @property
    def formatted_date(self) -> str:
        """Get the date in YYYY-MM-DD format."""
        return self.date.strftime('%Y-%m-%d') 