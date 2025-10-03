"""
Market data endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.ticker import Ticker
from app.services.market_data import MarketDataService
from app.services.polygon_service import PolygonService
from app.services.coingecko_service import CoinGeckoService

logger = structlog.get_logger()
router = APIRouter()

@router.get("/tickers")
async def get_market_tickers(
    market_type: str = Query("stocks", description="Market type: stocks, crypto, forex"),
    limit: int = Query(50, description="Number of tickers to return"),
    current_user: User = Depends(get_current_user)
):
    """Get market tickers - Polygon for stocks, CoinGecko for crypto"""
    
    try:
        if market_type == "crypto":
            # For crypto, get from local database with live prices
            # First, get ticker symbols from database
            ticker_models = db.query(Ticker).filter(
                Ticker.market_type == 'crypto',
                Ticker.is_active == True
            ).order_by(Ticker.rank.asc()).limit(limit).all()
            
            if not ticker_models:
                # Fallback: fetch directly from CoinGecko if database is empty
                coingecko_service = CoinGeckoService()
                tickers = await coingecko_service.get_top_cryptos(limit)
            else:
                # Fetch live prices for these coins from CoinGecko
                coingecko_service = CoinGeckoService()
                coin_ids = [t.coin_id for t in ticker_models if t.coin_id]
                
                # Get prices for all coins in one request
                try:
                    prices_data = coingecko_service.cg.get_price(
                        ids=','.join(coin_ids),
                        vs_currencies='usd',
                        include_24hr_change=True,
                        include_24hr_vol=True
                    )
                    
                    tickers = []
                    for ticker_model in ticker_models:
                        if ticker_model.coin_id in prices_data:
                            price_info = prices_data[ticker_model.coin_id]
                            tickers.append({
                                "symbol": ticker_model.symbol,
                                "name": ticker_model.name,
                                "price": price_info.get('usd', 0),
                                "change24h": price_info.get('usd_24h_change', 0),
                                "changePercent24h": price_info.get('usd_24h_change', 0) / 100,
                                "volume24h": price_info.get('usd_24h_vol', 0),
                                "rank": ticker_model.rank
                            })
                except Exception as e:
                    logger.error("Failed to fetch crypto prices", error=str(e))
                    # Fallback to direct fetch
                    tickers = await coingecko_service.get_top_cryptos(limit)
            
            return {
                "market_type": market_type,
                "tickers": tickers,
                "count": len(tickers),
                "source": "CoinGecko"
            }
        
        elif market_type == "stocks":
            # Use Polygon for stocks (paid plan)
            polygon_service = PolygonService()
            tickers = await polygon_service.get_popular_tickers("stocks")
            
            return {
                "market_type": market_type,
                "tickers": tickers,
                "count": len(tickers),
                "source": "Polygon.io"
            }
        
        else:
            return {
                "market_type": market_type,
                "tickers": [],
                "count": 0
            }
        
    except Exception as e:
        logger.error("Failed to fetch tickers", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch market tickers: {str(e)}"
        )

@router.get("/ticker/{symbol}")
async def get_single_ticker(
    symbol: str,
    market_type: str = Query("stocks", description="Market type: stocks, crypto"),
    current_user: User = Depends(get_current_user)
):
    """Get data for a single ticker"""
    
    try:
        if market_type == "crypto":
            coingecko_service = CoinGeckoService()
            # For crypto, we'd need to get coin details
            return {"error": "Not implemented for crypto yet"}
        else:
            polygon_service = PolygonService()
            ticker_data = await polygon_service.get_stock_ticker(symbol)
            
            if not ticker_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Ticker {symbol} not found"
                )
            
            return ticker_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get ticker", symbol=symbol, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ticker: {str(e)}"
        )

@router.get("/search")
async def search_tickers(
    query: str = Query(..., description="Search query"),
    market_type: str = Query("stocks", description="Market type: stocks, crypto, fx"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for tickers - Polygon server-side for stocks, local DB for crypto"""
    
    try:
        if market_type == "stocks":
            # Use Polygon's server-side search (no local storage needed!)
            polygon_service = PolygonService()
            results = await polygon_service.search_tickers(query, market_type, limit=20)
            
            return {
                "query": query,
                "market_type": market_type,
                "results": results,
                "count": len(results)
            }
        
        elif market_type == "crypto":
            # For crypto, search local database (top 2500 coins)
            search_query = db.query(Ticker).filter(
                Ticker.market_type == 'crypto',
                Ticker.is_active == True
            )
            
            # Search by symbol or name (case-insensitive)
            search_term = f"%{query}%"
            search_query = search_query.filter(
                (Ticker.symbol.ilike(search_term)) | 
                (Ticker.name.ilike(search_term))
            )
            
            # Order by rank (lower rank = more popular)
            search_query = search_query.order_by(Ticker.rank.asc())
            
            # Limit to top 20 results
            results = search_query.limit(20).all()
            
            ticker_list = [{
                "symbol": t.symbol,
                "name": t.name,
                "market_type": t.market_type,
                "coin_id": t.coin_id,
                "rank": t.rank
            } for t in results]
            
            return {
                "query": query,
                "market_type": market_type,
                "results": ticker_list,
                "count": len(ticker_list)
            }
        
        else:
            return {
                "query": query,
                "market_type": market_type,
                "results": [],
                "count": 0
            }
        
    except Exception as e:
        logger.error("Failed to search tickers", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search tickers: {str(e)}"
        )

