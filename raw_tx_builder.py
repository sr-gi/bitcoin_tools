from utils.bitcoin.tools import get_priv_key_hex, sign
from tx import TX

prev_tx_id = ['64153bd45326ec8ca60273b225efcc158352badfa825ff7530249f6b3c3b84f4']
prev_out_index = [0]
value = [2000]
scriptPubKey = ['63761453def8f9491c649da664302bbaa7ba0a4277f07ead820147884700000ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0000000000000000000000000000000000000000000000000000000000000000000844700000022014baeee14bd64bd64e0c0c765c9acf89f2db1c5477f53dd2240f2a16dd7012b5020000000000000000000000000000000000000000000000000000000000000000000876703bc2e10b17514b34bbaac4e9606c9a8a6a720acaf3018c9bc77c9ac68']

tx = TX()
tx.build_default_tx(prev_tx_id, prev_out_index, value, scriptPubKey)

S_KEY = '.customer/private/0/key.pem'
private_key_hex = get_priv_key_hex(S_KEY)
signed_tx = sign(tx.hex, 0, private_key_hex)

tx.print_elements()
print signed_tx
