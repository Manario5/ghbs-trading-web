import asyncio
import os
os.environ["MARKET_DATA_PROVIDER"] = "yfinance"
from backend.services.market_data_service import MarketDataService

async def main():
    s = MarketDataService()
    try:
        m = s.get_symbol_map()
        print("symbol map length:", len(m))
    except Exception as e:
        print("ERROR:", str(e))

asyncio.run(main())
