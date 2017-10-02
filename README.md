# Bitcoin tools

bitcoin_tools is a Python library created for teaching and researching purposes. Its main objective is helping 
users to understand how Bitcoin transactions can be created from scratch, allowing them to identify the fields constituting a transaction, how those fields can be modified, and where they are located in the hexadecimal representation of the transaction (the serialized transaction).

Moreover, bitcoin_tools allows users to set both scriptSig and scriptPubKey fields to whatever
script they want to generate, letting the creation and testing of new scripts far beyond the 
standard ones.`

### Dependencies

The library has the following dependencies (which can be satisfied by using pip install -r requirements.txt):

ecdsa
python-bitcoinlib
base58
plyvel
matplotlib
numpy
qrcode
Pillow

Last two are only required for creating qr-codes for private key WIF format. They could be avoided if such functionality is not required.


### Examples

Down below you can find some examples of how to use some of the library functions. More examples can be found in examples.py

#### Key management and Bitcoin address generation
```python

from bitcoin_tools.core.keys import generate_keys, store_keys
from bitcoin_tools.wallet import generate_wif, generate_btc_addr

# First of all the ECDSA keys are generated.
sk, pk = generate_keys()
# Then, the Bitcoin address is derived from the public key created above.
btc_addr = generate_btc_addr(pk)
# Both the public and private key are stored in disk in pem format. The Bitcoin address is used as an identifier in the
# name of the folder that contains both keys.
store_keys(sk.to_pem(), pk.to_pem(), btc_addr)
# Finally, the private key is encoded as WIF and also stored in disk, ready to be imported in a wallet.
generate_wif(btc_addr, sk)

```

#### Raw transaction building  
```python
# Reference to the previous transaction output that will be used to redeem and spend the funds, consisting on an id and
# an output index.
prev_tx_id = "7767a9eb2c8adda3ffce86c06689007a903b6f7e78dbc049ef0dbaf9eeebe075"
prev_out_index = 0

# Amount to be spent, in Satoshis, and the fee to be deduced (should be calculated).
value = 6163910
fee = 230 * 240

# Destination Bitcoin address where the value in bitcoins will be sent and locked until the owner redeems it.
destination_btc_addr = "miWdbNn9zDLnKpcNuCLdfRiJx59c93bT8t"

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
```
#### Raw tx analysis

```python
# First a transaction object is created (through the deserialize constructor) by deserializing the hex transaction we
# have selected.
hex_tx = "01000000013ca58d2f6fac36602d831ee0cf2bc80031c7472e80a322b57f614c5ce9142b71000000006b483045022100f0331d85cb7f7ec1bedc41f50c695d654489458e88aec0076fbad5d8aeda1673022009e8ca2dda1d6a16bfd7133b0008720145dacccb35c0d5c9fc567e52f26ca5f7012103a164209a7c23227fcd6a71c51efc5b6eb25407f4faf06890f57908425255e42bffffffff0241a20000000000001976a914e44839239ab36f5bc67b2079de00ecf587233ebe88ac74630000000000001976a914dc7016484646168d99e49f907c86c271299441c088ac00000000"
tx = TX.deserialize(hex_tx)

# Then, the transaction can be displayed using the display method to analyze how it's been constructed.
tx.display()
``` 

### Disclaimer

This library has been created with research purposes, hence, it allow you to modify any transaction field as you pleased.
However, some modifications can make your transactions non-standard, or even non-spendable. We totally discourage the 
use of the library outside the testnet if you are not sure about what you are doing, specially when dealing with 
non-standard scripts. A bad use of the library can lead you to lose some of your bitcoins.




