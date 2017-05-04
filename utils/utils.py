from bitcoin.core.script import *
from binascii import a2b_hex, b2a_hex
from constants import NSPECIALSCRIPTS


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


def txout_compress(n):
    """ Compresses the Satoshi amount of a UTXO to be stored in the LevelDB. Code is a port from the Bitcoin Core C++
    source:
        https://github.com/bitcoin/bitcoin/blob/v0.13.2/src/compressor.cpp#L133#L160

    :param n: Satoshi amount to be compressed.
    :type n: int
    :return: The compressed amount of Satoshis.
    :rtype: int
    """
    if n == 0:
        return 0
    e = 0
    while ((n % 10) == 0) and e < 9:
        n /= 10
        e += 1

    if e < 9:
        d = (n % 10)
        assert (1 <= d <= 9)
        n /= 10
        return 1 + (n * 9 + d - 1) * 10 + e
    else:
        return 1 + (n - 1) * 10 + 9


def txout_decompress(x):
    """ Decompresses the Satoshi amount of a UTXO stored in the LevelDB. Code is a port from the Bitcoin Core C++
    source:
        https://github.com/bitcoin/bitcoin/blob/v0.13.2/src/compressor.cpp#L161#L185

    :param x: Compressed amount to be decompressed.
    :type x: int
    :return: The decompressed amount of Satoshis.
    :rtype: int
    """

    if x == 0:
        return 0
    x -= 1
    e = x % 10
    x /= 10
    if e < 9:
        d = (x % 9) + 1
        x /= 9
        n = x * 10 + d
    else:
        n = x + 1
    while e > 0:
        n *= 10
        e -= 1
    return n


def b128_encode(n):
    """ Performs the MSB base-128 encoding of a given value. Used to store variable integers (varints) in the LevelDB.
    The code is a port from the Bitcoin Core C++ source. Notice that the code is not exactly the same since the original
    one reads directly from the LevelDB.

    The encoding is used to store Satoshi amounts into the Bitcoin LevelDB (chainstate). Before encoding, values are
    compressed using txout_compress.

    The encoding can also be used to encode block height values into the format use in the LevelDB, however, those are
    encoded not compressed.

    Explanation can be found in:
        https://github.com/bitcoin/bitcoin/blob/v0.13.2/src/serialize.h#L307L329
    And code:
        https://github.com/bitcoin/bitcoin/blob/v0.13.2/src/serialize.h#L343#L358

    The MSB of every byte (x)xxx xxxx encodes whether there is another byte following or not. Hence, all MSB are set to
    one except from the very last. Moreover, one is subtracted from all but the last digit in order to ensure a
    one-to-one encoding. Hence, in order decode a value, the MSB is changed from 1 to 0, and 1 is added to the resulting
    value. Then, the value is multiplied to the respective 128 power and added to the rest.

    Examples:

        - 255 = 807F (0x80 0x7F) --> (1)000 0000 0111 1111 --> 0000 0001 0111 1111 --> 1 * 128 + 127 = 255
        - 4294967296 (2^32) = 8EFEFEFF (0x8E 0xFE 0xFE 0xFF 0x00) --> (1)000 1110 (1)111 1110 (1)111 1110 (1)111 1111
            0000 0000 --> 0000 1111 0111 1111 0111 1111 1000 0000 0000 0000 --> 15 * 128^4 + 127*128^3 + 127*128^2 +
            128*128 + 0 = 2^32


    :param n: Value to be encoded.
    :type n: int
    :return: The base-128 encoded value
    :rtype: hex str
    """

    l = 0
    tmp = []
    data = ""

    while True:
        tmp.append(n & 0x7F)
        if l != 0:
            tmp[l] |= 0x80
        if n <= 0x7F:
            break
        n = (n >> 7) - 1
        l += 1

    tmp.reverse()
    for i in tmp:
        data += format(i, '02x')
    return data


