import plyvel
from binascii import hexlify, unhexlify
import ujson
from math import ceil
from copy import deepcopy
from bitcoin_tools.analysis.status import *
from bitcoin_tools.utils import change_endianness, encode_varint
from bitcoin_tools.core.script import OutputScript
from bitcoin_tools.core.keys import get_uncompressed_pk


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
    :return: The decompressed amount of satoshi.
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
    """ Parses a given serialized UTXO to extract a base-128 varint.

    :param utxo: Serialized UTXO from which the varint will be parsed.
    :type utxo: hex str
    :param offset: Offset where the beginning of the varint if located in the UTXO.
    :type offset: int
    :return: The extracted varint, and the offset of the byte located right after it.
    :rtype: hex str, int
    """

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


def decode_utxo(coin, outpoint):
    """
    Decodes a LevelDB serialized UTXO for Bitcoin core v 0.15 onwards. The serialized format is defined in the Bitcoin
    Core source code as outpoint:coin.

    Outpoint structure is as follows: key | tx_hash | index.

    Where the key corresponds to b'C', or 43 in hex. The transaction hash in encoded in Little endian, and the index
    is a base128 varint. The corresponding Bitcoin Core source code can be found at:

    https://github.com/bitcoin/bitcoin/blob/ea729d55b4dbd17a53ced474a8457d4759cfb5a5/src/txdb.cpp#L40-L53

    On the other hand, a coin if formed by: code | value | out_type | script.

    Where code encodes the block height and whether the tx is coinbase or not, as 2*height + coinbase, the value is
    a txout_compressed base128 Varint, the out_type is also a base128 Varint, and the script is the remaining data.
    The corresponding Bitcoin Core soruce code can be found at:

    https://github.com/bitcoin/bitcoin/blob/6c4fecfaf7beefad0d1c3f8520bf50bb515a0716/src/coins.h#L58-L64

    :param coin: The coin to be decoded (extracted from the chainstate)
    :type coin: str
    :param outpoint: The outpoint to be decoded (extracted from the chainstate)
    :type outpoint: str
    :return; The decoded UTXO.
    :rtype: dict
    """

    # First we will parse all the data encoded in the outpoint, that is, the transaction id and index of the utxo.
    # Check that the input data corresponds to a transaction.
    assert outpoint[:2] == '43'
    # Check the provided outpoint has at least the minimum length (1 byte of key code, 32 bytes tx id, 1 byte index)
    assert len(outpoint) >= 68
    # Get the transaction id (LE) by parsing the next 32 bytes of the outpoint.
    tx_id = outpoint[2:66]
    # Finally get the transaction index by decoding the remaining bytes as a b128 VARINT
    tx_index = b128_decode(outpoint[66:])

    # Once all the outpoint data has been parsed, we can proceed with the data encoded in the coin, that is, block
    # height, whether the transaction is coinbase or not, value, script type and script.
    # We start by decoding the first b128 VARINT of the provided data, that may contain 2*Height + coinbase
    code, offset = parse_b128(coin)
    code = b128_decode(code)
    height = code >> 1
    coinbase = code & 0x01

    # The next value in the sequence corresponds to the utxo value, the amount of Satoshi hold by the utxo. Data is
    # encoded as a B128 VARINT, and compressed using the equivalent to txout_compressor.
    data, offset = parse_b128(coin, offset)
    amount = txout_decompress(b128_decode(data))

    # Finally, we can obtain the data type by parsing the last B128 VARINT
    out_type, offset = parse_b128(coin, offset)
    out_type = b128_decode(out_type)

    if out_type in [0, 1]:
        data_size = 40  # 20 bytes
    elif out_type in [2, 3, 4, 5]:
        data_size = 66  # 33 bytes (1 byte for the type + 32 bytes of data)
        offset -= 2
    # Finally, if another value is found, it represents the length of the following data, which is uncompressed.
    else:
        data_size = (out_type - NSPECIALSCRIPTS) * 2  # If the data is not compacted, the out_type corresponds
        # to the data size adding the number os special scripts (nSpecialScripts).

    # And the remaining data corresponds to the script.
    script = coin[offset:]

    # Assert that the script hash the expected length
    assert len(script) == data_size

    # And to conclude, the output can be encoded. We will store it in a list for backward compatibility with the
    # previous decoder
    out = {'amount': amount, 'out_type': out_type, 'data': script}

    # Even though there is just one output, we will identify it as outputs for backward compatibility with the previous
    # decoder.
    return {'tx_id': tx_id, 'index': tx_index, 'coinbase': coinbase, 'out': out, 'height': height}


