# Network codes

PUBKEY_HASH = 0
TESTNET_PUBKEY_HASH = 111

WIF = 128
TESTNET_WIF = 239

# Scripting OP_CODES

OP_DUP = 118
OP_HASH_160 = 169
OP_EQUALVERIFY = 136
OP_CHECKSIG = 172

# Lengths
MAX_SIG_LEN = 74  # DER signature size between 71-73 bytes.
PK_LEN = 65  # Length of a Bitcoin public key
OP_PUSH_LEN = 1  # Every data push, regardless of the data size to be pushed, sizes 1 byte.

# Fees
MIN_TX_FEE = 5  # Satoshis/byte according (just for testnet, in mainnet it could be too low)
RECOMMENDED_MIN_TX_FEE = 120  # Satoshis/byte according to https://bitcoinfees.21.co/

# LevelDB
NSPECIALSCRIPTS = 6
