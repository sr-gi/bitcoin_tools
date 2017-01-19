from txs.raw_tx_builder import build_raw_tx
from wallet.keys import generate_keys, store_keys, load_keys
from wallet.wallet import generate_wif, generate_btc_addr

#################################################
# Key management and Bitcoin address generation #
#################################################
# Uncomment this part to generate fresh keys and Bitcoin address

# First of all the elliptic curve keys are generated.
sk, pk = generate_keys()
# The Bitcoin address is derived from the public key created above.
btc_addr = generate_btc_addr(pk.to_der(), v='test')
# Both the public and private key are stored in disk. The Bitcoin address is used as an identifier in the name
# of the folder that contains both keys.
store_keys(sk.to_pem(), pk.to_pem(), btc_addr)
# Finally, the private key is encoded as WIF and also stored in disk, ready to be imported in a wallet.
generate_wif(btc_addr, mode='image', v='test')


#################################################
# Key loading, if they'd been already generated #
#################################################
# Uncomment this part to load already generated keys. Replace the Bitcoin address for the one that matches yours.

# btc_addr = "mwryy9YdVezq2Wo1DukA5ADhrNemqCKTmy"
# sk, pk = load_keys(btc_addr)

#################################################
#           Raw transaction building            #
#################################################

# ---------------------------------------------------------------------------------------------------------------------
# Down bellow he inputs of the raw transaction builder can be found. Each item should be inserted in the
# corresponding list, separated by commas.
# ---------------------------------------------------------------------------------------------------------------------

# Reference to the previous transaction where the funds will be redeemed and spent. Consists in an id and
# an output index.
prev_tx_id = ['a5a985ee80a68434c46f9f3216b7fe294cd6de9c82f3bcf119ad6ab4c2e13e49']
prev_out_index = [1]
# Amount to be spent, in Satoshis.
value = [75000]
# Bitcoin address where the bitcoins come from. It should match with the address referenced by the prev_tx_id.
# The address will be used as an identifier to choose the proper keys when signing the transaction.
# Use the above generated Bitcoin address (btc_addr), or load some previously generated ones using the Bitcoin
# address that matches with the folder names.
src_btc_addr = [btc_addr]
# Destination Bitcoin address where the value in bitcoins will be sent and locked until the owner redeems it.
destination_btc_addr = ["mwryy9YdVezq2Wo1DukA5ADhrNemqCKTmy"]

# Finally, the raw transaction can be build using all the provided inputs.
# ToDo: Choose how to deal with fees. Currently they are set as minimum by default and can not be changed.
signed_tx = build_raw_tx(prev_tx_id, prev_out_index, src_btc_addr, value, destination_btc_addr)

# Displays the transaction.
print "hex: " + signed_tx
