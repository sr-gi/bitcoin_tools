from urllib2 import urlopen, Request
from json import loads


def change_endianness(x):
    """ Changes the endianness (from BE to LE and vice versa) of a given value.

    :param x: Given value which endianness will be changed.
    :type x: hex str
    :return: The opposite endianness representation of the given value.
    :rtype: hex str
    """

    # If there is an odd number of elements, we make it even by adding a 0
    if (len(x) % 2) == 1:
        x += "0"
    y = x.decode('hex')
    z = y[::-1]
    return z.encode('hex')


def int2bytes(a, b):
    """ Converts a given integer value (a) its b-byte representation, in hex format.

    :param a: Value to be converted.
    :type a: int
    :param b: Byte size to be filled.
    :type b: int
    :return: The b-bytes representation of the given value (a) in hex format.
    :rtype: hex str
    """

    m = pow(2, 8*b) - 1
    if a > m:
        raise Exception(str(a) + " is too big to be represented with " + str(b) + " bytes. Maximum value is "
                        + str(m) + ".")

    return ('%0' + str(2 * b) + 'x') % a


def parse_element(tx, size):
    """ Parses a given transaction to extract an element of a given size.

    :param tx: Transaction where the element will be extracted.
    :type tx: TX
    :param size: Size of the parameter to be extracted.
    :type size: int
    :return: The extracted element.
    :rtype: hex str
    """

    element = tx.hex[tx.offset:tx.offset + size * 2]
    tx.offset += size * 2
    return element


def parse_varint(tx):
    """ Parses a given transaction for extracting an encoded varint element.

    :param tx: Transaction where the element will be extracted.
    :type tx: TX
    :return: The b-bytes representation of the given value (a) in hex format.
    :rtype: hex str
    """

    # First of all, the offset of the hex transaction if moved to the proper position (i.e where the varint should be
    #  located) and the length and format of the data to be analyzed is checked.
    data = tx.hex[tx.offset:]
    assert (len(data) > 0)
    size = int(data[:2], 16)
    assert (size <= 255)

    # Then, the integer is encoded as a varint using the proper prefix, if needed.
    if size <= 252:  # No prefix
        storage_length = 1
    elif size == 253:  # 0xFD
        storage_length = 3
    elif size == 254:  # 0xFE
        storage_length = 5
    elif size == 255:  # 0xFF
        storage_length = 9
    else:
        raise Exception("Wrong input data size")

    # Finally, the storage length is used to extract the proper number of bytes from the transaction hex and the
    # transaction offset is updated.
    varint = data[:storage_length * 2]
    tx.offset += storage_length * 2

    return varint


def decode_varint(varint):
    """ Decodes a varint to its standard integer representation.

    :param varint: The varint value that will be decoded.
    :type varint: str
    :return: The standard integer representation of the given varint.
    :rtype: int
    """

    # The length of the varint is check to know whether there is a prefix to be removed or not.
    if len(varint) > 2:
        decoded_varint = int(change_endianness(varint[2:]), 16)
    else:
        decoded_varint = int(varint, 16)

    return decoded_varint


def encode_varint(value):
    """ Encodes a given integer value to a varint. It only used the four varint representation cases used by bitcoin:
    1-byte, 2-byte, 4-byte or 8-byte integers.

    :param value: The integer value that will be encoded into varint.
    :type value: int
    :return: The varint representation of the given integer value.
    :rtype: str
    """

    # The value is checked in order to choose the size of its final representation.
    # 0xFD(253), 0xFE(254) and 0xFF(255) are special cases, since are the prefixes defined for 2-byte, 4-byte
    # and 8-byte long values respectively.
    if value < pow(2, 8) - 3:
        size = 1
        varint = int2bytes(value, size)  # No prefix
    else:
        if value < pow(2, 16):
            size = 2
            prefix = 253  # 0xFD
        elif value < pow(2, 32):
            size = 4
            prefix = 254  # 0xFE
        elif value < pow(2, 64):
            size = 8
            prefix = 255  # 0xFF
        else:
            raise Exception("Wrong input data size")
        varint = format(prefix, 'x') + change_endianness(int2bytes(value, size))

    return varint


def check_public_key(pk):
    """ Checks if a given string is a public (or at least if it is formatted as if it is).

    :param pk: ECDSA public key to be checked.
    :type pk: hex str
    :return: True if the key matches the format, raise exception otherwise.
    :rtype: bool
    """

    prefix = pk[0:2]
    l = len(pk)

    if prefix not in ["02", "03", "04"]:
        raise Exception("Wrong public key format.")
    if prefix == "04" and l != 130:
        raise Exception("Wrong length for an uncompressed public key: " + str(l))
    elif prefix in ["02", "03"] and l != 66:
        raise Exception("Wrong length for a compressed public key: " + str(l))
    else:
        return True


