import json
import subprocess

import quart
import quart_cors
from quart import request

from web3 import Web3

ERC20_ABI = """
[
	{
		"constant": true,
		"inputs": [
			{
				"name": "_owner",
				"type": "address"
			}
		],
		"name": "balanceOf",
		"outputs": [
			{
				"name": "balance",
				"type": "uint256"
			}
		],
		"payable": false,
		"stateMutability": "view",
		"type": "function"
	}
]
"""
ETHEREUM_NODE_ADDRESS = "https://mainnet.infura.io/v3/<API_KEY>"
connection = Web3(Web3.HTTPProvider(ETHEREUM_NODE_ADDRESS))

app = quart_cors.cors(quart.Quart(__name__), allow_origin="*")

_globalVariable = {}

@app.post("/converteth/<path:amount>")
async def convert_eth(amount):
	request_data = await request.get_json(force=True)
	amount = int(amount)
	balance = connection.from_wei(amount, 'ether')
	return quart.Response(response=json.dumps({ "ether": float(balance) }), status=200)

@app.post("/convertwei/<path:amount>")
async def convert_wei(amount):
	request_data = await request.get_json(force=True)
	print("[!] Raw Request for /convertwei " + str(amount))
	amount = float(amount)
	balance = connection.to_wei(amount, 'ether')
	return quart.Response(response=json.dumps({ "wei": int(balance) }), status=200)

@app.post("/getbalance/<path:address>")
async def get_balance(address):
	request_data = await request.get_json(force=True)
	print("[!] Raw Request for /getbalance " + str(address))
	balance = connection.eth.get_balance(address)
	return quart.Response(response=json.dumps({ "wei": balance }), status=200)

@app.post("/getblock/<path:num>")
async def get_block(num):
	request_data = await request.get_json(force=True)
	print("[!] Raw Request for /getblock " + str(num))
	num = int(num)
	block = connection.eth.get_block(int(num)) #idk why typing keeps causing issues
	data = {
		'difficulty': block['difficulty'],
		'extraData': block['extraData'].hex(),
		'gasLimit': block['gasLimit'],
		'gasUsed': block['gasUsed'],
		'hash': block['hash'].hex(),
		'logsBloom': block['logsBloom'].hex(),
		'miner': block['miner'],
		'mixHash': block['mixHash'].hex(),
		'nonce': block['nonce'].hex(),
		'number': block['number'],
		'parentHash': block['parentHash'].hex(),
		'receiptsRoot': block['receiptsRoot'].hex(),
		'sha3Uncles': block['sha3Uncles'].hex(),
		'size': block['size'],
		'stateRoot': block['stateRoot'].hex(),
		'timestamp': block['timestamp'],
		'totalDifficulty': block['totalDifficulty'],
		'transactions': list(map(lambda x: x.hex(), block['transactions'])),
		'transactionsRoot': block['transactionsRoot'].hex(),
		'uncles': block['uncles']
	}
	return quart.Response(response=json.dumps(data), status=200)

@app.post("/gettransaction/<path:txid>")
async def get_transaction(txid):
	request_data = await request.get_json(force=True)
	print("[!] Raw Request for /gettransaction " + txid)
	transaction = connection.eth.get_transaction(txid)
	data = {
		'accessList': list(map(lambda x: dict(x), transaction['accessList'])),
		'blockHash': transaction['blockHash'].hex(),
		'blockNumber': transaction['blockNumber'],
		'chainId': transaction['chainId'],
		'from': transaction['from'],
		'gas': transaction['gas'],
		'gasPrice': transaction['gasPrice'],
		'hash': transaction['hash'].hex(),
		'input': transaction['input'],
		'maxFeePerGas': transaction['maxFeePerGas'],
		'maxPriorityFeePerGas': transaction['maxPriorityFeePerGas'],
		'nonce': transaction['nonce'],
		'r': transaction['r'].hex(),
		's': transaction['s'].hex(),
		'to': transaction['to'],
		'transactionIndex': transaction['transactionIndex'],
		'type': transaction['type'],
		'v': transaction['v'],
		'value': transaction['value']
	}
	return quart.Response(response=json.dumps(data), status=200)

