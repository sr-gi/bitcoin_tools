from bitcoin_tools.core.keys import load_keys, serialize_pk
from bitcoin_tools.core.transaction import TX
from json import load

#################################################
#       Advanced Raw transaction building       #
#                 P2MS -> P2MS                  #
#################################################
# ---------------------------------------------------------------------------------------------------------------------
# The following piece of code serves as an example of how to build a P2MS transaction. Funds will be redeemed from a
# Pay-to-multisig address, and m-out of-n signatures will be required from different keys.
# - The library store keys using a Bitcoin address as an identifier. If you need more information about generating and
# storing / loading keys, refer to key_management.py / basic_raw_tx_creation.py examples.
# - First of all we will select an unspent transaction output (UTXO) of type P2MS. This time, we will load it from a
# file.
# - Then the fees will be set.
# - Once all the data is defined, we will be ready to build the transaction. We can use the input/output constructor to
# do so.
# - Finally, we should sign the transaction using all m-out of-n required private keys. Notice that the order in which
# the keys are provided must match with the order in which the public keys where defined in the previous tx output
# script.
# - Finally we wil serialize the transaction and display it to check that all worked!
# ---------------------------------------------------------------------------------------------------------------------

# Loads the UTXO data from a json file. You can create your own file based on the provided example with UTXOs from keys
# you own. It won't work if you don't update it.
utxo = load(open('example_utxos/P2MS_utxo.json', 'r'))

# Get the previous transaction id and index, as well as the source bitcoin address.
prev_tx_id = str(utxo.get('tx_id'))
prev_out_index = utxo.get('index')

# Load the keys from the loaded addresses (you should have them!). Notice that since we are going to create a P2MS tx
# from a P2MS UTXO, several keys will be required.
source_btc_addrs = utxo.get('btc_addr')
keys = map(load_keys, source_btc_addrs)
sks = [k[0] for k in keys]
pks = [k[1] for k in keys]

# Amount to be spent, in Satoshi, and the fee to be deduced (should be calculated).
value = utxo.get('value')
fee = 230 * 240

# Now we can build the transaction from inputs/outputs.
# We will create a 2-3 P2MS from a 1-3 P2MS, so we need to include 1 signature to redeem the previous utxo, and include
# a 2-3 script to create the new one.

# To create the destination script, we need to include first the number of required signatures (2), and then, the
# all the public keys.
destination = [2, serialize_pk(pks[0]), serialize_pk(pks[1]),  serialize_pk(pks[2])]
# Using map will also do the trick.
# destination = [2] + map(serialize_pk, pks)

# Now we can create the transaction. Since we owe all the keys, we can choose any one of the tree to sign it.
tx = TX.build_from_io(prev_tx_id, prev_out_index, value - fee, destination)
tx.sign(sks[0], 0)

# Once created we can display the serialized transaction. Transaction is now ready to be broadcast.
print "hex: " + tx.serialize()

# Finally, we can analyze each field of the transaction.
tx.display()


