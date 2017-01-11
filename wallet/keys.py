from os import mkdir, path
from ecdsa import SigningKey, SECP256k1
from subprocess import check_output, STDOUT
from pyasn1.codec.der import decoder


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


def get_pub_key_hex(pk_der):
    """ Converts a public key in hexadecimal format from a DER encoded public key.

    :param pk_der: DER encoded public key
    :type pk_der: bytes
    :return: public key.
    :rtype: hex str
    """

    # Get the asn1 representation of the public key DER data.
    asn1_pk, _ = decoder.decode(str(pk_der))

    # Get the public key as a BitString. The public key corresponds to the second component
    # of the asn1 public key structure.
    pk_bit = asn1_pk.getComponentByPosition(1)

    # Convert the BitString into a String.
    pk_str = ""
    for i in range(len(pk_bit)):
        pk_str += str(pk_bit[i])

    # Parse the data to get it in the desired form.
    pk_hex = '0' + hex(int(pk_str, 2))[2:-1]

    return pk_hex


# ToDO: Find a way to get the SK without a system call
def get_priv_key_hex(sk_file_path):
    """ Gets the EC private key in hexadecimal format from a key file.

    :param sk_file_path: system path where the EC private key is found.
    :type sk_file_path: str
    :return: private key.
    :rtype: hex str
    """

    # Obtain the private key using an OpenSSL system call.
    cmd = ['openssl', 'ec', '-in', sk_file_path, '-text', '-noout']
    response = check_output(cmd, stderr=STDOUT)

    # Parse the result to remove all the undesired spacing characters.
    raw_key = response[response.find('priv:') + 8: response.find('pub:')]
    raw_key = raw_key.replace(":", "")
    raw_key = raw_key.replace(" ", "")
    raw_key = raw_key.replace("\n", "")

    # If the key starts with 00, the two first characters are removed.
    if raw_key[:2] == '00':
        sk_hex = raw_key[2:]
    else:
        sk_hex = raw_key

    return sk_hex