@app.post("/getcode/<path:contract>")
async def get_code(contract):
	request_data = await request.get_json(force=True)
	print("[!] Raw Request for /getcode " + str(request_data))
	code = connection.eth.get_code(contract)
	return quart.Response(response=json.dumps({ 'code': code.hex() }), status=200)

@app.get("/blocknumber")
async def get_blocknumber():
	print("[!] Raw Request for /blocknumber")
	block = connection.eth.block_number
	return quart.Response(response=json.dumps({ "block_number": block }), status=200)

#Incomplete
'''
@app.post("/estimate_gas/<path:transferInfo>")
async def estimate_gas(transferInfo):
	request_data = await request.get_json(force=True)
	print("[!] Raw Request for /estimate_gas " + str(request_data))
	sender = str(request_data['sender'])
	recevier = str(request_data['recevier'])
	amount = int(request_data['amount'])
	contract = None if "contract" not in request_data.keys() else str(request_data['contract'])
	if contract != None:
		data = {
			'from': sender,
			'to': recevier,
			'value': amount
		}
		try:
			gas = connection.eth.estimate_gas(data)
			return quart.Response(response=json.dumps({}), status=200) #Incomplete
		except ValueError as e:
			return quart.Response(response=json.dumps({ 'error': 'Failed to estimate gas.' }), status=401)
	else:
		erc20_abi = json.loads(ERC20_ABI)
		contract = connection.eth.contract(address=contract, abi=erc20_abi)
		transfer_params = contract.encode_function_call('transfer', [recevier, amount])
		data = {
			'from': sender,
			'to': receiver,
			'value': 0,
			'data': tansfer_data
		}
		try:
			gas = connection.eth.estimate_gas(data)
			return quart.Response(response=json.dumps({}), status=200) #Incomplete
		except ValueError as e:
			return quart.Response(response=json.dumps({ 'error': 'Failed to estimate gas.' }), status=401)

@app.post("/transfer/<path:transferInfo>")
async def transfer(transferInfo):
	request_data = await request.get_json(force=True)
	print("[!] Raw Request for /transfer " + str(request_data))
	key = str(request_data['key'])
	amount = int(request_data['amount'])
	to = str(request_data['to'])
	contract = None if "contract" not in request_data.keys() else str(request_data['contract'])
	sender = connection.eth.account.privateKeyToAccount(key).address
	balance = connection.eth.get_balance(sender)
	if balance < amount:
		return quart.Response(response=json.dumps({ 'error': 'The requested transfer is larger then the account balance.' }), status=401)
	gasPrice = connection.eth.gas_price
	gasLimit = connection.eth.estimate_gas({'from': sender, 'to': to, 'value': amount})
	tx = {
		'from': sender,
		'to': to,
		'value': amount,
		'gas': gasLimit,
		'gasPrice': gasPrice,
		'nonce': connection.web3.getTransactionCount(sender)
	}
	signedTx = connection.eth.account.sign_transaction(tx, private_key=key)
	txHash = web3.eth.send_raw_transaction(signedTx.rawTransaction)
	return quart.Response(response=json.dumps({ "txid": txHash }), status=200)
'''

@app.get("/logo.png")
async def plugin_logo():
	filename = 'logo.png'
	return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
	host = request.headers['Host']
	with open("./.well-known/ai-plugin.json") as f:
		text = f.read()
		return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openai_spec():
	host = request.headers['Host']
	with open("openapi.yaml") as f:
		text = f.read()
		return quart.Response(text, mimetype="text/yaml")

def main():
	app.run(debug=True, host="0.0.0.0", port=3333)

if __name__ == "__main__":
	main()
