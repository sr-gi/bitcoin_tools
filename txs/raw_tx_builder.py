from bitcoin import sign
from tx import TX
from wallet.wallet import generate_std_scriptpubkey, get_priv_key_hex


def build_raw_tx(prev_tx_id, prev_out_index, value, src_btc_addr, destination_btc_addr):

    assert len(prev_tx_id) == len(prev_out_index) == len(value) == len(src_btc_addr)

    scriptPubKey = []
    for i in range(len(destination_btc_addr)):
        scriptPubKey.append(generate_std_scriptpubkey(destination_btc_addr[i]))

    tx = TX()
    tx.build_default_tx(prev_tx_id, prev_out_index, value, scriptPubKey)

    for i in range(len(src_btc_addr)):
        S_KEY = src_btc_addr[i] + "/sk.pem"
        private_key_hex = get_priv_key_hex(S_KEY)
        signed_tx = sign(tx.hex, 0, private_key_hex)

    tx.print_elements()
    return signed_tx

