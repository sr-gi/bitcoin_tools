from binascii import unhexlify, hexlify
from hashlib import new, sha256
from os import mkdir, path
from re import match

from base58 import b58encode, b58decode
from qrcode import make as qr_make

from bitcoin_tools import CFG
from bitcoin_tools.core.keys import serialize_pk, serialize_sk

# Network codes
PUBKEY_HASH = 0
TESTNET_PUBKEY_HASH = 111

WIF = 128
TESTNET_WIF = 239


def hash_160(data):
    """ Calculates the RIPEMD-160 hash of a given string.

    :param data: Data to be hashed. Normally used with ECDSA public keys.
    :type data: hex str
    :return: The RIPEMD-160 hash.
    :rtype: bytes
    """

    # Calculate the RIPEMD-160 hash of the given data.
    md = new('ripemd160')
    h = sha256(unhexlify(data)).digest()
    md.update(h)
    h160 = md.digest()

    return h160


def hash_160_to_btc_address(h160, v):
    """ Calculates the Bitcoin address of a given RIPEMD-160 hash from an elliptic curve public key.

    :param h160: RIPEMD-160 hash.
    :type h160: bytes
    :param v: version (prefix) used to calculate the Bitcoin address.

     Possible values:

        - 0 for main network (PUBKEY_HASH).
        - 111 For testnet (TESTNET_PUBKEY_HASH).
    :type v: int
    :return: The corresponding Bitcoin address.
    :rtype: hex str
    """

    # If h160 is passed as hex str, the value is converted into bytes.
    if match('^[0-9a-fA-F]*$', h160):
        h160 = unhexlify(h160)

    # Add the network version leading the previously calculated RIPEMD-160 hash.
    vh160 = chr(v) + h160
    # Double sha256.
    h = sha256(sha256(vh160).digest()).digest()
    # Add the two first bytes of the result as a checksum tailing the RIPEMD-160 hash.
    addr = vh160 + h[0:4]
    # Obtain the Bitcoin address by Base58 encoding the result
    addr = b58encode(addr)

    return addr


def btc_addr_to_hash_160(btc_addr):
    """ Calculates the RIPEMD-160 hash from a given Bitcoin address

    :param btc_addr: Bitcoin address.
    :type btc_addr: str
    :return: The corresponding RIPEMD-160 hash.
    :rtype: hex str
    """

    # Base 58 decode the Bitcoin address.
    decoded_addr = b58decode(btc_addr)
    # Covert the address from bytes to hex.
    decoded_addr_hex = hexlify(decoded_addr)
    # Obtain the RIPEMD-160 hash by removing the first and four last bytes of the decoded address, corresponding to
    # the network version and the checksum of the address.
    h160 = decoded_addr_hex[2:-8]

    return h160


def pk_to_btc_addr(pk, v='test'):
    """ Calculates the Bitcoin address of a given elliptic curve public key.

    :param pk: elliptic curve public key.
    :type pk: hex str
    :param v: version used to calculate the Bitcoin address.
    :type v: str
    :return: The corresponding Bitcoin address.

        - main network address if v is 'main.
        - testnet address otherwise
    :rtype: hex str
    """

    # Choose the proper version depending on the provided 'v'.
    if v in ['mainnet', 'main']:
        v = PUBKEY_HASH
    elif v in ['testnet', 'test']:
        v = TESTNET_PUBKEY_HASH
    else:
        raise Exception("Invalid version, use either 'main' or 'test'.")

    # Calculate the RIPEMD-160 hash of the given public key.
    h160 = hash_160(pk)
    # Calculate the Bitcoin address from the chosen network.
    btc_addr = hash_160_to_btc_address(h160, v)

    return btc_addr


def generate_btc_addr(pk, v='test',  compressed=True):
    """ Calculates Bitcoin address associated to a given elliptic curve public key and a given network.

    :param pk: ECDSA VerifyingKey object (public key to be converted into Bitcoin address).
    :type pk: VerifyingKey
    :param v: version (prefix) used to calculate the WIF, it depends on the type of network.
    :type v: str
    :param compressed: Indicates if Bitcoin address will be generated with the compressed or uncompressed key.
    :type compressed: bool
    :return: The Bitcoin address associated to the given public key and network.
    :rtype: str
    """

    # Get the hex representation of the provided DER encoded public key.
    public_key_hex = serialize_pk(pk, compressed)
    # Generate the Bitcoin address of de desired network.
    btc_addr = pk_to_btc_addr(public_key_hex, v)

    return btc_addr


def sk_to_wif(sk, compressed=True, mode='image', v='test'):
    """ Generates a Wallet Import Format (WIF) representation of a provided elliptic curve private key.

    :param sk: elliptic curve private key.
    :type sk: hex str
    :param compressed: Whether the WIF will be used with a compressed or uncompressed public key
    :type compressed: bool
    :param mode: defines the type of return.
    :type mode: str
    :param v: version (prefix) used to calculate the WIF, it depends on the type of network.
    :type v: str
    :return: The WIF representation of the private key.

        - main network WIF if v is 'main'.
        - testnet WIF otherwise.
    :rtype:

        - qrcode is mode is 'image'.
        - str otherwise.
    """

    # Choose the proper version depending on the provided 'v'.
    if v in ['mainnet', 'main']:
        v = WIF
    elif v in ['testnet', 'test']:
        v = TESTNET_WIF
    else:
        raise Exception("Invalid version, use either 'main' or 'test'.")

    # Add the network version leading the private key (in hex).
    e_pkey = chr(v) + unhexlify(sk)
    # Flag compressed pk when needed
    if compressed:
        e_pkey += unhexlify('01')
    # Double sha256.
    h = sha256(sha256(e_pkey).digest()).digest()
    # Add the two first bytes of the result as a checksum tailing the encoded key.
    wif = e_pkey + h[0:4]
    # Enconde the result in base58.
    wif = b58encode(wif)

    # Choose the proper return mode depending on 'mode'.
    if mode is 'image':
        response = qr_make(wif)
    elif mode is 'text':
        response = wif
    else:
        raise Exception("Invalid mode, used either 'image' or 'text'.")

    return response


def generate_wif(btc_addr, sk, mode='image', v='test', vault_path=None):
    """ Generates a Wallet Import Format (WIF) file into disk. Uses an elliptic curve private key from disk as an input
    using the btc_addr associated to the public key of the same key pair as an identifier.

    :param btc_addr: Bitcoin address associated to the public key of the same key pair as the private key.
    :type btc_addr: hex str
    :param sk: Private key to be converted into Wallet Import Format (WIF).
    :type sk: ECDSA SigningKey object.
    :param mode: defines the type of return.
    :type mode: str
    :param v: version (prefix) used to calculate the WIF, it depends on the type of network.
    :type v: str
    :param vault_path: Path where WIF file will be stored be stored. Defined in the config file by default.
    :type vault_path: str
    :return: None.
    :rtype: None
    """

    # Get a private key in hex format and create the WIF representation.
    wif = sk_to_wif(serialize_sk(sk), mode=mode, v=v)

    if vault_path is None:
        vault_path = CFG.address_vault

    # Store the result depending on the selected mode.
    if not path.exists(vault_path + btc_addr):
        mkdir(vault_path + btc_addr)

    if mode is 'image':
        wif.save(vault_path + btc_addr + "/WIF.png")
    elif mode is 'text':
        f = file(vault_path + btc_addr + "/WIF.txt", 'w')
        f.write(wif)
    else:
        raise Exception("Invalid mode, used either 'image' or 'text'.")
