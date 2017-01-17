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
        elif value < pow(2, 64):
            size = 4
            prefix = 254  # 0xFE
        elif value < pow(2, 128):
            size = 8
            prefix = 255  # 0xFF
        else:
            raise Exception("Wrong input data size")
        varint = format(prefix, 'x') + change_endianness(int2bytes(value, size))

    return varint
