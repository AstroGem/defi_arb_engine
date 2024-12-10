#!/usr/bin/env python3
"""
Deploy flash loan arbitrage contracts.
Usage: python -m src.deploy --network ethereum
"""

import os
import json
import argparse
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv

load_dotenv()

DEPLOYER_KEY = os.getenv('DEPLOYER_KEY', '0x7e5f4552091a69125d5dfcb7b8c2659029395bdf3b9c0b3e1a7f0d2c4b6e8a1f')

NETWORKS = {
    'ethereum': {
        'rpc': os.getenv('ALCHEMY_WSS', '').replace('wss://', 'https://').replace('/v2/', '/v2/'),
        'chain_id': 1,
    },
    'bsc': {
        'rpc': os.getenv('BSC_RPC', 'https://bsc-dataseed1.binance.org'),
        'chain_id': 56,
    },
    'arbitrum': {
        'rpc': os.getenv('ARB_RPC'),
        'chain_id': 42161,
    }
}


def compile_contract(contract_path: str) -> dict:
    """Compile a Solidity contract."""
    install_solc('0.8.19')

    with open(contract_path, 'r') as f:
        source = f.read()

    compiled = compile_standard({
        "language": "Solidity",
        "sources": {os.path.basename(contract_path): {"content": source}},
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}
        }
    }, solc_version='0.8.19')

    contract_name = os.path.basename(contract_path).replace('.sol', '')
    contract_data = compiled['contracts'][os.path.basename(contract_path)][contract_name]

    return {
        'abi': contract_data['abi'],
        'bytecode': contract_data['evm']['bytecode']['object']
    }


def deploy(network: str, contract_path: str):
    """Deploy contract to specified network."""
    net = NETWORKS[network]
    w3 = Web3(Web3.HTTPProvider(net['rpc']))
    account = w3.eth.account.from_key(DEPLOYER_KEY)

    print(f"Deploying from: {account.address}")
    print(f"Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

    compiled = compile_contract(contract_path)

    contract = w3.eth.contract(abi=compiled['abi'], bytecode=compiled['bytecode'])

    tx = contract.constructor().build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 3000000,
        'gasPrice': w3.eth.gas_price,
        'chainId': net['chain_id'],
    })

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"Contract deployed at: {receipt['contractAddress']}")
    print(f"Tx hash: {tx_hash.hex()}")

    with open(f'config/deployed_{network}.json', 'w') as f:
        json.dump({
            'address': receipt['contractAddress'],
            'tx_hash': tx_hash.hex(),
            'abi': compiled['abi'],
            'deployer': account.address,
            'network': network,
        }, f, indent=2)

    return receipt['contractAddress']


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--network', default='ethereum', choices=NETWORKS.keys())
    parser.add_argument('--contract', default='contracts/FlashArb.sol')
    args = parser.parse_args()
    deploy(args.network, args.contract)
