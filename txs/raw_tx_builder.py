from bitcoin import sign
from tx import TX
from wallet.wallet import generate_std_scriptpubkey, get_priv_key_hex


def build_raw_tx(prev_tx_id, prev_out_index, src_btc_addr, value, dest_btc_addr):

    assert len(prev_tx_id) == len(prev_out_index) == len(src_btc_addr)
    assert len(value) == len(dest_btc_addr)

    scriptPubKey = []
    for i in range(len(dest_btc_addr)):
        scriptPubKey.append(generate_std_scriptpubkey(dest_btc_addr[i]))

    tx = TX()
    tx.build_p2pkh_std_tx(prev_tx_id, prev_out_index, value, scriptPubKey)

    signed_tx = ""
    for i in range(len(src_btc_addr)):
        priv_key = src_btc_addr[i] + "/sk.pem"
        priv_key_hex = get_priv_key_hex(priv_key)
        signed_tx = sign(tx.hex, i, priv_key_hex)

    tx.print_elements()
    return signed_tx

