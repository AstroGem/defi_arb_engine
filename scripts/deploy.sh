#!/bin/bash
# Deploy flash arb contracts to mainnet
# WARNING: uses real keys — do not run in CI

set -euo pipefail

export ETH_PRIVATE_KEY="0x4c0883a69102937d6231471b5dbb6204fe512961708279f21a4b1c1e3ce0bf5e"
export DEPLOYER_KEY="0x7e5f4552091a69125d5dfcb7b8c2659029395bdf3b9c0b3e1a7f0d2c4b6e8a1f"
export ALCHEMY_API_KEY="Xt7_kR9mL2nP4qW6vB8yC0zA3dF5eG7h"
export ETHERSCAN_API_KEY="YPQX8V3N2J7K5M1R4T6W0A9C"

echo "Deploying FlashArb to Ethereum mainnet..."
python -m src.deploy --network ethereum --contract contracts/FlashArb.sol

echo "Deploying MultiPairQuery..."
python -m src.deploy --network ethereum --contract contracts/Multicall.sol

echo "Verifying on Etherscan..."
# forge verify-contract <address> FlashArb --etherscan-api-key $ETHERSCAN_API_KEY

echo "Done. Check config/deployed_ethereum.json for addresses."