@router.get("/ohlcv")
async def get_ohlcv(
    symbol: str = Query(..., description="Trading pair symbol (e.g., BTC/USDT)"),
    tf: str = Query("1m", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(1000, description="Number of candles to fetch"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get OHLCV data for a symbol"""
    
    try:
        market_service = MarketDataService()
        candles = await market_service.get_ohlcv(symbol, tf, limit)
        
        return {
            "symbol": symbol,
            "timeframe": tf,
            "candles": candles,
            "count": len(candles)
        }
        
    except Exception as e:
        logger.error("Failed to fetch OHLCV", symbol=symbol, timeframe=tf, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch market data: {str(e)}"
        )

@router.post("/context")
async def get_trade_context(
    trade_data: dict,
    tf: str = Query("1m", description="Timeframe for context candles"),
    pre_mins: int = Query(60, description="Minutes before trade"),
    post_mins: int = Query(60, description="Minutes after trade"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get candles around a trade for context"""
    
    try:
        market_service = MarketDataService()
        
        # Extract trade info
        symbol = trade_data.get("symbol")
        filled_at = trade_data.get("filled_at")
        
        if not symbol or not filled_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trade must include symbol and filled_at"
            )
        
        # Parse datetime if it's a string
        if isinstance(filled_at, str):
            filled_at = datetime.fromisoformat(filled_at.replace('Z', '+00:00'))
        
        # Calculate time window
        start_time = filled_at - timedelta(minutes=pre_mins)
        end_time = filled_at + timedelta(minutes=post_mins)
        
        # Fetch candles
        candles = await market_service.get_ohlcv_range(symbol, tf, start_time, end_time)
        
        return {
            "trade": trade_data,
            "timeframe": tf,
            "pre_mins": pre_mins,
            "post_mins": post_mins,
            "candles": candles,
            "trade_timestamp": filled_at.isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to fetch trade context", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trade context: {str(e)}"
        )

@router.get("/symbols")
async def get_available_symbols(
    venue: Optional[str] = Query(None, description="Exchange venue (kraken, coinbase)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available trading symbols"""
    
    try:
        market_service = MarketDataService()
        symbols = await market_service.get_symbols(venue)
        
        return {
            "venue": venue or "all",
            "symbols": symbols,
            "count": len(symbols)
        }
        
    except Exception as e:
        logger.error("Failed to fetch symbols", venue=venue, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch symbols: {str(e)}"
        )