def check_address(btc_addr, network='test'):
    """ Checks if a given string is a Bitcoin address for a given network (or at least if it is formatted as if it is).

    :param btc_addr: Bitcoin address to be checked.
    :rtype: hex str
    :param network: Network to be checked (either mainnet or testnet).
    :type network: hex str
    :return: True if the Bitcoin address matches the format, raise exception otherwise.
    """

    if network in ['test', "testnet"] and btc_addr[0] not in ['m', 'n']:
        raise Exception("Wrong testnet address format.")
    elif network in ['main', 'mainnet'] and btc_addr[0] != '1':
        raise Exception("Wrong mainnet address format.")
    elif network not in ['test', 'testnet', 'main', 'mainnet']:
        raise Exception("Network must be test/testnet or main/mainnet")
    elif len(btc_addr) not in range(26, 35+1):
        raise Exception("Wrong address format, Bitcoin addresses should be 27-35 hex char long.")
    else:
        return True


def check_signature(signature):
    """ Checks if a given string is a signature (or at least if it is formatted as if it is).

    :param signature: Signature to be checked.
    :type signature: hex str
    :return: True if the signatures matches the format, raise exception otherwise.
    :rtype: bool
    """

    l = (len(signature[4:]) - 2) / 2

    if signature[:2] != "30":
        raise Exception("Wrong signature format.")
    elif int(signature[2:4], 16) != l:
        raise Exception("Wrong signature length " + str(l))
    else:
        return True


def check_script(script):
    """ Checks if a given string is a script (hash160) (or at least if it is formatted as if it is).

    :param script: Script to be checked.
    :type script: hex str
    :return: True if the signatures matches the format, raise exception otherwise.
    :rtype: bool
    """

    if not isinstance(script, str):
        raise Exception("Wrong script format.")
    elif len(script)/2 != 20:
        raise Exception("Wrong signature length " + str(len(script)/2))
    else:
        return True


def is_public_key(pk):
    """ Encapsulates check_public_key function as a True/False option.

    :param pk: ECDSA public key to be checked.
    :type pk: hex str
    :return: True if pk is a public key, false otherwise.
    """

    try:
        return check_public_key(pk)
    except:
        return False


def is_btc_addr(btc_addr, network='test'):
    """ Encapsulates check_address function as a True/False option.

    :param btc_addr: Bitcoin address to be checked.
    :type btc_addr: hex str
    :param network: The network to be checked (either mainnet or testnet).
    :type network: str
    :return: True if btc_addr is a public key, false otherwise.
    """

    try:
        return check_address(btc_addr, network)
    except:
        return False


def is_signature(signature):
    """ Encapsulates check_signature function as a True/False option.

    :param signature: Signature to be checked.
    :type signature: hex str
    :return: True if signature is a signature, false otherwise.
    """

    try:
        return check_signature(signature)
    except:
        return False


def is_script(script):
    """ Encapsulates check_script function as a True/False option.

    :param script: Script to be checked.
    :type script: hex str
    :return: True if script is a script, false otherwise.
    """

    try:
        return check_script(script)
    except:
        return False


def get_prev_ScriptPubKey(tx_id, index, network='test'):
    """ Gets the ScriptPubKey of a given transaction id and its type, by querying blockcyer's API.

    :param tx_id: Transaction identifier to be queried.
    :type tx_id: hex str
    :param index: Index of the output from the transaction.
    :type index: int
    :param network: Network in which the transaction can be found (either mainnet or testnet).
    :type network: hex str
    :return: The corresponding ScriptPubKey and its type.
    :rtype hex str, str
    """

    if network in ['main', 'mainnet']:
        base_url = "https://api.blockcypher.com/v1/btc/main/txs/"
    elif network in ['test', 'testnet']:
        base_url = "https://api.blockcypher.com/v1/btc/test3/txs/"
    else:
        raise Exception("Bad network.")

    request = Request(base_url + tx_id)
    header = 'User-agent', 'Mozilla/5.0'
    request.add_header("User-agent", header)

    r = urlopen(request)

    data = loads(r.read())

    script = data.get('outputs')[index].get('script')
    t = data.get('outputs')[index].get('script_type')

    return script, parse_script_type(t)


def parse_script_type(t):
    """ Parses a script type obtained from a query to blockcyper's API.

    :param t: script type to be parsed.
    :type t: str
    :return: The parsed script type.
    :rtype: str
    """

    if t == 'pay-to-multi-pubkey-hash':
        r = "P2MS"
    elif t == 'pay-to-pubkey':
        r = "P2PK"
    elif t == 'pay-to-pubkey-hash':
        r = "P2PKH"
    elif t == 'pay-to-script-hash':
        r = "P2PSH"
    else:
        r = "unknown"

    return r



