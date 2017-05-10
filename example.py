from tx.tx import TX
from wallet.keys import generate_keys, store_keys, load_keys
from wallet.wallet import generate_wif, generate_btc_addr

#################################################
# Key management and Bitcoin address generation #
#################################################
# ---------------------------------------------------------------------------------------------------------------------
# Uncomment down bellow to generate fresh keys and Bitcoin address.
# ---------------------------------------------------------------------------------------------------------------------

# First of all the elliptic curve keys are generated.
sk, pk = generate_keys()
# The Bitcoin address is derived from the public key created above.
btc_addr = generate_btc_addr(pk, v='test')
# Both the public and private key are stored in disk. The Bitcoin address is used as an identifier in the name
# of the folder that contains both keys.
store_keys(sk.to_pem(), pk.to_pem(), btc_addr)
# Finally, the private key is encoded as WIF and also stored in disk, ready to be imported in a wallet.
generate_wif(btc_addr, sk, mode='image', v='test')

#################################################
#               Key loading                     #
#################################################
# ---------------------------------------------------------------------------------------------------------------------
# Uncomment down bellow to load already generated keys. Replace the Bitcoin address for the one that matches yours.
# ---------------------------------------------------------------------------------------------------------------------

# btc_addr = "mwryy9YdVezq2Wo1DukA5ADhrNemqCKTmy"
# sk, pk = load_keys(btc_addr)

#################################################
#           Raw transaction building            #
#################################################
# ---------------------------------------------------------------------------------------------------------------------
# Down bellow and example of how to build a transaction can be found. Funds will be redeemed from the already
# generated (or loaded) Bitcoin address. Notice that, in order to work, there should be funds hold by the address.
# Change prev_tx_id, prev_out_index and value for the corresponding ones, and make sure that the loaded keys match with
# the Bitcoin address that information is referring to.
# ---------------------------------------------------------------------------------------------------------------------

# Reference to the previous transaction where the funds will be redeemed and spent. Consists in an id and
# an output index.
prev_tx_id = "7767a9eb2c8adda3ffce86c06689007a903b6f7e78dbc049ef0dbaf9eeebe075"
prev_out_index = 0

# Amount to be spent, in Satoshis, and the fee to be deduced (should be calculated).
value = 6163910
# ToDo: Choose how to deal with fees.
fee = 230 * 240

# Destination Bitcoin address where the value in bitcoins will be sent and locked until the owner redeems it.
destination_btc_addr = "mwryy9YdVezq2Wo1DukA5ADhrNemqCKTmy"

# Now, the raw transaction can be built.
# First, we construct a transaction object
tx = TX()
# Next, we  build out transaction from io (input/output) using the previous transaction references, the value, and the
# destination.
tx.build_from_io(prev_tx_id, prev_out_index, value - fee, destination_btc_addr)
# Finally, the transaction is signed using the private key associated with the Bitcoin address from each input.
# Input 0 will be signed, since we have only created one input.
tx.sign(sk, 0)

# Once created we can display the serialized transaction. Transaction is now ready to be broadcast.
print "hex: " + tx.serialize()

# Finally, we can analyze each field of the transaction.
tx.deserialize()



