from bitcoin_tools.core.transaction import TX

#################################################
#       Advanced Raw transaction building       #
#                 P2MS -> P2MS                  #
#################################################
# ---------------------------------------------------------------------------------------------------------------------
# The following piece of code serves as an example of how to build a P2MS transaction. Funds will be redeemed from a
# Pay-to-multisig address, and m-out of-n signatures will be required from different keys.
# - The library store keys using a Bitcoin address as an identifier. If you need more information about generating and
# storing / loading keys, refer to key_management.py / basic_raw_tx_creation.py examples.
# - First of all we will select an unspent transaction output (UTXO) of type P2MS, by choosing the proper prev_tx_id and
# index.
# - Then we should define the amount to be transferred and the fees.
# - Now we are ready to build the transaction. We can use the input/output constructor to do so.
# - Finally, we should sign the transaction using all m-out of-n required private keys. Notice that the order of the in
# which the keys are provided must match with the order in which the public keys where defined in the previous tx output
# script.
# - Finally we can serialize the transaction and display it to check that all worked!
# ---------------------------------------------------------------------------------------------------------------------

# Reference to the previous transaction output that will be used to redeem and spend the funds, consisting on an id and
# an output index.
prev_tx_id = "adcd6d269d5e0713fa9650099e9ab54ebf845a0d95f3740b44361bdb287959a7"
prev_out_index = 0

# Amount to be spent, in Satoshis, and the fee to be deduced (should be calculated).
value = 6163910
fee = 230 * 240

# Destination Bitcoin address where the value in bitcoins will be sent and locked until the owner redeems it.
destination_btc_addr = "mwryy9YdVezq2Wo1DukA5ADhrNemqCKTmy"

# First, we  build our transaction from io (input/output) using the previous transaction references, the value, and the
# destination.
tx = TX.build_from_io(prev_tx_id, prev_out_index, value - fee, destination_btc_addr)
# Finally, the transaction is signed using the private key associated with the Bitcoin address from each input.
# Input 0 will be signed, since we have only created one.
tx.sign(sk, 0)

# Once created we can display the serialized transaction. Transaction is now ready to be broadcast.
print "hex: " + tx.serialize()

# Finally, we can analyze each field of the transaction.
tx.display()