def decompress_script(compressed_script, script_type):
    """ Takes CScript as stored in leveldb and returns it in uncompressed form
    (de)compression scheme is defined in bitcoin/src/compressor.cpp

    :param compressed_script: raw script bytes hexlified (data in decode_utxo)
    :type compressed_script: str
    :param script_type: first byte of script data (out_type in decode_utxo)
    :type script_type: int
    :return: the decompressed CScript
    :rtype: str
    """

    if script_type == 0:
        if len(compressed_script) != 40:
            raise Exception("Compressed script has wrong size")
        script = OutputScript.P2PKH(compressed_script, hash160=True)

    elif script_type == 1:
        if len(compressed_script) != 40:
            raise Exception("Compressed script has wrong size")
        script = OutputScript.P2SH(compressed_script)

    elif script_type in [2, 3]:
        if len(compressed_script) != 66:
            raise Exception("Compressed script has wrong size")
        script = OutputScript.P2PK(compressed_script)

    elif script_type in [4, 5]:
        if len(compressed_script) != 66:
            raise Exception("Compressed script has wrong size")
        prefix = format(script_type - 2, '02')
        script = OutputScript.P2PK(get_uncompressed_pk(prefix + compressed_script[2:]))

    else:
        assert len(compressed_script) / 2 == script_type - NSPECIALSCRIPTS
        script = OutputScript.from_hex(compressed_script)

    return script.content


def display_decoded_utxo(decoded_utxo):
    """ Displays the information extracted from a decoded UTXO from the chainstate.

    :param decoded_utxo: Decoded UTXO from the chainstate
    :type decoded_utxo: dict
    :return: None
    :rtype: None
    """

    print "isCoinbase: " + str(decoded_utxo['coinbase'])

    out = decoded_utxo['out']
    print "vout[" + str(decoded_utxo['index']) + "]:"
    print "\tSatoshi amount: " + str(out['amount'])
    print "\tOutput code type: " + str(out['out_type'])
    print "\tHash160 (Address): " + out['data']

    print "Block height: " + str(decoded_utxo['height'])


def parse_ldb(fout_name, fin_name=CFG.chainstate_path, decode=True):
    """
    Parsed data from the chainstate LevelDB and stores it in a output file.
    :param fout_name: Name of the file to output the data.
    :type fout_name: str
    :param fin_name: Name of the LevelDB folder (CFG.chainstate_path by default)
    :type fin_name: str
    :param decode: Whether the parsed data is decoded before stored or not (default: True)
    :type decode: bool
    :return: None
    :rtype: None
    """

    prefix = b'C'

    # Output file
    fout = open(CFG.data_path + fout_name, 'w')
    # Open the LevelDB
    db = plyvel.DB(fin_name, compression=None)  # Change with path to chainstate

    # Load obfuscation key (if it exists)
    o_key = db.get((unhexlify("0e00") + "obfuscate_key"))

    # If the key exists, the leading byte indicates the length of the key (8 byte by default). If there is no key,
    # 8-byte zeros are used (since the key will be XORed with the given values).
    if o_key is not None:
        o_key = hexlify(o_key)[2:]

    # For every UTXO (identified with a leading 'c'), the key (tx_id) and the value (encoded utxo) is displayed.
    # UTXOs are obfuscated using the obfuscation key (o_key), in order to get them non-obfuscated, a XOR between the
    # value and the key (concatenated until the length of the value is reached) if performed).
    for key, o_value in db.iterator(prefix=prefix):
        serialized_length = len(key) + len(o_value)
        key = hexlify(key)
        if o_key is not None:
            utxo = deobfuscate_value(o_key, hexlify(o_value))
        else:
            utxo = hexlify(o_value)

        # If the decode flag is passed, we also decode the utxo before storing it. This is really useful when running
        # a full analysis since will avoid decoding the whole utxo set twice (once for the utxo and once for the tx
        # based analysis)
        if decode:
            utxo = decode_utxo(utxo, key)
            utxo['len'] = serialized_length

        fout.write(ujson.dumps(utxo, sort_keys=True) + "\n")

    fout.close()
    db.close()


