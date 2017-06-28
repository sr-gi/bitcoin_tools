# Bitcoin tools

bitcoin_tools is a Python library created for teaching and researching purposes. Its main objective is helping 
users to understand how Bitcoin transactions can be created from scratch, allowing them to identify the fields constituting a transaction, how those fields can be modified, and where they are located in the hexadecimal representation of the transaction (the serialized transaction).

Moreover, bitcoin_tools allows users to set both scriptSig and scriptPubKey fields to whatever
script they want to generate, letting the creation and testing of new scripts far beyond the 
standard ones. (The creation of script from scratch is still not part of the code, but hexadecimal scripts created 
with other tools can be easily inserted into transactions).


### Examples

Down below you can find some examples of how to use some of the library functions. More examples can be found in examples.py

#### Key management and Bitcoin address generation
```python
# First of all the elliptic curve keys are generated.
sk, pk = generate_keys()
# The Bitcoin address is derived from the public key created above.
btc_addr = generate_btc_addr(pk, v='test')
# Both the public and private key are stored in disk. The Bitcoin address is used as an identifier in the name
# of the folder that contains both keys.
store_keys(sk.to_pem(), pk.to_pem(), btc_addr)
# Finally, the private key is encoded as WIF and also stored in disk, ready to be imported in a wallet.
generate_wif(btc_addr, sk, mode='image', v='test')

```

#### Raw transaction building  
```python
# Reference to the previous transaction where the funds will be redeemed and spent. Consists in an id and
# an output index.
prev_tx_id = "7767a9eb2c8adda3ffce86c06689007a903b6f7e78dbc049ef0dbaf9eeebe075"
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
# Input 0 will be signed, since we have only created one input.
tx.sign(sk, 0)
# Once created we can display the serialized transaction. Transaction is now ready to be broadcast.
print "hex: " + tx.serialize()

# Finally, we can analyze each field of the transaction.
tx.display()

### Disclaimer

The purpose of the code is purely educational. We totally discourage the use of it outside the testnet, especially when
dealing with non-standard scripts. A bad use of the library can lead you to lose some of your bitcoins.




