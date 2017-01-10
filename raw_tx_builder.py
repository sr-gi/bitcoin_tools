from bitcoin import sign
from tx import TX
from simplified_tools.wallet import generate_std_scriptpubkey, get_priv_key_hex

prev_tx_id = ['64153bd45326ec8ca60273b225efcc158352badfa825ff7530249f6b3c3b84f4']
prev_out_index = [0]
value = [2000]
destination_btc_addr = ["mkpKXgxN9tqoFDosG2Rjh1KvqrteXZ1kk9"]
scriptPubKey = []

for i in range(len(destination_btc_addr)):
    scriptPubKey.append(generate_std_scriptpubkey(destination_btc_addr[i]))

tx = TX()
tx.build_default_tx(prev_tx_id, prev_out_index, value, scriptPubKey)

source_btc_addr = ""
S_KEY = source_btc_addr + "_key.pem"
private_key_hex = get_priv_key_hex(S_KEY)
signed_tx = sign(tx.hex, 0, private_key_hex)

tx.print_elements()
print signed_tx
