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
btc_addr = generate_btc_addr(pk.to_der(), v='test')
# Both the public and private key are stored in disk. The Bitcoin address is used as an identifier in the name
# of the folder that contains both keys.
store_keys(sk.to_pem(), pk.to_pem(), btc_addr)
# Finally, the private key is encoded as WIF and also stored in disk, ready to be imported in a wallet.
generate_wif(btc_addr, mode='image', v='test') 
```

### Key loading  
```python
btc_addr = "mwryy9YdVezq2Wo1DukA5ADhrNemqCKTmy"
sk, pk = load_keys(btc_addr)
```
### Raw transaction building  
```python
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
```

### Disclaimer

The purpose of the code is purely educational. We totally discourage the use of it outside the testnet, especially when
dealing with non-standard scripts. A bad use of the library can lead you to lose some of your bitcoins.




