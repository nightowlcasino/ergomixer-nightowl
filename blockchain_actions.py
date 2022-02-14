import json
import requests
from base58conv import hex_to_base58
import asyncio
import ast
import time
from conf import headers, owl_token_id, usd_token_id


def proxy_contract_builder(address):
    # Proxy Contract is unsafe, node can spend user funds.
    ergotree = hex_to_base58(json.loads(requests.get(
        'http://127.0.0.1:9053/script/addressToTree/'+address, headers=headers).text)['tree'])
    payload = {
        "source": "PK(\"9hKFHa886348VhfM1BRfLPKi8wwXMnyVqqmri9p5zPFE8qgMMui\") && CONTEXT.preHeader.timestamp >" +str(int(time.time_ns()/10000000)) +"L"
    }
    return json.loads(requests.post(
        'http://127.0.0.1:9053/script/p2sAddress', json=payload, headers=headers).text)['address']


def get_mixer(address_list, token_amount_user, tokenId):
    request = []
    splits = []
    while token_amount_user > 0:
        if token_amount_user >= 5000:
            splits.append(5000)
            token_amount_user -= 5000
        elif token_amount_user >= 1000:
            splits.append(1000)
            token_amount_user -= 1000
        elif token_amount_user >= 200:
            splits.append(200)
            token_amount_user -= 200
    for i in range(len(splits)):
        mixed_output = {
            "amount": 1000000,
            "withdraw": address_list[0],
            "token": 30,
            "mixingTokenId": tokenId,
            "mixingTokenAmount": splits[i]
        }
        request.append(mixed_output)
        address_list.append(address_list.pop(0))
    mix_response = json.loads(requests.get(
        'http://localhost:9000/mix/request/list').text)
    return mix_response[-1]['deposit'], mix_response[-1]['amount'], mix_response[-1]['mixingTokenAmount']


async def spend_proxy(p2s, address, mixer_withdraws):
    # User input
    boxId_resp = requests.get('https://api.ergoplatform.com/api/v1/boxes/byAddress/' + p2s)
    counter = 0
    while int(json.loads(boxId_resp.text)['total']) == 0:
        await asyncio.sleep(25)
        boxId_resp = requests.get('https://api.ergoplatform.com/api/v1/boxes/byAddress/' + p2s)
        counter += 1
        if counter > 144:
            return
    input_box = json.loads(boxId_resp.text)['items'][0]['boxId']
    bin_box_user = [json.loads(requests.get('http://127.0.0.1:9053/utxo/byIdBinary/' + input_box).text)['bytes']]

    tokens = json.loads(boxId_resp.text)['items'][0]['assets'][0]
    token_amount_user = tokens['amount']
    token_id_user = tokens['tokenId']
    # Swap Contract Input
    boxId_resp = requests.get('https://api.ergoplatform.com/api/v1/boxes/byAddress/4CUZWUFcK7rujNiNFVWbqfw7mUYoXcsVxvzB6Xwipg62gQBgfHKrJJGy7SUnyZy76HUNXGGoBBW4w7y4V7bASVTfbTVSfDV1TL9iBmt6ixY5a6LMqbgswC2XqYHBnwDuQCmp3iqDRMQKz9KhPQkU7vcms3mmBsvj9frFFrZ55Z1y6CDZP64eyHRcD9xf85G43KELM6SXihFXPPnVejxUfCZpbfhVdoX6CDPZCHtPP7U1YGxxgvtoLfAP4TfJZpEhikNE37exxrVMApefetP7NnPa7aCXcx52i4NagdrwdJDTsTxuefitNdJGX8Q3zFf35zyCEciQY3qViDop59cjnmEDRhtpQroVPTPcHXcv4m41Na7jKBcGrV1eyqhQkLSwruJuiwBUybkHyCSYUgxuHjPG3DDTgsBHv55nUQzeswp9yfRzigrfhp')
    input_box = json.loads(boxId_resp.text)['items'][0]['boxId']
    bin_box_swap = [json.loads(requests.get('http://127.0.0.1:9053/utxo/byIdBinary/' + input_box).text)['bytes']]
    tokens = json.loads(boxId_resp.text)['items'][0]['assets']
    owl_amount_swap = tokens[0]['amount']
    usd_amount_swap = tokens[1]['amount']
    if token_id_user == owl_token_id:
        token_id_user = usd_token_id
        owls_in = token_amount_user
        usds_in = token_amount_user * - 1
    else:
        token_id_user = owl_token_id
        owls_in = token_amount_user * - 1
        usds_in = token_amount_user
    value = 1000000
    if mixer_withdraws:
        mixer_response = get_mixer(mixer_withdraws, token_amount_user, token_id_user)
        address = mixer_response[0]
        value = mixer_response[1]
    # Build Transaction
    transaction_to_sign = \
        {
            "requests": [
                {
                    "address": address,
                    "value": value,
                    "assets": [
                        {
                            "tokenId": token_id_user,
                            "amount": token_amount_user
                        }
                    ]
                },
                {
                    "address": "4CUZWUFcK7rujNiNFVWbqfw7mUYoXcsVxvzB6Xwipg62gQBgfHKrJJGy7SUnyZy76HUNXGGoBBW4w7y4V7bASVTfbTVSfDV1TL9iBmt6ixY5a6LMqbgswC2XqYHBnwDuQCmp3iqDRMQKz9KhPQkU7vcms3mmBsvj9frFFrZ55Z1y6CDZP64eyHRcD9xf85G43KELM6SXihFXPPnVejxUfCZpbfhVdoX6CDPZCHtPP7U1YGxxgvtoLfAP4TfJZpEhikNE37exxrVMApefetP7NnPa7aCXcx52i4NagdrwdJDTsTxuefitNdJGX8Q3zFf35zyCEciQY3qViDop59cjnmEDRhtpQroVPTPcHXcv4m41Na7jKBcGrV1eyqhQkLSwruJuiwBUybkHyCSYUgxuHjPG3DDTgsBHv55nUQzeswp9yfRzigrfhp",
                    "value": 1000000,
                    "assets": [
                        {
                            "tokenId": owl_token_id,
                            "amount": owl_amount_swap + owls_in
                        },
                        {
                            "tokenId": usd_token_id,
                            "amount": usd_amount_swap + usds_in
                        }
                    ]
                }

            ],
            "fee": 1000000,
            "inputsRaw":
                bin_box_user + bin_box_swap
            }

    transaction_gen_resp= requests.post("http://127.0.0.1:9053/wallet/transaction/generate",
                                            json=transaction_to_sign,
                                            headers=headers).text
    requests.post("http://127.0.0.1:9053/transactions", json=ast.literal_eval(transaction_gen_resp),
                                        headers=headers)