def b128_decode(data):
    """ Performs the MSB base-128 decoding of a given value. Used to decode variable integers (varints) from the LevelDB.
    The code is a port from the Bitcoin Core C++ source. Notice that the code is not exactly the same since the original
    one reads directly from the LevelDB.

    The decoding is used to decode Satoshi amounts stored in the Bitcoin LevelDB (chainstate). After decoding, values
    are decompressed using txout_decompress.

    The decoding can be also used to decode block height values stored in the LevelDB. In his case, values are not
    compressed.

    Original code can be found in:
        https://github.com/bitcoin/bitcoin/blob/v0.13.2/src/serialize.h#L360#L372

    Examples and further explanation can be found in b128_encode function.

    :param data: The base-128 encoded value to be decoded.
    :type data: hex str
    :return: The decoded value
    :rtype: int
    """

    n = 0
    i = 0
    while True:
        d = int(data[2 * i:2 * i + 2], 16)
        n = n << 7 | d & 0x7F
        if d & 0x80:
            n += 1
            i += 1
        else:
            return n


def parse_b128(utxo, offset=0):
    data = utxo[offset:offset+2]
    offset += 2
    more_bytes = int(data, 16) & 0x80  # MSB b128 Varints have set the bit 128 for every byte but the last one,
    # indicating that there is an additional byte following the one being analyzed. If bit 128 of the byte being read is
    # not set, we are analyzing the last byte, otherwise, we should continue reading.
    while more_bytes:
        data += utxo[offset:offset+2]
        more_bytes = int(utxo[offset:offset+2], 16) & 0x80
        offset += 2

    return data, offset


def decode_utxo(utxo):
    """ Decodes a LevelDB serialized UTXO. The serialized format is defined in the Bitcoin Core source as follows:
     Serialized format:
     - VARINT(nVersion)
     - VARINT(nCode)
     - unspentness bitvector, for vout[2] and further; least significant byte first
     - the non-spent CTxOuts (via CTxOutCompressor)
     - VARINT(nHeight)

     The nCode value consists of:
     - bit 1: IsCoinBase()
     - bit 2: vout[0] is not spent
     - bit 4: vout[1] is not spent
     - The higher bits encode N, the number of non-zero bytes in the following bitvector.
        - In case both bit 2 and bit 4 are unset, they encode N-1, as there must be at
        least one non-spent output).

    VARINT refers to the CVarint used along the Bitcoin Core client, that is base128 encoding. A CTxOut contains the
    compressed amount of Satoshis that the UTXO holds. That amount is encoded using the equivalent to txout_compress +
    b128_encode.
    """

    # Version is extracted from the first varint of the serialized utxo
    version, offset = parse_b128(utxo)
    version = b128_decode(version)

    # The next MSB base 128 varint is parsed to extract both is the utxo is coin base (first bit) and which of the
    # outputs are not spent.
    code, offset = parse_b128(utxo, offset)
    code = b128_decode(code)
    coinbase = code & 0x01

    # Check if the first two outputs are spent
    vout = [(code | 0x01) & 0x02, (code | 0x01) & 0x04]

    # The higher bits of the current byte (from the fourth onwards) encode n, the number of non-zero bytes of
    # the following bitvector. If both vout[0] and vout[1] are spent (v[0] = v[1] = 0) then the higher bits encodes n-1,
    # since there should be at least one non-spent output.
    if not vout[0] and not vout[1]:
        n = (code >> 3) + 1
        vout = []
    else:
        n = code >> 3
        vout = [i for i in xrange(len(vout)) if vout[i] is not 0]

    # If n is set, the encoded value contains a bitvector. The following bytes are parsed until n non-zero bytes have
    # been extracted. (If a 00 is found, the parsing continues but n is not decreased)
    if n > 0:
        bitvector = ""
        while n:
            data = utxo[offset:offset+2]
            if data != "00":
                n -= 1
            bitvector += data
            offset += 2

        # Once the value is parsed, the endianness of the value is switched from LE to BE and the binary representation
        # of the value is checked to identify the non-spent output indexes.
        bin_data = format(int(change_endianness(bitvector), 16), '0'+str(n*8)+'b')[::-1]

        # Every position (i) with a 1 encodes the index of a non-spent output as i+2, since the two first outs (v[0] and
        # v[1] has been already counted)
        # (e.g: 0440 (LE) = 4004 (BE) = 0100 0000 0000 0100. It encodes outs 4 (i+2 = 2+2) and 16 (i+2 = 14+2).
        extended_vout = [i+2 for i in xrange(len(bin_data))
                         if bin_data.find('1', i) == i]  # Finds the index of '1's and adds 2.

        # Finally, the first two vouts are included to the list (if they are non-spent).
        vout += extended_vout

    # Once the number of outs and their index is known, they could be parsed.
    outs = []
    for i in vout:
        # The Satoshis amount is parsed, decoded and decompressed.
        data, offset = parse_b128(utxo, offset)
        amount = txout_decompress(b128_decode(data))
        # The output type is also parsed.
        out_type, offset = parse_b128(utxo, offset)
        out_type = b128_decode(out_type)
        # Depending on the type, the length of the following data will differ.  Types 0 and 1 refers to P2PKH and P2SH
        # encoded outputs. They are always followed 20 bytes of data, corresponding to the hash160 of the address (in
        # P2PKH outputs) or to the scriptHash (in P2PKH). Notice that the leading and tailing opcodes are not included.
        # If 2-5 is found, the following bytes encode a public key. The first by in this cases should be also included,
        # since it determines the format of the key.
        if out_type in [0, 1]:
            data_size = 40  # 20 bytes
        elif out_type in [2, 3, 4, 5]:
            data_size = 66  # 33 bytes (1 byte for the type + 32 bytes of data)
            offset -= 2
        # Finally, if another value is found, it represents the length of the following data, which is uncompressed.
        else:
            data_size = (out_type - NSPECIALSCRIPTS) * 2  # If the data is not compacted, the out_type corresponds
            # to the data size adding the number os special scripts (nSpecialScripts).

        # And finally the address (the hash160 of the public key actually)
        data, offset = utxo[offset:offset+data_size], offset + data_size
        outs.append({'index': i, 'amount': amount, 'out_type': out_type, 'data': data})

    # Once all the outs are processed, the block height is parsed
    height, offset = parse_b128(utxo, offset)
    height = b128_decode(height)
    # And the length of the serialized utxo is compared with the offset to ensure that no data remains unchecked.
    assert len(utxo) == offset

    return {'version': version, 'coinbase': coinbase, 'outs': outs, 'height': height}