def get_chainstate_lastblock(fin_name=CFG.chainstate_path):
    """
    Gets the block hash of the last block a given chainstate folder is updated to.
    :param fin_name: chainstate folder name
    :type fin_name: str
    :return: The block hash (Big Endian)
    :rtype: str
    """

    # Open the chainstate
    db = plyvel.DB(fin_name, compression=None)

    # Load obfuscation key (if it exists)
    o_key = db.get((unhexlify("0e00") + "obfuscate_key"))

    # Get the key itself (the leading byte indicates only its size)
    if o_key is not None:
        o_key = hexlify(o_key)[2:]

    # Get the obfuscated block hash
    o_height = db.get(b'B')

    # Deobfuscate the height
    height = deobfuscate_value(o_key, hexlify(o_height))

    return change_endianness(height)


def aggregate_dust_np(fin_name, fout_name="dust.json", fltr=None):
    """
    Aggregates all the dust / non-profitable (np) utxos of a given parsed utxo file (from utxo_dump function).

    :param fin_name: Input file name, from where data wil be loaded.
    :type fin_name: str
    :param fout_name: Output file name, where data will be stored.
    :type fout_name: str
    :param fltr: Filter to be applied to the samples. None by default.
    :type fltr: function
    :return: A dict with the aggregated data
    :rtype: dict
    """

    # Dust calculation
    # Input file
    fin = open(CFG.data_path + fin_name, 'r')

    dust = {fee_per_byte: 0 for fee_per_byte in range(MIN_FEE_PER_BYTE, MAX_FEE_PER_BYTE+FEE_STEP, FEE_STEP)}
    value_dust = deepcopy(dust)
    data_len_dust = deepcopy(dust)

    np = deepcopy(dust)
    value_np = deepcopy(dust)
    data_len_np = deepcopy(dust)

    npest = deepcopy(dust)
    value_npest = deepcopy(dust)
    data_len_npest = deepcopy(dust)

    total_utxo = 0
    total_value = 0
    total_data_len = 0

    for line in fin:
        data = ujson.loads(line[:-1])

        # Apply filter if it is set, otherwise all samples are analyzed (sample is only skipped if there is a filter
        # and the data does not match the condition)
        if not fltr or (fltr and fltr(data)):
            # If the UTXO is dust for the checked range, we increment the dust count, dust value and dust length for the
            # given threshold.
            if MIN_FEE_PER_BYTE <= data['dust'] <= MAX_FEE_PER_BYTE:
                rate = data['dust']
                dust[rate] += 1
                value_dust[rate] += data["amount"]
                data_len_dust[rate] += data["utxo_data_len"]

            # Same with non-profitable outputs.
            if MIN_FEE_PER_BYTE <= data['non_profitable'] <= MAX_FEE_PER_BYTE:
                rate = data['non_profitable']
                np[rate] += 1
                value_np[rate] += data["amount"]
                data_len_np[rate] += data["utxo_data_len"]

            # Same with estimated non-profitable outputs.
            if MIN_FEE_PER_BYTE <= data['non_profitable_est'] <= MAX_FEE_PER_BYTE:
                rate = data['non_profitable_est']
                npest[rate] += 1
                value_npest[rate] += data["amount"]
                data_len_npest[rate] += data["utxo_data_len"]

        # And we increase the total counters for each read utxo.
        total_utxo = total_utxo + 1
        total_value += data["amount"]
        total_data_len += data["utxo_data_len"]

    fin.close()

    # Moreover, since if an output is dust/non-profitable for a given threshold, it will also be for every other step
    # onwards, we accumulate the result of a given step with the accumulated value from the previous step.
    for fee_per_byte in range(MIN_FEE_PER_BYTE+FEE_STEP, MAX_FEE_PER_BYTE, FEE_STEP):
        dust[fee_per_byte] += dust[fee_per_byte - FEE_STEP]
        value_dust[fee_per_byte] += value_dust[fee_per_byte - FEE_STEP]
        data_len_dust[fee_per_byte] += data_len_dust[fee_per_byte - FEE_STEP]

        np[fee_per_byte] += np[fee_per_byte - FEE_STEP]
        value_np[fee_per_byte] += value_np[fee_per_byte - FEE_STEP]
        data_len_np[fee_per_byte] += data_len_np[fee_per_byte - FEE_STEP]

        npest[fee_per_byte] += npest[fee_per_byte - FEE_STEP]
        value_npest[fee_per_byte] += value_npest[fee_per_byte - FEE_STEP]
        data_len_npest[fee_per_byte] += data_len_npest[fee_per_byte - FEE_STEP]

    # Finally we create the output with the accumulated data and store it.
    data = {"dust_utxos": dust, "dust_value": value_dust, "dust_data_len": data_len_dust,
            "np_utxos": np, "np_value": value_np, "np_data_len": data_len_np,
            "npest_utxos": npest, "npest_value": value_npest, "npest_data_len": data_len_npest,
            "total_utxos": total_utxo, "total_value": total_value, "total_data_len": total_data_len}

    # Store dust calculation in a file.
    out = open(CFG.data_path + fout_name, 'w')
    out.write(ujson.dumps(data))
    out.close()

    return data


