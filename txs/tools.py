def change_endianness(x):
    # If there is an odd number of elements, we make it even by adding a 0
    if (len(x) % 2) == 1:
        x += "0"
    y = x.decode('hex')
    z = y[::-1]
    return z.encode('hex')


def int2bytes(a, b):
    return ('%0' + str(2 * b) + 'x') % a


def parse_element(tx, size):
    element = tx.hex[tx.offset:tx.offset + size * 2]
    tx.offset += size * 2
    return element


def parse_varint(tx):
    data = tx.hex[tx.offset:]
    assert (len(data) > 0)
    size = int(data[:2], 16)
    assert (size <= 255)

    if size <= 252:
        storage_length = 1
        varint = data[:2]
    else:
        if size == 253:  # 0xFD
            storage_length = 3
        elif size == 254:  # 0xFE
            storage_length = 5
        elif size == 255:  # 0xFF
            storage_length = 9
        else:
            raise Exception("Wrong input data size")

        varint = data[:storage_length * 2]

    tx.offset += storage_length * 2

    return varint


def decode_varint(varint):
    if len(varint) > 2:
        decoded_varint = int(change_endianness(varint[2:]), 16)
    else:
        decoded_varint = int(varint, 16)

    return decoded_varint


def encode_varint(value):
    size = len(format(value, 'x'))
    if size == 1:
        varint = int2bytes(value, size)
    else:
        size /= 2
        if size == 2:
            prefix = 253  # 0xFD
        elif size == 4:
            prefix = 254  # 0xFE
        elif size == 8:
            prefix = 255  # 0xFF
        else:
            raise Exception("Wrong input data size")

        varint = format(prefix, 'x') + change_endianness(int2bytes(value, size))

    return varint
