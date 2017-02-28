# Bitcoin tools

bitcoin_tools is a Python library created for teaching and researching purposes. Its main objective is helping 
users to understand how Bitcoin transactions can be created from scratch, allowing them to identify the fields constituting a transaction, how those fields can be modified, and where they are located in the hexadecimal representation of the transaction (the serialized transaction).

Moreover, bitcoin_tools allows users to set both scriptSig and scriptPubKey fields to whatever
script they want to generate, letting the creation and testing of new scripts far beyond the 
standard ones. (The creation of script from scratch is still not part of the code, but hexadecimal scripts created 
with other tools can be easily inserted into transactions).



### Disclaimer

The purpose of the code is purely educational. We totally discourage the use of it outside the testnet, especially when
dealing with non-standard scripts. A bad use of the library can lead you to lose some of your bitcoins.