def display_decoded_utxo(decoded_utxo):
    print "version: " + str(decoded_utxo['version'])
    print "isCoinbase: " + str(decoded_utxo['coinbase'])

    outs = decoded_utxo['outs']
    print "Number of outputs: " + str(len(outs))
    for out in outs:
        print "vout[" + str(out['index']) + "]:"
        print "\tSatoshi amount: " + str(out['amount'])
        print "\tOutput code type: " + out['out_type']
        print "\tHash160 (Address): " + out['address']

    print "Block height: " + str(decoded_utxo['height'])


def check_signature(signature):
    l = (len(signature[4:]) - 2) / 2

    if signature[:2] != "30":
        raise Exception("Wrong signature format.")
    elif int(signature[2:4], 16) != l:
        raise Exception("Wrong signature length " + str(l))
    else:
        return True


def check_public_key(pk):
    prefix = pk[0:2]
    l = len(pk)

    if prefix not in ["02", "03", "04"]:
        raise Exception("Wrong public key format.")
    if prefix == "04" and l != 130:
        raise Exception("Wrong length for an uncompressed public key: " + str(l))
    elif prefix in ["02", "03"] and l != 64:
        raise Exception("Wrong length for a compressed public key: " + str(l))
    else:
        return True


def check_address(btc_addr, network='test'):
    if network in ['test', "testnet"] and btc_addr[0] not in ['m', 'n']:
        raise Exception("Wrong testnet address format.")
    elif network in ['main', 'mainnet'] and btc_addr[0] != '1':
        raise Exception("Wrong mainnet address format.")
    elif network not in ['test', 'testnet', 'main', 'mainnet']:
        raise Exception("Network must be test/testnet or main/mainnet")
    else:
        return True


# ToDo: Change for script
def deserialize_script(script):
    start = "CScript(["
    end = "])"

    ps = CScript(a2b_hex(script)).__repr__()
    ps = ps[ps.index(start)+len(start): ps.index(end)].split(", ")

    for i in range(len(ps)):
        if ps[i].startswith('x('):
            ps[i] = ps[i][3:-2]
            ps[i] = '<' + ps[i] + '>'

    return " ".join(ps)


def serialize_script(data):
    hex_string = ""
    for e in data.split(" "):
        if e[0] == "<" and e[-1] == ">":
            hex_string += b2a_hex(CScriptOp.encode_op_pushdata(a2b_hex(e[1:-1])))
        elif eval(e) in OPCODE_NAMES:
            hex_string += format(eval(e), '02x')
        else:
            raise Exception

    return hex_string





