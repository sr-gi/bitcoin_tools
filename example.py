from txs.raw_tx_builder import build_raw_tx
from wallet.keys import generate_keys, store_keys
from wallet.wallet import generate_wif, generate_btc_addr

#################################################
# Key management and Bitcoin address generation #
#################################################

# First of all the elliptic curve keys are generated.
ec = generate_keys()
# The Bitcoin address is derived from the public key created above.
btc_addr = generate_btc_addr(ec.pub(), v='test')
# Both the public and private key are stored in disk. The Bitcoin address is used as an identifier in the name
# of the file.
store_keys(ec, btc_addr)
# Finally, the private key is encoded as WIF and also stored in disk, ready to be imported in a wallet.
generate_wif(btc_addr, mode='image', v='test')

#################################################
#           Raw transaction building            #
#################################################

# ---------------------------------------------------------------------------------------------------------------------
# Down bellow he inputs of the raw transaction builder can be found. Each item should be inserted in the corresponding
# list, separated by commas.
# ---------------------------------------------------------------------------------------------------------------------

# Reference to the previous transaction where the funds will be redeemed and spent. Consists in an id an a output.
prev_tx_id = ['64153bd45326ec8ca60273b225efcc158352badfa825ff7530249f6b3c3b84f4']
prev_out_index = [0]
# Amount to be spent, in Satoshis.
value = [2000]
# Bitcoin address where the bitcoins come from. It should match with the address referenced by the prev_tx_id.
# The address will be used as an identifier to choose the proper keys when signing the transaction.
# Use the above generated Bitcoin address (btc_addr), or load some previously generated ones using the Bitcoin
# address that matches with the folder names.
src_btc_addr = [btc_addr]
# Destination Bitcoin address, where the value in bitcoins will be sent, and lock until the owner redeems it.
destination_btc_addr = ["mkpKXgxN9tqoFDosG2Rjh1KvqrteXZ1kk9"]

# Build the raw transaction using all the provided inputs.
signed_tx = build_raw_tx(prev_tx_id, prev_out_index, value, src_btc_addr, destination_btc_addr)

# Display the transaction
print signed_tx
