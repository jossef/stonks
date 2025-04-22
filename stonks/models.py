"""
Data models for the Stonks application.

This module defines the data structures used throughout the application.
"""
from dataclasses import dataclass
from datetime import date
from typing import Optional, Literal, Dict, Any


@dataclass
class SymbolConfig:
    """Configuration for a financial symbol to track."""
    id: str
    type: Literal["etf", "caspit"]
    source: Literal["justetf", "yahoo_finance", "issa"]
    symbol: str
    currency: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SymbolConfig':
        """
        Create a SymbolConfig instance from a dictionary.
        
        Args:
            data: Dictionary containing symbol configuration
            
        Returns:
            A new SymbolConfig instance
        """
        return cls(
            id=data["id"],
            type=data["type"],
            source=data["source"],
            symbol=data["symbol"],
            currency=data["currency"]
        )


@dataclass
class SymbolData:
    """Data for a financial symbol including price information."""
    config: SymbolConfig
    price: float
    price_date: str
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the symbol data to a dictionary.
        
        Returns:
            Dictionary representation of the symbol data
        """
        return {
            "id": self.config.id,
            "type": self.config.type,
            "source": self.config.source,
            "symbol": self.config.symbol,
            "currency": self.config.currency,
            "price": self.price,
            "price_date": self.price_date
        }