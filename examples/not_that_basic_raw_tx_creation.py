from bitcoin_tools.core.keys import load_keys
from bitcoin_tools.core.transaction import TX

#################################################
#               Key loading                     #
#################################################
# ---------------------------------------------------------------------------------------------------------------------
# The following piece of code loads an already generated ECDSA key pair from disk (check key_management.py if you
# haven't generated a key pair yet).
# - You should replace the Bitcoin address for the one that matches yours.
# ---------------------------------------------------------------------------------------------------------------------

btc_addr = "mqrCarJrAvXrSQXpupd9i52hgYkaPVdyck"
sk, pk = load_keys(btc_addr)

#################################################
#  Not that basic Raw transaction building      #
#        P2PKH -> P2PKH, P2PKH (2 outputs)      #
#################################################
# ---------------------------------------------------------------------------------------------------------------------
# The following piece of code serves as an example of how to build a P2PKH transaction. Funds will be redeemed from the
# already loaded Bitcoin address (Notice that, in order to work, there should be funds hold by the address).
# - You will build a transaction that spends from a P2PKH output and generates a two new P2PKH outputs.
# - You should change prev_tx_id, prev_out_index and value for the ones who match with an unspent transaction output
# from your recently generated address.
# - Choose a fee big enough to pay for the transaction inclusion into a block. You can use https://bitcoinfees.21.co/ to
# figure out the current fee-per-byte ratio.
# - Choose the transaction destination addresses.
# - Build the transaction using the basic constructor.
# - Sign and broadcast the transaction.
# ---------------------------------------------------------------------------------------------------------------------

# Reference to the previous transaction output that will be used to redeem and spend the funds, consisting on an id and
# an output index.
prev_tx_id = "131b785c8afb42844fbc4d93566afa34b6ee457687033f818d6a301416994397"
prev_out_index = 0

# Amount to be spent, in Satoshis, and the fee to be deduced (should be calculated).
fee = 230 * 240
value = [100000000, 66614329 - fee]

# Destination Bitcoin addresses where the values in bitcoins will be sent and locked until the owner(s) redeems them.
destination_btc_addr = ["miWdbNn9zDLnKpcNuCLdfRiJx59c93bT8t", "mmp3aVcmdM9PKDj1FQZtBqK9nBnx1eNhPf"]

# First, we  build our transaction from io (input/output) using the previous transaction references, the values, and the
# destinations.
tx = TX.build_from_io(prev_tx_id, prev_out_index, value, destination_btc_addr)
# Finally, the transaction is signed using the private key associated with the Bitcoin address from each input.
# Input 0 will be signed, since we have only created one.
tx.sign(sk, 0)

# Once created we can display the serialized transaction. Transaction is now ready to be broadcast.
print "hex: " + tx.serialize()

# Finally, we can analyze each field of the transaction.
tx.display()
