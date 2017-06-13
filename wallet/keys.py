from binascii import b2a_hex, a2b_hex
from os import mkdir, path
from hashlib import sha256
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_der
from utils.utils import change_endianness, int2bytes


def generate_keys():
    """ Gets a new  elliptic curve key pair using the SECP256K1 elliptic curve (the one used by Bitcoin).

    :return: elliptic curve key pair.
    :rtype: list
    """

    # Generate the key pair from a SECP256K1 elliptic curve.
    sk = SigningKey.generate(curve=SECP256k1)
    pk = sk.get_verifying_key()

    return sk, pk


def store_keys(sk, pk, btc_addr):
    """ Stores an elliptic curve key pair in PEM format into disk. Both keys are stored in a folder named after the
    Bitcoin address derived from the public key.

    :param sk: PEM encoded elliptic curve private key.
    :type sk: str
    :param pk: PEM encoded elliptic curve public key.
    :type pk: str
    :param btc_addr: Bitcoin address associated to the public key of the key pair.
    :type btc_addr: str
    :return: None.
    :rtype: None
    """

    if not path.exists(btc_addr):
        mkdir(btc_addr)

    # Save both keys into disk using the Bitcoin address as an identifier.
    open(btc_addr + '/sk.pem', "w").write(sk)
    open(btc_addr + '/pk.pem', "w").write(pk)


def load_keys(btc_addr):
    """ Loads an elliptic curve key pair in PEM format from disk. Keys are stored in their proper objects from the ecdsa
    python library (SigningKey and VerifyingKey respectively)

    :param btc_addr: Bitcoin address associated to the public key of the key pair.
    :type btc_addr: str
    :return: ecdsa key pair as a tuple.
    :rtype: SigningKey, VerifyingKey
    """

    sk_pem = open(btc_addr + '/sk.pem', "r").read()
    pk_pem = open(btc_addr + '/pk.pem', "r").read()

    return SigningKey.from_pem(sk_pem), VerifyingKey.from_pem(pk_pem)


def serialize_pk(pk):
    """ Serializes a ecdsa.VerifyingKey (public key).

    :param pk: ECDSA VerifyingKey object (public key to be serialized).
    :type pk: ecdsa.VerifyingKey
    :return: serialized public key.
    :rtype: hex str
    """

    return '04' + b2a_hex(pk.to_string())


def serialize_sk(sk):
    """ Serializes a ecdsa.SigningKey (private key).

    :param sk: ECDSA SigningKey object (private key to be serialized).
    :type sk: ecdsa.SigningKey
    :return: serialized private key.
    :rtype: hex str
    """
    return b2a_hex(sk.to_string())


def ecdsa_tx_sign(unsigned_tx, pk, hashcode="SIGHASH_ALL"):
    # ToDo: Add all hashcodes
    if hashcode == "SIGHASH_ALL":
        hc = change_endianness(int2bytes(1, 4))
        hc_ret = change_endianness(int2bytes(1, 1))

    h = sha256(unsigned_tx + a2b_hex(hc)).digest()
    s = pk.sign_deterministic(h, hashfunc=sha256, sigencode=sigencode_der)

    return b2a_hex(s) + hc_ret


