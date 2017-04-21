from pybitcointools import sign
from tx import TX
from wallet.wallet import generate_std_scriptpubkey, get_priv_key_hex


def build_raw_tx(prev_tx_id, prev_out_index, src_btc_addr, value, dest_btc_addr, scriptPubKey=None, scriptSig=None):

    assert len(prev_tx_id) == len(prev_out_index) == len(src_btc_addr)
    assert len(value) == len(dest_btc_addr)

    #ToDo: If the scriptPubKey is set, the dest_btc_addr is not used, so could be NULL

    if scriptPubKey is None:
        scriptPubKey = []
        for i in range(len(dest_btc_addr)):
            scriptPubKey.append(generate_std_scriptpubkey(dest_btc_addr[i]))
    else:
        assert len(scriptPubKey) == len(dest_btc_addr)

    tx = TX()

    if scriptSig is None:
        tx.build_p2pkh_std_tx(prev_tx_id, prev_out_index, value, scriptPubKey)
        raw_tx = tx.hex
        for i in range(len(src_btc_addr)):
            priv_key = src_btc_addr[i] + "/sk.pem"
            priv_key_hex = get_priv_key_hex(priv_key)
            raw_tx = sign(raw_tx, i, priv_key_hex)

    else:
        assert len(scriptPubKey) == len(src_btc_addr)
        tx.build_p2pkh_std_tx(prev_tx_id, prev_out_index, value, scriptPubKey, scriptSig)
        raw_tx = tx.hex

    return raw_tx

