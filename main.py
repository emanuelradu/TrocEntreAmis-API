from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from web3 import Web3
from web3.contract import Contract, ContractFunction

app = FastAPI()

NULL_ADDRESS = '0x0000000000000000000000000000000000000000'

# ABI and contract address of the TrocEntreAmis smart contract
abi = [{"inputs":[{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"description","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"addItem","outputs":[{"components":[{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"description","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"status","type":"uint256"}],"internalType":"struct TrocEntreAmis.Item","name":"","type":"tuple"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"id","type":"uint256"}],"name":"findItem","outputs":[{"components":[{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"description","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"status","type":"uint256"}],"internalType":"struct TrocEntreAmis.Item","name":"","type":"tuple"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getAll","outputs":[{"components":[{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"description","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"status","type":"uint256"}],"internalType":"struct TrocEntreAmis.Item[]","name":"","type":"tuple[]"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"},{"internalType":"uint256","name":"id","type":"uint256"}],"name":"transferOwnership","outputs":[{"components":[{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"description","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"status","type":"uint256"}],"internalType":"struct TrocEntreAmis.Item","name":"","type":"tuple"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"description","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"}],"name":"updateItem","outputs":[{"components":[{"internalType":"uint256","name":"id","type":"uint256"},{"internalType":"address","name":"owner","type":"address"},{"internalType":"string","name":"name","type":"string"},{"internalType":"string","name":"description","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"},{"internalType":"uint256","name":"status","type":"uint256"}],"internalType":"struct TrocEntreAmis.Item","name":"","type":"tuple"}],"stateMutability":"nonpayable","type":"function"}]

contract_address = "0x9cc40BaC75FED80d5B69e6A48D5014DD8CFb11A4" # address of the deployed contract on the blockchain
my_wallet_address = "0000" # address of the owner
my_private_key = "0000" # pk of the owner

# connect to the Arbitrum blockchain
web3 = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))

my_wallet = web3.toChecksumAddress(my_wallet_address)
transactionCount = web3.eth.getTransactionCount(my_wallet) - 1

# check if web3 is connected to the network
if web3.isConnected():
    print('Connected to Arbitrum testnet')
else:
    print('Failed to connect to Arbitrum testnet')

# Initialize contract instance
contract = web3.eth.contract(address=contract_address, abi=abi)

class ItemBase(BaseModel):
    name: str
    description: str
    value: int

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    owner: str
    status: int

class ItemTransfer(BaseModel):
    new_owner: str
    id: int
class ContractLogicError(Exception):
    pass

def getIncrementedTransactionCount():
    global transactionCount
    transactionCount += 1
    return transactionCount

@app.get("/items")
def read_items():
    items = []
    print(contract.functions.getAll().call())
    for item in contract.functions.getAll().call():
        items.append(Item(id=item[0], owner=item[1], name=item[2], description=item[3], value=item[4], status=item[5]))
    return items

@app.get("/items/{item_id}")
def read_item(item_id: int):
    try:
        item = contract.functions.findItem(item_id).call()
    except:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(id=item[0], owner=item[1], name=item[2], description=item[3], value=item[4], status=item[5])

@app.post("/items")
def create_item(item: ItemCreate):
    txn = contract.functions.addItem(item.name, item.description, item.value).buildTransaction({
        'from': my_wallet,
        'gas': 1000000,
        'gasPrice': web3.toWei('1', 'gwei'),
        'nonce': getIncrementedTransactionCount()
    })
    signed_txn = web3.eth.account.sign_transaction(txn, private_key=my_private_key)
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    return str(txn_hash)

@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemUpdate):
    try:
        item_in_contract = contract.functions.findItem(item_id).call()
    except:
        raise HTTPException(status_code=404, detail="Item not found")
    if item_in_contract[1] != my_wallet_address:
        raise HTTPException(status_code=403, detail="Not authorized")
    txn = contract.functions.updateItem(item_id, item.name, item.description, item.value).buildTransaction({
        'from': my_wallet,
        'gas': 1000000,
        'gasPrice': web3.toWei('1', 'gwei'),
        'nonce': getIncrementedTransactionCount()
    })
    signed_txn = web3.eth.account.sign_transaction(txn, private_key=my_private_key) # replace with your private key
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    web3.eth.wait_for_transaction_receipt(txn_hash)
    return read_item(item_id)

@app.patch("/items/transfer-owner")
def transfer_owner(item: ItemTransfer):
    try:
        item_in_contract = contract.functions.findItem(item.id).call()
    except :
        raise HTTPException(status_code=404, detail="Item not found")
    
    if item_in_contract[1] != my_wallet_address:
        raise HTTPException(status_code=403, detail="Not authorized")
    if item.new_owner == NULL_ADDRESS:
        raise HTTPException(status_code=400, detail="New owner address cannot be null")

    txn = contract.functions.transferOwnership(item.new_owner, item.id).buildTransaction({
        'from': my_wallet,
        'gas': 1000000,
        'gasPrice': web3.toWei('1', 'gwei'),
        'nonce': getIncrementedTransactionCount()
    })
    signed_txn = web3.eth.account.sign_transaction(txn, private_key=my_private_key) # replace with your private key
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    web3.eth.wait_for_transaction_receipt(txn_hash)
    
    return JSONResponse(content={"message": f"Item {item.id} ownership transferred to {item.new_owner}"})
    

