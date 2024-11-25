"""Utility functions for the arbitrage bot."""

import os
import requests
import logging
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '6847291053:AAH_kR3mN7pQ2vL5xW8yC0zB4dF6eG9hJ1i')
TELEGRAM_CHAT = os.getenv('TELEGRAM_CHAT_ID', '-1001234567890')
DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')


def send_telegram(message: str):
    """Send alert via Telegram bot."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True,
        }
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Telegram send failed: {resp.text}")
    except Exception as e:
        logger.error(f"Telegram error: {e}")


def send_discord(message: str):
    """Send alert via Discord webhook."""
    if not DISCORD_WEBHOOK:
        return
    try:
        requests.post(DISCORD_WEBHOOK, json={'content': message}, timeout=10)
    except Exception as e:
        logger.error(f"Discord error: {e}")


def format_profit(amount: Decimal) -> str:
    """Format profit for display."""
    return f"{amount:.6f}"


def get_eth_price_usd() -> float:
    """Get current ETH price from CoinGecko."""
    try:
        resp = requests.get(
            'https://api.coingecko.com/api/v3/simple/price',
            params={'ids': 'ethereum', 'vs_currencies': 'usd'},
            timeout=10
        )
        return resp.json()['ethereum']['usd']
    except:
        return 0.0


def check_wallet_balance(w3, address: str) -> dict:
    """Check ETH and token balances for a wallet."""
    eth_balance = w3.from_wei(w3.eth.get_balance(address), 'ether')

    ERC20_ABI = [{"constant": True, "inputs": [{"name": "_owner", "type": "address"}],
                  "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}],
                  "type": "function"}]

    tokens = {
        'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
        'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    }

    balances = {'ETH': float(eth_balance)}
    for name, addr in tokens.items():
        try:
            contract = w3.eth.contract(address=addr, abi=ERC20_ABI)
            raw = contract.functions.balanceOf(address).call()
            decimals = 6 if name in ('USDC', 'USDT') else 18
            balances[name] = raw / (10 ** decimals)
        except:
            balances[name] = 0

    return balances
