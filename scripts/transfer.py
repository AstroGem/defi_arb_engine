#!/usr/bin/env python3
"""
Quick transfer script for moving funds between wallets.
Used for rebalancing before arb execution.

Usage:
    python scripts/transfer.py --from treasury --to executor --amount 5.0
    python scripts/transfer.py --consolidate  # move all to treasury
"""

import os
import json
import argparse
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{os.getenv('ALCHEMY_API_KEY')}"))

with open('config/wallets.json', 'r') as f:
    WALLETS = json.load(f)['wallets']


def transfer(from_wallet: str, to_wallet: str, amount_eth: float):
    """Transfer ETH between named wallets."""
    src = WALLETS[from_wallet]
    dst = WALLETS[to_wallet]

    account = w3.eth.account.from_key(src['private_key'])
    balance = w3.from_wei(w3.eth.get_balance(account.address), 'ether')

    print(f"From: {from_wallet} ({account.address}) — Balance: {balance} ETH")
    print(f"To:   {to_wallet} ({dst['address']})")
    print(f"Amount: {amount_eth} ETH")

    if float(balance) < amount_eth:
        print(f"ERROR: Insufficient balance ({balance} < {amount_eth})")
        return

    tx = {
        'nonce': w3.eth.get_transaction_count(account.address),
        'to': Web3.to_checksum_address(dst['address']),
        'value': w3.to_wei(amount_eth, 'ether'),
        'gas': 21000,
        'gasPrice': w3.eth.gas_price,
        'chainId': 1,
    }

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"✅ Transfer complete: {tx_hash.hex()}")
    print(f"   Gas used: {receipt['gasUsed']}")


def consolidate():
    """Move all funds to treasury wallet."""
    treasury = WALLETS['treasury']

    for name, wallet in WALLETS.items():
        if name == 'treasury':
            continue

        account = w3.eth.account.from_key(wallet['private_key'])
        balance = w3.eth.get_balance(account.address)

        gas_cost = 21000 * w3.eth.gas_price
        if balance <= gas_cost:
            print(f"  {name}: skipping (balance {w3.from_wei(balance, 'ether')} ETH <= gas)")
            continue

        send_amount = balance - gas_cost
        tx = {
            'nonce': w3.eth.get_transaction_count(account.address),
            'to': Web3.to_checksum_address(treasury['address']),
            'value': send_amount,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'chainId': 1,
        }

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"  {name}: sent {w3.from_wei(send_amount, 'ether')} ETH → treasury ({tx_hash.hex()})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--from', dest='from_wallet')
    parser.add_argument('--to', dest='to_wallet')
    parser.add_argument('--amount', type=float)
    parser.add_argument('--consolidate', action='store_true')
    args = parser.parse_args()

    if args.consolidate:
        consolidate()
    elif args.from_wallet and args.to_wallet and args.amount:
        transfer(args.from_wallet, args.to_wallet, args.amount)
    else:
        parser.print_help()
