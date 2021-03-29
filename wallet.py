# importing libraries
from constants import *
import os
from dotenv import load_dotenv
import subprocess
import json
from eth_account import Account
from bit import PrivateKeyTestnet
from web3 import Web3
from web3.middleware import geth_poa_middleware
from bit.network import NetworkAPI

load_dotenv()

# calling mnemonic environment variable
mnemonic = os.getenv('MNEMONIC')

# function to derive wallets
def derive_wallets(mnemonic, coin, numderive):
    """Use the subprocess library to call the php file script from Python"""
    command = f'php ./hd-wallet-derive/hd-wallet-derive.php -g --mnemonic="{mnemonic}" --numderive="{numderive}" --coin="{coin}" --format=json' 
    
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    
    keys = json.loads(output)
    return  keys
# function to call derive_wallets function for BTCTEST and ETH currencies and output a dictionary
# with derived information for three accounts per coin
def coins ():

    coin_dict = {
        'btc' : derive_wallets(mnemonic, BTC, 3),
        'btc-test' : derive_wallets(mnemonic, BTCTEST, 3),
        'eth' : derive_wallets(mnemonic, ETH, 3),
        'ltc' : derive_wallets(mnemonic, LTC, 3)
    }
    
    return coin_dict

# function to convert private key into a readable format for web3 / bit
def priv_key_to_account (coin, priv_key):
    
    if coin == ETH:
        return Account.privateKeyToAccount(priv_key)
    elif coin == BTCTEST:
        return PrivateKeyTestnet(priv_key)

# setting sender ETH account
eth_account = priv_key_to_account(ETH,coins()[ETH][0]['privkey'])

# setting a receiver ETH address
eth_address = coins()[ETH][1]['address']

# setting sender BTCTEST account
btctest_account = priv_key_to_account(BTCTEST,coins()[BTCTEST][0]['privkey'])

# setting a receiver BTCTEST address
btctest_address = coins()[BTCTEST][1]['address']

# setting up Web3 port
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# connect to local ETH/ geth
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# function to create raw, unsigned transaction
def create_tx(coin, account, to, amount):
    if coin == ETH:
        gasEstimate = w3.eth.estimateGas({
            "from": account.address, 
            "to": to, 
            "value": w3.toWei(amount,'ether') 
        })
        return {
            "from": account.address,
            "to": to,
            "value": w3.toWei(amount,'ether') ,
            "gas": gasEstimate,
            "gasPrice": w3.eth.gasPrice,
            "nonce": w3.eth.getTransactionCount(account.address),
            #"chainID": w3.net.chainId --this has been deprecated
        }
    elif coin == BTCTEST:
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])
    
# function to create, sign, and send transaction 
def send_tx(coin, account, recipient, amount):
    
    raw_tx = create_tx(coin, account, recipient, amount)
    signed_tx = account.sign_transaction(raw_tx)
    
    if coin == ETH:
        result = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return result.hex()
    elif coin == BTCTEST:
        return NetworkAPI.broadcast_tx_testnet(signed_tx)

# BTC Testnet Transaction
btc_acc = priv_key_to_account(BTCTEST,btc_PrivateKey)

# create BTC transaction
create_tx(BTCTEST,btctest_account,btctest_address, 0.00000001)

# sending BTCTEST transaction
send_tx(BTCTEST,btctest_account,btctest_address,0.0001)

# ETH-Transaction double check if  I am connected to blockchain. 
w3.isConnected()

# setting sender ETH account
eth_account = priv_key_to_account(ETH,coins()[ETH][1]['privkey'])
#display the account address
print("Account Address:",eth_account.address)
# Display balances
bal_from = w3.eth.getBalance(eth_account.address)
bal_to = w3.eth.getBalance("0x63F4319fd95C861175332e08B5b9D4bcaA280785")

print(f'Balance in source: {bal_from}. Balance in target: {bal_to}')

#create ETH transaction
create_tx(ETH,eth_account,"0x63F4319fd95C861175332e08B5b9D4bcaA280785", 400)

# sending ETH transaction
send_tx(ETH, eth_account,"0x63F4319fd95C861175332e08B5b9D4bcaA280785", 400)

#confirm the transaction
w3.eth.getBalance("0x63F4319fd95C861175332e08B5b9D4bcaA280785")