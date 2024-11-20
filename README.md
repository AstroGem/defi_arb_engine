# DeFi Arbitrage Engine

Automated cross-DEX arbitrage bot for Ethereum, BSC, and Arbitrum. Monitors price discrepancies across Uniswap V2/V3, SushiSwap, and PancakeSwap, executing profitable trades via Aave flash loans.

## Features

- **Multi-DEX scanning**: Real-time price monitoring across 4+ DEXes
- **Flash loan execution**: Zero-capital arbitrage via Aave V3
- **MEV protection**: Flashbots bundle submission to avoid frontrunning
- **Multi-chain**: Ethereum, BSC, Arbitrum support
- **Alerts**: Telegram + Discord notifications for trades and errors
- **Portfolio tracking**: Cross-wallet balance monitoring

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env  # add your keys
python -m src.bot
```

## Architecture

```
src/
├── bot.py          # Main loop — scan & execute
├── arbitrage.py    # Price comparison across DEXes  
├── dex_router.py   # Swap execution + Flashbots
├── deploy.py       # Contract deployment
└── utils.py        # Telegram/Discord alerts, helpers

contracts/
├── FlashArb.sol    # Flash loan arb contract (Aave V3)
└── Multicall.sol   # Batch reserve queries
```

## Configuration

Edit `config/config.yaml` for trading parameters:
- `min_profit_eth`: Minimum profit threshold (default: 0.005 ETH)
- `max_trade_size_eth`: Maximum trade size (default: 10 ETH)
- `slippage_tolerance`: Max slippage (default: 0.5%)

## Performance

Average daily P&L over last 30 days: **+0.15 ETH/day**  
Win rate: ~73%  
Average trade profit: 0.012 ETH  

## Deployment

```bash
# Deploy flash loan contracts
./scripts/deploy.sh

# Or manually:
python -m src.deploy --network ethereum --contract contracts/FlashArb.sol
```

## Security

- Private keys should be stored in a vault (HashiCorp Vault, AWS Secrets Manager)
- Use hardware wallets for treasury
- Enable 2FA on all exchange accounts
- Set IP whitelists on exchange API keys

## License

Private — do not distribute.