def check_multisig(script, std=True):
    """
    Checks whether a given script is a multisig one. By default, only standard multisig script are accepted.

    :param script: The script to be checked.
    :type script: str
    :param std: Whether the script is standard or not.
    :type std: bool
    :return: True if the script is multisig (under the std restrictions), False otherwise.
    :rtype: bool
    """

    if std:
        # Standard bare Pay-to-multisig only accepts up to 3-3.
        r = range(81, 83)
    else:
        # m-of-n combination is valid up to 20.
        r = range(84, 101)

    if int(script[:2], 16) in r and script[2:4] in ["21", "41"] and script[-2:] == "ae":
        return True
    else:
        return False


def check_multisig_type(script):
    """
    Checks whether a given script is a multisig one. If it is multisig, return type (m and n values).

    :param script: The script to be checked.
    :type script: str
    :return: "multisig-m-n" or False
    """

    if len(OutputScript.deserialize(script).split()) > 2:
        m = OutputScript.deserialize(script).split()[0]
        n = OutputScript.deserialize(script).split()[-2]
        op_multisig = OutputScript.deserialize(script).split()[-1]

        if op_multisig == "OP_CHECKMULTISIG" and script[2:4] in ["21", "41"]:
            return "multisig-" + str(m) + "-" + str(n)

    return False


def check_opreturn(script):
    """
    Checks whether a given script is an OP_RETURN one.

    Warning: there should NOT be any OP_RETURN output in the UTXO set.

    :param script: The script to be checked.
    :type script: str
    :return: True if the script is an OP_RETURN, False otherwise.
    :rtype: bool
    """
    op_return_opcode = 0x6a
    return int(script[:2], 16) == op_return_opcode


def check_native_segwit(script):
    """
    Checks whether a given output script is a native SegWit type.

    :param script: The script to be checked.
    :type script: str
    :return: tuple, (True, segwit type) if the script is a native SegWit, (False, None) otherwise
    :rtype: tuple, first element boolean
    """

    if len(script) == 22*2 and script[:4] == "0014":
        return True, "P2WPKH"

    if len(script) == 34*2 and script[:4] == "0020":
        return True, "P2WSH"

    return False, None


