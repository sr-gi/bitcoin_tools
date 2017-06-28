from bitcoin_tools.utils import change_endianness, int2bytes
from binascii import b2a_hex, a2b_hex
from hashlib import sha256
from os import mkdir, path
from bitcoin.core.script import SIGHASH_ALL, SIGHASH_SINGLE, SIGHASH_NONE
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


def serialize_pk(pk, compressed=True):
    """ Serializes a ecdsa.VerifyingKey (public key).

    :param compressed: Indicates if the serialized public key will be either compressed or uncompressed.
    :type compressed: bool
    :param pk: ECDSA VerifyingKey object (public key to be serialized).
    :type pk: ecdsa.VerifyingKey
    :return: serialized public key.
    :rtype: hex str
    """

    # Updated with code based on from PR #54 from python-ecdsa until the PR gets merged:
    # https://github.com/warner/python-ecdsa/pull/54

    x_str = number_to_string(pk.pubkey.point.x(), pk.pubkey.order)

    if compressed:
        if pk.pubkey.point.y() & 1:
            prefix = '03'
        else:
            prefix = '02'

        s_key = prefix + b2a_hex(x_str)
    else:
        s_key = '04' + b2a_hex(pk.to_string())

    return s_key


def serialize_sk(sk):
    """ Serializes a ecdsa.SigningKey (private key).

    :param sk: ECDSA SigningKey object (private key to be serialized).
    :type sk: ecdsa.SigningKey
    :return: serialized private key.
    :rtype: hex str
    """
    return b2a_hex(sk.to_string())


def ecdsa_tx_sign(unsigned_tx, sk, hashflag=SIGHASH_ALL):
    """ Performs and ECDSA sign over a given transaction using a given secret key.
    :param unsigned_tx: unsigned transaction that will be double-sha256 and signed.
    :type unsigned_tx: hex str
    :param sk: ECDSA private key that will sign the transaction.
    :type sk: SigningKey
    :param hashflag: hash type that will be used during the signature process and will identify the signature format.
    :type hashflag: int
    :return:
    """

    # Encode the hash type as a 4-byte hex value.
    if hashflag in [SIGHASH_ALL, SIGHASH_SINGLE, SIGHASH_NONE]:
        hc = int2bytes(hashflag, 4)
    else:
        raise Exception("Wrong hash flag.")

    # ToDo: Deal with SIGHASH_ANYONECANPAY

    # sha-256 the unsigned transaction together with the hash type (little endian).
    h = sha256(a2b_hex(unsigned_tx + change_endianness(hc))).digest()
    # sign the transaction (using a sha256 digest, that will conclude with the double-sha256)
    s = sk.sign_deterministic(h, hashfunc=sha256, sigencode=sigencode_der_canonize)

    # Finally, add the hashtype to the end of the signature as a 2-byte big endian hex value.
    return b2a_hex(s) + hc[-2:]
