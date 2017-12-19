from bitcoin_tools.core.transaction import TX

#################################################
#           Hex transaction analysis            #
#################################################

# ---------------------------------------------------------------------------------------------------------------------
# The following piece of code parses a serialized transaction (hex encoded) and displays all the information related
# to it.
# - Leftmost displayed transaction shows data as should be interpreted (human-readable), while rightmost
# (surrounded by parenthesis) shows it as it is in the serialize transaction (can be used to identify it inside the
# transaction)
# - You should change the hex_tx for the one you'd like to deserialize. Serialized transaction can be obtain from block
# explorers such as blockcypher.com or blockchain.info, or by building a transaction using some of the library tools.
# ---------------------------------------------------------------------------------------------------------------------

# First a transaction object is created (through the deserialize constructor) by deserializing the hex transaction we
# have selected.
hex_tx = "01000000013ca58d2f6fac36602d831ee0cf2bc80031c7472e80a322b57f614c5ce9142b71000000006b483045022100f0331d85cb7f7ec1bedc41f50c695d654489458e88aec0076fbad5d8aeda1673022009e8ca2dda1d6a16bfd7133b0008720145dacccb35c0d5c9fc567e52f26ca5f7012103a164209a7c23227fcd6a71c51efc5b6eb25407f4faf06890f57908425255e42bffffffff0241a20000000000001976a914e44839239ab36f5bc67b2079de00ecf587233ebe88ac74630000000000001976a914dc7016484646168d99e49f907c86c271299441c088ac00000000"
tx = TX.deserialize(hex_tx)

# Then, the transaction can be displayed using the display method to analyze how it's been constructed.
tx.display()