def get_min_input_size(out, height, count_p2sh=False, coin="bitcoin", compressed_pk_height=0):
    """
    Computes the minimum size an input created by a given output type (parsed from the chainstate) will have.
    The size is computed in two parts, a fixed size that is non type dependant, and a variable size which
    depends on the output type.

    :param out: Output to be analyzed.
    :type out: dict
    :param height: Block height where the utxo was created. Used to set P2PKH min_size.
    :type height: int
    :param count_p2sh: Whether P2SH should be taken into account.
    :type count_p2sh: bool
    :param: Coin to be used in the analysis (default: bitcoin).
    :type coin: str
    :param compressed_pk_height: Height at which compressed public keys where first used. For coins different that
    Bitcoin, Bitcoin Cash and Litecoin, and analysis of when compressed pk where used for the first time has not been
    performed yet. Set the compressed_pk_height as you pleased for those cases.
    :type compressed_pk_height: int
    :return: The minimum input size of the given output type.
    :rtype: int
    """

    out_type = out["out_type"]
    script = out["data"]

    # Fixed size
    prev_tx_id = 32
    prev_out_index = 4
    nSequence = 4

    fixed_size = prev_tx_id + prev_out_index + nSequence

    # Variable size (depending on scripSig):
    # Public key size can be either 33 or 65 bytes, depending on whether the key is compressed or uncompressed. We wil
    # make them fall in one of the categories depending on the block height in which the transaction was included.
    #
    # Signatures size is contained between 71-73 bytes depending on the size of the S and R components of the signature.
    # Since we are looking for the minimum size, we will consider all signatures to be 71-byte long in order to define
    # a lower bound.

    if out_type is 0:
        # P2PKH
        if coin in ["bitcoin", "bitcoincash"]:
            # Bitcoin core starts using compressed pk in version (0.6.0, 30/03/12, around block height 173480)
            height_limit = 173480
        elif coin == "litecoin":
            # v0.6.0 (march 2012) is block 110K for litecoin
            height_limit = 110000
        else:
            height_limit = compressed_pk_height
            if height_limit == 0:
                print "Warning: You are calculating the minimum input size for a coin other than Bitcoin, " \
                      "Bitcoin Cash and Litecoin. By default the height ar which compressed public keys where first " \
                      "used is not set, so 0 is used. Consider changing the compressed_pk_height "

        if height < height_limit:
            # uncompressed keys
            scriptSig = 138  # PUSH sig (1 byte) + sig (71 bytes) + PUSH pk (1 byte) + uncompressed pk (65 bytes)
        else:
            # compressed keys
            scriptSig = 106  # PUSH sig (1 byte) + sig (71 bytes) + PUSH pk (1 byte) + compressed pk (33 bytes)
        scriptSig_len = 1
    elif out_type is 1:
        # P2SH
        # P2SH inputs can have arbitrary length. Defining the length of the original script by just knowing the hash
        # is infeasible. Two approaches can be followed in this case. The first one consists on considering P2SH
        # by defining the minimum length a script of such type could have. The other approach will be ignoring such
        # scripts when performing the dust calculation.
        if count_p2sh:
            # If P2SH UTXOs are considered, the minimum script that can be created has only 1 byte (OP_1 for example)
            scriptSig = 1
            scriptSig_len = 1
        else:
            # Otherwise, we will define the length as 0 and skip such scripts for dust calculation.
            scriptSig = -fixed_size
            scriptSig_len = 0
    elif out_type in [2, 3, 4, 5]:
        # P2PK
        # P2PK requires a signature and a push OP_CODE to push the signature into the stack. The format of the public
        # key (compressed or uncompressed) does not affect the length of the signature.
        scriptSig = 72  # PUSH sig (1 byte) + sig (71 bytes)
        scriptSig_len = 1
    else:
        segwit = check_native_segwit(script)
        # P2MS
        if check_multisig(script):
            # Multisig can be 15-15 at most.
            req_sigs = int(script[:2], 16) - 80  # OP_1 is hex 81
            scriptSig = 1 + (req_sigs * 72)  # OP_0 (1 byte) + 72 bytes per sig (PUSH sig (1 byte) + sig (71 bytes))
            scriptSig_len = int(ceil(scriptSig / float(256)))
        elif segwit[0] and segwit[1] == "P2WPKH":
            scriptSig = 27 # PUSH sig (1 byte) + sig (71 bytes) + PUSH pk (1 byte) + pk (33 bytes) (106 / 4 = 27)
            scriptSig_len = 1
        else:
            # All other types (non-standard outs) are counted just as the fixed size + 1 byte of the scripSig_len
            scriptSig = 0
            scriptSig_len = 1

    var_size = scriptSig_len + scriptSig

    return fixed_size + var_size


