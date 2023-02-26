from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from web3 import Web3
from web3.contract import Contract, ContractFunction

app = FastAPI()

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545')) # initialize Web3 provider with Ethereum node endpoint
NULL_ADDRESS = '0x0000000000000000000000000000000000000000'

# ABI and contract address of the TrocEntreAmis smart contract
abi = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "id",
                "type": "uint256"
            }
        ],
        "name": "findItem",
        "outputs": [
            {
                "components": [
                    {
                        "internalType": "address",
                        "name": "owner",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "id",
                        "type": "uint256"
                    },
                    {
                        "internalType": "string",
                        "name": "name",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "description",
                        "type": "string"
                    },
                    {
                        "internalType": "uint256",
                        "name": "value",
                        "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                        "name": "status",
                        "type": "uint256"
                    }
                ],
                "internalType": "struct TrocEntreAmis.Item memory",
                "name": "",
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "name",
                "type": "string"
            },
            {
                "internalType": "string",
                "name": "description",
                "type": "string"
            },
            {
                "internalType": "uint256",
                "name": "value",
                "type": "uint256"
            },
            {
                "internalType": "uint256",
                "name": "status",
                "type": "uint256"
            }
        ],
        "name": "addItem",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
      "inputs":[
         {
            "internalType":"uint256",
            "name":"id",
            "type":"uint256"
         },
         {
            "internalType":"string",
            "name":"name",
            "type":"string"
         },
         {
            "internalType":"string",
            "name":"description",
            "type":"string"
         },
         {
            "internalType":"uint256",
            "name":"value",
            "type":"uint256"
         },
         {
            "internalType":"uint256",
            "name":"status",
            "type":"uint256"
         }
      ],
      "name":"updateItem",
      "outputs":[
         {
            "components":[
               {
                  "internalType":"address",
                  "name":"owner",
                  "type":"address"
               },
               {
                  "internalType":"uint256",
                  "name":"id",
                  "type":"uint256"
               },
               {
                  "internalType":"string",
                  "name":"name",
                  "type":"string"
               },
               {
                  "internalType":"string",
                  "name":"description",
                  "type":"string"
               },
               {
                  "internalType":"uint256",
                  "name":"value",
                  "type":"uint256"
               },
               {
                  "internalType":"uint256",
                  "name":"status",
                  "type":"uint256"
               }
            ],
            "internalType":"struct TrocEntreAmis.Item",
            "name":"",
            "type":"tuple"
         }
      ],
      "stateMutability":"nonpayable",
      "type":"function"
   },
   {
      "inputs":[
         {
            "internalType":"address",
            "name":"newOwner",
            "type":"address"
         },
         {
            "internalType":"uint256",
            "name":"id",
            "type":"uint256"
         }
      ],
      "name":"transferOwnership",
      "outputs":[
         
      ],
      "stateMutability":"nonpayable",
      "type":"function"
   }
]

contract_address = "0x..." # address of the deployed contract on the blockchain

# connect to the Arbitrum testnet node
web3 = Web3(Web3.HTTPProvider('https://rinkeby.arbitrum.io/rpc'))

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
    status: int

class Item(ItemBase):
    id: int
    owner: str
    status: int

class ItemTransfer(BaseModel):
    new_owner: str

class ContractLogicError(Exception):
    pass

@app.get("/items")
def read_items():
    items = []
    for i in range(contract.functions.itemsLength().call()):
        item = contract.functions.findItem(i).call()
        items.append(Item(id=item[1], owner=item[0], name=item[2], description=item[3], value=item[4], status=item[5]))
    return items

@app.get("/items/{item_id}")
def read_item(item_id: int):
    try:
        item = contract.functions.findItem(item_id).call()
    except:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(id=item[1], owner=item[0], name=item[2], description=item[3], value=item[4], status=item[5])

@app.post("/items")
def create_item(item: ItemCreate):
    txn = contract.functions.addItem(item.name, item.description, item.value, 1).buildTransaction({
        'from': web3.eth.accounts[0],
        'gas': 1000000,
        'gasPrice': web3.toWei('1', 'gwei')
    })
    signed_txn = web3.eth.account.sign_transaction(txn, private_key='<YOUR_PRIVATE_KEY>') # replace with your private key
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(txn_hash)
    item_id = receipt['events'][0]['args']['id']
    return read_item(item_id)

@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemUpdate):
    try:
        item_in_contract = contract.functions.findItem(item_id).call()
    except:
        raise HTTPException(status_code=404, detail="Item not found")
    if item_in_contract[0] != web3.eth.accounts[0]:
        raise HTTPException(status_code=403, detail="Not authorized")
    txn = contract.functions.updateItem(item_id, item.name, item.description, item.value, item.status).buildTransaction({
        'from': web3.eth.accounts[0],
        'gas': 1000000,
        'gasPrice': web3.toWei('1', 'gwei')
    })
    signed_txn = web3.eth.account.sign_transaction(txn, private_key='<YOUR_PRIVATE_KEY>') # replace with your private key
    txn_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    web3.eth.wait_for_transaction_receipt(txn_hash)
    return read_item(item_id)

@app.patch("/items/{item_id}/transfer-owner")
def transfer_owner(item_id: int, new_owner: str, request: Request):
    try:
        item = contract.functions.findItem(item_id).call()
        current_owner = item[0]
        if current_owner != request.client.host:
            raise HTTPException(status_code=401, detail="Only the current owner can transfer ownership")
        if new_owner == NULL_ADDRESS:
            raise HTTPException(status_code=400, detail="New owner address cannot be null")

        contract.functions.transferOwnership(new_owner, item_id).transact()
        return JSONResponse(content={"message": f"Item {item_id} ownership transferred to {new_owner}"})
    except ContractLogicError as e:
        raise HTTPException(status_code=404, detail="Item not found")

