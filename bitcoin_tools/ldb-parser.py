import plyvel
from binascii import b2a_hex, a2b_hex
from json import dumps
from bitcoin_tools.utils import load_conf_file

# Load config file
cfg = load_conf_file()

# Output file
fout = open(cfg.data_path + "/utxos.txt", 'w')

# Open the LevelDB
db = plyvel.DB(cfg.btc_core_path + "/chainstate", compression=None)  # Change with path to chainstate

# Load obfuscation key (if it exists)
o_key = db.get((a2b_hex("0e00") + "obfuscate_key"))

# If the key exists, the leading byte indicates the length of the key (8 byte by default). If there is no key, 8-byte
# zeros are used (since the key will be XORed with the given values).
if o_key is not None:
    o_key = b2a_hex(o_key)[2:]
else:
    o_key = "0000000000000000"

# For every UTXO (identified with a leading 'c'), the key (tx_id) and the value (encoded utxo) is displayed.
# UTXOs are obfuscated using the obfuscation key (o_key), in order to get them non-obfuscated, a XOR between the
# value and the key (concatenated until the length of the value is reached) if performed).
for key, o_value in db.iterator(prefix=b'c'):
    value = "".join([format(int(v, 16) ^ int(o_key[i % len(o_key)], 16), 'x') for i, v in enumerate(b2a_hex(o_value))])
    assert len(b2a_hex(o_value)) == len(value)
    fout.write(dumps({"key":  b2a_hex(key), "value": value}) + "\n")

db.close()