def load_estimation_data(coin):
    """
    Returns estimation data for public key sizes, and P2SH, non-std and P2WSH input/witness script sizes. If no
    estimation data is available, returns a tuple of None values.

    :param coin: string (bitcoin, bitcoincash or litecoin)
    :return: 5-element tuple: a dictionary 3 floats and a int, with estimation data by height (dict), average estimation
    data (floats) and the maximum height at which we have estimation data (int).
    """

    try:
        with open(CFG.estimated_data_dir + coin + "/p2pkh_pubkey_avg_size_height_output.json") as f:
            p2pkh_pksize = ujson.load(f)
            max_height = len(p2pkh_pksize)

        with open(CFG.estimated_data_dir + coin + "/p2sh.json") as f:
            p2sh_scriptsize = ujson.load(f)

        with open(CFG.estimated_data_dir + coin + "/nonstd.json") as f:
            nonstd_scriptsize = ujson.load(f)

        with open(CFG.estimated_data_dir + coin + "/p2wsh.json") as f:
            p2wsh_scriptsize = ujson.load(f)

    except IOError:
        print "Warning: No estimation data found. Non-profitable estimation charts will always show 0."
        p2pkh_pksize, p2sh_scriptsize, nonstd_scriptsize, p2wsh_scriptsize, max_height = None, None, None, None, None

    return p2pkh_pksize, p2sh_scriptsize, nonstd_scriptsize, p2wsh_scriptsize, max_height


def get_est_input_size(out, height, p2pkh_pksize, p2sh_scriptsize, nonstd_scriptsize, p2wsh_scriptsize, max_height):
    """
    Computes the estimated size an input created by a given output type (parsed from the chainstate) will have.
    The size is computed in two parts, a fixed size that is non type dependant, and a variable size which
    depends on the output type.

    If no estimation data is available, returns NaN.

    :param out: Output to be analyzed.
    :type out: dict
    :param height: Block height where the utxo was created. Used to set P2PKH min_size.
    :type height: int
    :param p2pkh_pksize: Estimation data for P2PKH outputs.
    :type p2pkh_pksize: dict
    :param p2sh_scriptsize: Estimation data for P2SH outputs.
    :type p2sh_scriptsize: float
    :param nonstd_scriptsize: Estimation data for non-standard outputs.
    :type nonstd_scriptsize: float
    :param p2wsh_scriptsize: Estimation data fot P2WSH outputs.
    :type p2wsh_scriptsize: float
    :param max_height: Last block from which we have estimation data.
    :type max_height: int
    :return: The minimum input size of the given output type.
    :rtype: int
    """

    if p2pkh_pksize is None:
        # If no estimation data is available, return Nan.
        return float('nan')

    out_type = out["out_type"]
    script = out["data"]

    # Fixed size
    prev_tx_id = 32
    prev_out_index = 4
    nSequence = 4

    fixed_size = prev_tx_id + prev_out_index + nSequence

    # Variable size (depending on scripSig):
    # Public key size can be either 33 or 65 bytes, depending on whether the key is compressed or uncompressed. We will
    # use data from the blockchain to estimate it depending on block height.
    #
    # Signatures size is contained between 71-73 bytes depending on the size of the S and R components of the signature.
    # Since the most common size is 72, we will consider all signatures to be 72-byte long.

    # If we don't have updated estimation data, a warning will be displayed and the last estimation point will be used
    # for the rest of values.
    if height >= max_height:
        print "Warning: There is no estimation data for that height. The last available estimation will be used."

    if out_type is 0:
        # P2PKH
        if height >= max_height:
            p2pkh_est_data = p2pkh_pksize[str(max_height - 1)]
        else:
            p2pkh_est_data = p2pkh_pksize[str(height)]
        scriptSig = 74 + p2pkh_est_data  # PUSH sig (1 byte) + sig (72 bytes) + PUSH pk (1 byte) + PK est
        scriptSig_len = 1
    elif out_type is 1:
        # P2SH
        scriptSig = p2sh_scriptsize
        scriptSig_len = int(ceil(scriptSig / float(256)))
    elif out_type in [2, 3, 4, 5]:
        # P2PK
        # P2PK requires a signature and a push OP_CODE to push the signature into the stack. The format of the public
        # key (compressed or uncompressed) does not affect the length of the signature.
        scriptSig = 73  # PUSH sig (1 byte) + sig (72 bytes)
        scriptSig_len = 1
    else:
        segwit = check_native_segwit(script)
        # P2MS
        if check_multisig(script):
            # Multisig can be 15-15 at most.
            req_sigs = int(script[:2], 16) - 80  # OP_1 is hex 81
            scriptSig = 1 + (req_sigs * 73)  # OP_0 (1 byte) + 72 bytes per sig (PUSH sig (1 byte) + sig (72 bytes))
            scriptSig_len = int(ceil(scriptSig / float(256)))
        elif segwit[0] and segwit[1] == "P2WPKH":
            scriptSig = 27 # PUSH sig (1 byte) + sig (72 bytes) + PUSH pk (1 byte) + pk (33 bytes) (107 / 4 = 27)
            scriptSig_len = 1
        elif segwit[0] and segwit[1] == "P2WSH":
            scriptSig = ceil(p2wsh_scriptsize/4.0)
            scriptSig_len = int(ceil(scriptSig / float(256)))
        else:
            # All other types (non-standard outs)
            scriptSig = nonstd_scriptsize
            scriptSig_len = int(ceil(scriptSig / float(256)))

    var_size = scriptSig_len + scriptSig

    return fixed_size + var_size


