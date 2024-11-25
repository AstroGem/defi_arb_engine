"""
Multi-DEX arbitrage opportunity scanner.
Compares prices across Uniswap V2/V3, SushiSwap, and PancakeSwap.
"""

import asyncio
import logging
from decimal import Decimal
from typing import List, Dict, Optional
from web3 import Web3

logger = logging.getLogger(__name__)

UNISWAP_V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
SUSHI_FACTORY = "0xC0AEe478e3658e2610c5F7A4A2E1777cE9e4f2Ac"

WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
USDT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
DAI  = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
WBTC = "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"

PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", "outputs": [
        {"name": "_reserve0", "type": "uint112"},
        {"name": "_reserve1", "type": "uint112"},
        {"name": "_blockTimestampLast", "type": "uint32"}
    ], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"},
]

FACTORY_ABI = [
    {"constant": True, "inputs": [
        {"name": "tokenA", "type": "address"},
        {"name": "tokenB", "type": "address"}
    ], "name": "getPair", "outputs": [{"name": "pair", "type": "address"}], "type": "function"},
]

TOKEN_PAIRS = [
    (WETH, USDC), (WETH, USDT), (WETH, DAI), (WETH, WBTC),
    (USDC, USDT), (USDC, DAI), (WBTC, USDC),
]


class ArbitrageScanner:
    def __init__(self, w3: Web3, config: dict):
        self.w3 = w3
        self.config = config
        self.dexes = config.get('dexes', [])
        self.min_profit = Decimal(str(config['trading']['min_profit_eth']))

    async def find_opportunities(self) -> List[Dict]:
        """Scan all DEX pairs for arbitrage opportunities."""
        opportunities = []

        for token_a, token_b in TOKEN_PAIRS:
            prices = {}

            for dex in self.dexes:
                if dex.get('chain', 'ethereum') != 'ethereum':
                    continue
                try:
                    price = self._get_price(dex, token_a, token_b)
                    if price and price > 0:
                        prices[dex['name']] = price
                except Exception as e:
                    logger.debug(f"Error getting price from {dex['name']}: {e}")

            if len(prices) < 2:
                continue

            sorted_prices = sorted(prices.items(), key=lambda x: x[1])
            cheapest_dex, cheapest_price = sorted_prices[0]
            expensive_dex, expensive_price = sorted_prices[-1]

            spread = (expensive_price - cheapest_price) / cheapest_price

            if spread > self.config['trading']['slippage_tolerance']:
                profit_estimate = self._estimate_profit(
                    cheapest_price, expensive_price,
                    Decimal(str(self.config['trading']['max_trade_size_eth']))
                )

                if profit_estimate >= self.min_profit:
                    opportunities.append({
                        'pair': f"{token_a[:8]}.../{token_b[:8]}...",
                        'token_a': token_a,
                        'token_b': token_b,
                        'buy_dex': cheapest_dex,
                        'sell_dex': expensive_dex,
                        'buy_price': cheapest_price,
                        'sell_price': expensive_price,
                        'spread': float(spread),
                        'profit_eth': profit_estimate,
                    })

        return sorted(opportunities, key=lambda x: x['profit_eth'], reverse=True)

    def _get_price(self, dex: dict, token_a: str, token_b: str) -> Optional[Decimal]:
        """Get the price of token_a in terms of token_b on a given DEX."""
        factory = self.w3.eth.contract(
            address=Web3.to_checksum_address(dex['factory']),
            abi=FACTORY_ABI
        )

        pair_address = factory.functions.getPair(
            Web3.to_checksum_address(token_a),
            Web3.to_checksum_address(token_b)
        ).call()

        if pair_address == '0x' + '0' * 40:
            return None

        pair = self.w3.eth.contract(
            address=Web3.to_checksum_address(pair_address),
            abi=PAIR_ABI
        )

        reserves = pair.functions.getReserves().call()
        token0 = pair.functions.token0().call()

        reserve_a = reserves[0] if token0.lower() == token_a.lower() else reserves[1]
        reserve_b = reserves[1] if token0.lower() == token_a.lower() else reserves[0]

        if reserve_a == 0:
            return None

        return Decimal(reserve_b) / Decimal(reserve_a)

    def _estimate_profit(self, buy_price: Decimal, sell_price: Decimal, trade_size: Decimal) -> Decimal:
        """Estimate profit for a given trade size, accounting for slippage."""
        slippage = Decimal(str(self.config['trading']['slippage_tolerance']))
        effective_buy = buy_price * (1 + slippage)
        effective_sell = sell_price * (1 - slippage)

        tokens_bought = trade_size / effective_buy
        revenue = tokens_bought * effective_sell
        profit = revenue - trade_size

        return max(profit, Decimal('0'))
