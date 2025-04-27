# Stonks

A Python application for tracking financial instrument prices from various sources.

## Features

- Support for multiple data sources:
  - JustETF
  - Yahoo Finance
  - Tel Aviv Stock Exchange (TASE)
- Configurable symbol tracking
- Automatic price updates
- Data persistence
- Robust error handling
- Type-safe implementation

## Project Structure

```
stonks/
├── src/
│   └── stonks/
│       ├── __init__.py
│       ├── app.py
│       ├── config.py
│       ├── models.py
│       ├── providers.py
│       └── storage.py
├── symbols/
│   └── *.json
├── dist/
├── main.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/stonks.git
cd stonks
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Symbol tracking is configured using JSON files in the `symbols` directory. Each file should have the following structure:

```json
{
    "id": "unique_symbol_id",
    "symbol": "SYMBOL",
    "currency": "USD",
    "source": "yahoo_finance",
    "type": "etf"  // Optional, used for TASE
}
```

Supported sources:
- `justetf`: JustETF API
- `yahoo_finance`: Yahoo Finance API
- `issa`: Tel Aviv Stock Exchange

## Usage

Run the application:
```bash
python main.py
```

The application will:
1. Read all symbol configuration files from the `symbols` directory
2. Fetch current prices from the configured sources
3. Save the results in the `dist` directory

## Development

### Code Style

The project uses:
- Black for code formatting
- Flake8 for linting
- MyPy for type checking

Run the development tools:
```bash
# Format code
black src/

# Run linter
flake8 src/

# Run type checker
mypy src/
```

### Testing

Run tests with pytest:
```bash
pytest
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