def get_utxo(tx_id, index, fin_name=CFG.chainstate_path):
    """
    Gets a UTXO from the chainstate identified by a given transaction id and index.
    If the requested UTXO does not exist, return None.

    :param tx_id: Transaction ID that identifies the UTXO you are looking for.
    :type tx_id: str
    :param index: Index that identifies the specific output.
    :type index: int
    :param fin_name: Name of the LevelDB folder (chainstate by default)
    :type fin_name: str
    :return: A outpoint:coin pair representing the requested UTXO
    :rtype: str, str
    """

    prefix = b'C'
    outpoint = prefix + unhexlify(tx_id + b128_encode(index))

    # Open the LevelDB
    db = plyvel.DB(fin_name, compression=None)  # Change with path to chainstate

    # Load obfuscation key (if it exists)
    o_key = db.get((unhexlify("0e00") + "obfuscate_key"))

    # If the key exists, the leading byte indicates the length of the key (8 byte by default). If there is no key,
    # 8-byte zeros are used (since the key will be XORed with the given values).
    if o_key is not None:
        o_key = hexlify(o_key)[2:]

    coin = db.get(outpoint)

    if coin is not None and o_key is not None:
        coin = deobfuscate_value(o_key, hexlify(coin))

    db.close()

    return hexlify(outpoint), coin


def deobfuscate_value(obfuscation_key, value):
    """
    De-obfuscate a given value parsed from the chainstate.

    :param obfuscation_key: Key used to obfuscate the given value (extracted from the chainstate).
    :type obfuscation_key: str
    :param value: Obfuscated value.
    :type value: str
    :return: The de-obfuscated value.
    :rtype: str.
    """

    l_value = len(value)
    l_obf = len(obfuscation_key)

    # Get the extended obfuscation key by concatenating the obfuscation key with itself until it is as large as the
    # value to be de-obfuscated.
    if l_obf < l_value:
        extended_key = (obfuscation_key * ((l_value / l_obf) + 1))[:l_value]
    else:
        extended_key = obfuscation_key[:l_value]

    r = format(int(value, 16) ^ int(extended_key, 16), 'x')

    # In some cases, the obtained value could be 1 byte smaller than the original, since the leading 0 is dropped off
    # when the formatting.
    if len(r) == l_value-1:
        r = r.zfill(l_value)

    assert len(value) == len(r)

    return r


