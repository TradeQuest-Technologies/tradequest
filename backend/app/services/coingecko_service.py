"""
CoinGecko market data service for cryptocurrency
"""

from pycoingecko import CoinGeckoAPI
from typing import List, Dict, Any, Optional
import structlog

logger = structlog.get_logger()

class CoinGeckoService:
    """Service for fetching crypto market data from CoinGecko (free API)"""
    
    def __init__(self):
        self.cg = CoinGeckoAPI()
    
    async def get_top_cryptos(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get top cryptocurrencies by market cap"""
        try:
            # Get market data for top coins
            markets = self.cg.get_coins_markets(
                vs_currency='usd',
                order='market_cap_desc',
                per_page=limit,
                page=1,
                sparkline=False,
                price_change_percentage='24h'
            )
            
            tickers = []
            for coin in markets:
                tickers.append({
                    "symbol": f"{coin['symbol'].upper()}/USD",
                    "name": coin['name'],
                    "price": coin['current_price'],
                    "change24h": coin['price_change_24h'] or 0,
                    "changePercent24h": (coin['price_change_percentage_24h'] or 0) / 100,  # Convert to decimal
                    "volume24h": coin['total_volume'] or 0,
                    "marketCap": coin['market_cap'] or 0,
                    "high24h": coin['high_24h'] or 0,
                    "low24h": coin['low_24h'] or 0,
                    "image": coin.get('image', ''),
                    "rank": coin.get('market_cap_rank', 0)
                })
            
            logger.info("Fetched top cryptos from CoinGecko", count=len(tickers))
            return tickers
            
        except Exception as e:
            logger.error("Failed to fetch from CoinGecko", error=str(e))
            return []
    
    async def search_crypto(self, query: str) -> List[Dict[str, Any]]:
        """Search for cryptocurrencies"""
        try:
            results = self.cg.search(query)
            coins = results.get('coins', [])
            
            search_results = []
            for coin in coins[:20]:  # Limit to 20 results
                search_results.append({
                    "symbol": coin['symbol'].upper(),
                    "name": coin['name'],
                    "id": coin['id'],
                    "market_cap_rank": coin.get('market_cap_rank', 0),
                    "image": coin.get('thumb', '')
                })
            
            return search_results
            
        except Exception as e:
            logger.error("Failed to search CoinGecko", error=str(e))
            return []
    
    async def get_crypto_details(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a specific cryptocurrency"""
        try:
            coin = self.cg.get_coin_by_id(
                id=coin_id,
                localization=False,
                tickers=False,
                market_data=True,
                community_data=False,
                developer_data=False
            )
            
            market_data = coin.get('market_data', {})
            
            return {
                "symbol": coin['symbol'].upper(),
                "name": coin['name'],
                "price": market_data.get('current_price', {}).get('usd', 0),
                "change24h": market_data.get('price_change_24h', 0),
                "changePercent24h": (market_data.get('price_change_percentage_24h', 0)) / 100,
                "volume24h": market_data.get('total_volume', {}).get('usd', 0),
                "marketCap": market_data.get('market_cap', {}).get('usd', 0),
                "high24h": market_data.get('high_24h', {}).get('usd', 0),
                "low24h": market_data.get('low_24h', {}).get('usd', 0),
                "ath": market_data.get('ath', {}).get('usd', 0),
                "atl": market_data.get('atl', {}).get('usd', 0),
                "description": coin.get('description', {}).get('en', ''),
                "image": coin.get('image', {}).get('large', '')
            }
            
        except Exception as e:
            logger.error("Failed to get crypto details", coin_id=coin_id, error=str(e))
            return None
