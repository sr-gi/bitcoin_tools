from bitcoin_tools import CFG
from bitcoin_tools.utils import change_endianness, int2bytes
from bitcoin.core.script import SIGHASH_ALL, SIGHASH_SINGLE, SIGHASH_NONE

from binascii import hexlify, unhexlify
from hashlib import sha256
from os import mkdir, path
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_der_canonize, number_to_string


def generate_keys():
    """ Gets a new  elliptic curve key pair using the SECP256K1 elliptic curve (the one used by Bitcoin).

    :return: elliptic curve key pair.
    :rtype: list
    """

    # Generate the key pair from a SECP256K1 elliptic curve.
    sk = SigningKey.generate(curve=SECP256k1)
    pk = sk.get_verifying_key()

    return sk, pk


def store_keys(sk, pk, btc_addr, vault_path=None):
    """ Stores an elliptic curve key pair in PEM format into disk. Both keys are stored in a folder named after the
    Bitcoin address derived from the public key.

    :param sk: PEM encoded elliptic curve private key.
    :type sk: str
    :param pk: PEM encoded elliptic curve public key.
    :type pk: str
    :param btc_addr: Bitcoin address associated to the public key of the key pair.
    :type btc_addr: str
    :param vault_path: Path where keys will be stored. Defined in the config file by default.
    :type vault_path: str
    :return: None.
    :rtype: None
    """

    if vault_path is None:
        vault_path = CFG.address_vault

    if not path.exists(vault_path + btc_addr):
        mkdir(vault_path + btc_addr)

    # Save both keys into disk using the Bitcoin address as an identifier.
    open(vault_path + btc_addr + '/sk.pem', "w").write(sk)
    open(vault_path + btc_addr + '/pk.pem', "w").write(pk)


def load_keys(btc_addr, vault_path=None):
    """ Loads an elliptic curve key pair in PEM format from disk. Keys are stored in their proper objects from the ecdsa
    python library (SigningKey and VerifyingKey respectively)

    :param btc_addr: Bitcoin address associated to the public key of the key pair.
    :type btc_addr: str
    :param vault_path: Path where keys are be stored. Defined in the config file by default.
    :type vault_path: str
    :return: ecdsa key pair as a tuple.
    :rtype: SigningKey, VerifyingKey
    """

    if vault_path is None:
        vault_path = CFG.address_vault

    sk_pem = open(vault_path + btc_addr + '/sk.pem', "r").read()
    pk_pem = open(vault_path + btc_addr + '/pk.pem', "r").read()

    return SigningKey.from_pem(sk_pem), VerifyingKey.from_pem(pk_pem)


def serialize_pk(pk, compressed=True):
    """ Serializes a ecdsa.VerifyingKey (public key).

    :param compressed: Indicates if the serialized public key will be either compressed or uncompressed.
    :type compressed: bool
    :param pk: ECDSA VerifyingKey object (public key to be serialized).
    :type pk: ecdsa.VerifyingKey
    :return: serialized public key.
    :rtype: hex str
    """

    # Updated with code based on PR #54 from python-ecdsa until the PR gets merged:
    # https://github.com/warner/python-ecdsa/pull/54

    x_str = number_to_string(pk.pubkey.point.x(), pk.pubkey.order)

    if compressed:
        if pk.pubkey.point.y() & 1:
            prefix = '03'
        else:
            prefix = '02'

        s_key = prefix + hexlify(x_str)
    else:
        s_key = '04' + hexlify(pk.to_string())

    return s_key


def serialize_sk(sk):
    """ Serializes a ecdsa.SigningKey (private key).

    :param sk: ECDSA SigningKey object (private key to be serialized).
    :type sk: ecdsa.SigningKey
    :return: serialized private key.
    :rtype: hex str
    """
    return hexlify(sk.to_string())


def ecdsa_tx_sign(unsigned_tx, sk, hashflag=SIGHASH_ALL, deterministic=True):
    """ Performs and ECDSA sign over a given transaction using a given secret key.
    :param unsigned_tx: unsigned transaction that will be double-sha256 and signed.
    :type unsigned_tx: hex str
    :param sk: ECDSA private key that will sign the transaction.
    :type sk: SigningKey
    :param hashflag: hash type that will be used during the signature process and will identify the signature format.
    :type hashflag: int
    :param deterministic: Whether the signature is performed using a deterministic k or not. Set by default.
    :type deterministic: bool
    :return:
    """

    # Encode the hash type as a 4-byte hex value.
    if hashflag in [SIGHASH_ALL, SIGHASH_SINGLE, SIGHASH_NONE]:
        hc = int2bytes(hashflag, 4)
    else:
        raise Exception("Wrong hash flag.")

    # ToDo: Deal with SIGHASH_ANYONECANPAY

    # sha-256 the unsigned transaction together with the hash type (little endian).
    h = sha256(unhexlify(unsigned_tx + change_endianness(hc))).digest()
    # Sign the transaction (using a sha256 digest, that will conclude with the double-sha256)
    # If deterministic is set, the signature will be performed deterministically choosing a k from the given transaction
    if deterministic:
        s = sk.sign_deterministic(h, hashfunc=sha256, sigencode=sigencode_der_canonize)
    # Otherwise, k will be chosen at random. Notice that this can lead to a private key disclosure if two different
    # messages are signed using the same k.
    else:
        s = sk.sign(h, hashfunc=sha256, sigencode=sigencode_der_canonize)

    # Finally, add the hashtype to the end of the signature as a 2-byte big endian hex value.
    return hexlify(s) + hc[-2:]


def get_compressed_pk(pk):
    """
    Constructs the compressed representation of a SECP256k1 ECDSA public key form a given uncompressed key.

    :param pk: The uncompressed SECP256k1 key to be decompressed.
    :type pk: hex
    :return: The compressed SECP256k1 ECDSA key.
    :rtype: hex
    """

    ecdsa_pk = VerifyingKey.from_string(unhexlify(pk[2:]), curve=SECP256k1)
    compressed_pk = serialize_pk(ecdsa_pk)

    return compressed_pk


def get_uncompressed_pk(compressed_pk):
    """
    Constructs the uncompressed representation of a SECP256k1 ECDSA public key form a given compressed key.

    The code is port from https://stackoverflow.com/a/43654055/5413535 with a couple of bug fixed.

    :param compressed_pk: The compressed SECP256k1 key to be decompressed.
    :type compressed_pk: hex
    :return: The uncompressed SECP256k1 ECDSA key.
    :rtype: hex
    """

    # Get p from the curve
    p = SECP256k1.curve.p()

    # Get x and the prefix
    x_hex = compressed_pk[2:66]
    x = int(x_hex, 16)
    prefix = compressed_pk[0:2]

    # Compute y
    y_square = (pow(x, 3, p) + 7) % p
    y_square_square_root = pow(y_square, (p + 1) / 4, p)

    # Chose the proper y depending on the prefix and whether the computed square root is odd or even
    if prefix == "02" and y_square_square_root & 1 or prefix == "03" and not y_square_square_root & 1:
        y = (-y_square_square_root) % p
    else:
        y = y_square_square_root

    # Construct the uncompressed pk
    uncompressed_pk = "04" + x_hex + format(y, '064x')

    return uncompressed_pk