def roundup_rate(fee_rate, fee_step=FEE_STEP):

    """
    Rounds up a given fee rate to the nearest fee_step (FEE_STEP by default). If the rounded value it the value itself,
    adds fee_step, assuring that the returning rate is always bigger than the given one.

    :param fee_rate: Fee rate to be rounded up.
    :type fee_rate: float
    :param fee_step: Value at which fee_rate will be round up (FEE_STEP by default)
    :type fee_step: int
    :return: The rounded up fee_rate.
    :rtype: int
    """

    try:
        # If the value to be rounded is already multiple of the fee step, we just add another step. Otherwise the value
        # is rounded up.
        if fee_rate == 0:
            rate = fee_rate
        elif (fee_rate % fee_step) == 0:
            rate = int(fee_rate + fee_step)
        else:
            rate = int(ceil(fee_rate / float(fee_step))) * fee_step
    except ValueError:
        # fee_rate may be NaN (for the non-profitable estimation metric when no estimation data is available).
        # In this case, return None (ujson can not deal with NaNs).
        rate = None

    return rate


def get_serialized_size(utxo, verbose=True):
    """
    Computes the uncompressed serialized size of an UTXO. This version is slower than get_serialized_size_fast version
    (Don't you say!) since it performs the actual decompress and online calculation of the size of the script.

    Watch out! Use get_serialized_size_fast when parsing the whole UTXO set, this version will make you spend way more
    time.

    :param utxo: unspent output to compute the size
    :type utxo: dict
    :param verbose: Just warns you about using the slow version.
    :type verbose: bool
    :return: size in bytes
    :rtype int
    """

    if verbose:
        print("You're using the non-fast version of get_serialized_size. You may want to use the fast version specially"
              "if parsing the whole UTXO set")

    # Decompress the UTXO script
    out_script = decompress_script(utxo.get('data'), utxo.get('out_type'))
    out_size = len(out_script) / 2

    # Add the number of bytes corresponding to the scriptPubKey length
    out_size += len(encode_varint(out_size)) / 2

    # Add 8 bytes for bitcoin value
    out_size += 8

    return out_size


def get_serialized_size_fast(utxo):
    """
    Computes the uncompressed serialized size of an UTXO. The sizes are hardcoded in this version since they only depend
    on the script type. Therefore its way faster than get_serialized_size.

    Watch out! Use this version when parsing the whole UTXO set.

    :param utxo: unspent output to compute the size
    :type utxo: dict
    :return: size in bytes
    :rtype int
    """

    if utxo.get("out_type") is 0:
        # P2PKH: OP_DUP (1 byte) + OP_HASH160 (1 byte) + PUSH (1 byte) + HASH160 (20 bytes) + OP_EQUALVERIFY (1 byte) +
        # OP_CHECKSIG (1 byte) = 25 bytes
        out_size = 25
    elif utxo.get("out_type") is 1:
        # P2SH: OP_HASH160 (1 byte) + PUSH (1 byte) + HAS160 (20 bytes) + OP_EQUAL (1 byte) = 23 bytes
        out_size = 23
    elif utxo.get("out_type") in [2, 3]:
        # P2PK compressed: PUSH (1 byte) + compressed_pk (33 bytes) + OP_CHECKSIG (1 byte) = 35 bytes
        out_size = 35
    elif utxo.get("out_type") in [4, 5]:
        # P2PK uncompressed: PUSH (1 byte) + uncompressed_pk (65 bytes) + OP_CHECKSIG (1 byte) = 67 bytes
        out_size = 67
    else:
        # Any other type will have the full script stored in the utxo
        out_size = len(utxo.get("data")) / 2

    # Add the number of bytes corresponding to the scriptPubKey length
    out_size += len(encode_varint(out_size)) / 2

    # Add 8 bytes for bitcoin value
    out_size += 8

    return out_size

