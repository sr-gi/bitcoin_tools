from binascii import unhexlify, hexlify
from copy import deepcopy
from hashlib import sha256
from ecdsa import SigningKey
from bitcoin_tools.core.keys import serialize_pk, ecdsa_tx_sign
from bitcoin_tools.core.script import InputScript, OutputScript, Script, SIGHASH_ALL, SIGHASH_SINGLE, SIGHASH_NONE, \
    SIGHASH_ANYONECANPAY
from bitcoin_tools.utils import change_endianness, encode_varint, int2bytes, is_public_key, is_btc_addr, is_script, \
    parse_element, parse_varint, get_prev_ScriptPubKey


class TX:
    """ Defines a class TX (transaction) that holds all the modifiable fields of a Bitcoin transaction, such as
    version, number of inputs, reference to previous transactions, input and output scripts, value, etc.
    """

    def __init__(self):
        self.version = None
        self.inputs = None
        self.outputs = None
        self.nLockTime = None
        self.prev_tx_id = []
        self.prev_out_index = []
        self.scriptSig = []
        self.scriptSig_len = []
        self.nSequence = []
        self.value = []
        self.scriptPubKey = []
        self.scriptPubKey_len = []

        self.offset = 0
        self.hex = ""

    @classmethod
    def build_from_hex(cls, hex_tx):
        """
        Alias of deserialize class method.

        :param hex_tx: Hexadecimal serialized transaction.
        :type hex_tx: hex str
        :return: The transaction build using the provided hex serialized transaction.
        :rtype: TX
        """

        return cls.deserialize(hex_tx)

    @classmethod
    def build_from_scripts(cls, prev_tx_id, prev_out_index, value, scriptSig, scriptPubKey, fees=None):
        """ Builds a transaction from already built Input and Output scripts. This builder should be used when building
        custom transaction (Non-standard).

        :param prev_tx_id: Previous transaction id.
        :type prev_tx_id: either str or list of str
        :param prev_out_index: Previous output index. Together with prev_tx_id represent the UTXOs the current
        transaction is aiming to redeem.
        :type prev_out_index: either str or list of str
        :param value: Value in Satoshis to be spent.
        :type value: either int or list of int
        :param scriptSig: Input script containing the restrictions that will lock the transaction.
        :type scriptSig: either InputScript or list of InputScript
        :param scriptPubKey: Output script containing the redeem fulfilment conditions.
        :type scriptPubKey: either OutputScript or list of OutputScript
        :param fees: Fees that will be applied to the transaction. If set, fees will be subtracted from the last output.
        :type fees: int
        :return: The transaction build using the provided scripts.
        :rtype: TX
        """

        tx = cls()

        # Normalize all parameters
        if isinstance(prev_tx_id, str):
            prev_tx_id = [prev_tx_id]
        if isinstance(prev_out_index, int):
            prev_out_index = [prev_out_index]
        if isinstance(value, int):
            value = [value]
        if isinstance(scriptSig, InputScript):
            scriptSig = [scriptSig]
        if isinstance(scriptPubKey, OutputScript):
            scriptPubKey = [scriptPubKey]

        if len(prev_tx_id) is not len(prev_out_index) or len(prev_tx_id) is not len(scriptSig):
            raise Exception("The number ofs UTXOs to spend must match with the number os ScriptSigs to set.")
        elif len(scriptSig) == 0 or len(scriptPubKey) == 0:
            raise Exception("Scripts can't be empty")
        else:
            tx.version = 1

            # INPUTS
            tx.inputs = len(prev_tx_id)
            tx.prev_tx_id = prev_tx_id
            tx.prev_out_index = prev_out_index

            for i in range(tx.inputs):
                # ScriptSig
                tx.scriptSig_len.append(len(scriptSig[i].content) / 2)
                tx.scriptSig.append(scriptSig[i])

                tx.nSequence.append(pow(2, 32) - 1)  # ffffffff

            # OUTPUTS
            tx.outputs = len(scriptPubKey)

            for i in range(tx.outputs):
                tx.value.append(value[i])
                # ScriptPubKey
                tx.scriptPubKey_len.append(len(scriptPubKey[i].content) / 2)
                tx.scriptPubKey.append(scriptPubKey[i])  # Output script.

            # If fees have been set, subtract them from the final value. Otherwise, assume they have been already
            # subtracted when specifying the amounts.
            if fees:
                tx.value[-1] -= fees

            tx.nLockTime = 0

            tx.hex = tx.serialize()

        return tx

    @classmethod
    def build_from_io(cls, prev_tx_id, prev_out_index, value, outputs, fees=None, network='test'):
        """ Builds a transaction from a collection of inputs and outputs, such as previous transactions references and
        output references (either public keys, Bitcoin addresses, list of public keys (for multisig transactions), etc).
        This builder leaves the transaction ready to sign, so its the one to be used in most cases
        (Standard transactions).

        outputs format:

        P2PKH -> Bitcoin address, or list of Bitcoin addresses.
        e.g: output = btc_addr or output = [btc_addr0, btc_addr1, ...]

        P2PK -> Serialized Public key, or list of serialized pubic keys. (use keys.serialize_pk)
        e.g: output = pk or output = [pk0, pk1, ...]

        P2MS -> List of int (m) and public keys, or list of lists of int (m_i) and public keys. m represent the m-of-n
        number of public keys needed to redeem the transaction.
        e.g: output = [n, pk0, pk1, ...] or output = [[n_0, pk0_0, pk0_1, ...], [n_1, pk1_0, pk1_1, ...], ...]

        P2SH -> script hash (hash160 str hex) or list of hash 160s.
        e.g: output = da1745e9b549bd0bfa1a569971c77eba30cd5a4b or output = [da1745e9b549bd0bfa1a569971c77eba30cd5a4b,
        ...]

        :param prev_tx_id: Previous transaction id.
        :type prev_tx_id: either str or list of str
        :param prev_out_index: Previous output index. Together with prev_tx_id represent the UTXOs the current
        transaction is aiming to redeem.
        :type prev_out_index: either str or list of str
        :param value: Value in Satoshis to be spent.
        :type value: either int or list of int
        :param outputs: Information to build the output of the transaction.
        :type outputs: See above outputs format.
        :param fees: Fees that will be applied to the transaction. If set, fees will be subtracted from the last output.
        :type fees: int
        :param network: Network into which the transaction will be published (either mainnet or testnet).
        :type network: str
        :return: Transaction build with the input and output provided data.
        :rtype: TX
        """

        ins = []
        outs = []

        # Normalize all parameters
        if isinstance(prev_tx_id, str):
            prev_tx_id = [prev_tx_id]
        if isinstance(prev_out_index, int):
            prev_out_index = [prev_out_index]
        if isinstance(value, int):
            value = [value]
        if isinstance(outputs, str) or (isinstance(outputs, list) and isinstance(outputs[0], int)):
            outputs = [outputs]

        # If fees have been set, subtract them from the final value. Otherwise, assume they have been already
        # subtracted when specifying the amounts.
        if fees:
            value[-1] -= fees

        if len(prev_tx_id) != len(prev_out_index):
            raise Exception("Previous transaction id and index number of elements must match. " + str(len(prev_tx_id))
                            + "!= " + str(len(prev_out_index)))
        elif len(value) != len(outputs):
            raise Exception("Each output must have set a Satoshi amount. Use 0 if no value is going to be transferred.")

        for o in outputs:
            # Multisig outputs are passes ad an integer m representing the m-of-n transaction, amb m public keys.
            if isinstance(o, list) and o[0] in range(1, 15):
                pks = [is_public_key(pk) for pk in o[1:]]
                if all(pks):
                    oscript = OutputScript.P2MS(o[0], len(o) - 1, o[1:])
                else:
                    raise Exception("Bad output")
            elif is_public_key(o):
                oscript = OutputScript.P2PK(o)
            elif is_btc_addr(o, network):
                oscript = OutputScript.P2PKH(o)
            elif is_script(o):
                oscript = OutputScript.P2SH(o)
            else:
                raise Exception("Bad output")

            outs.append(deepcopy(oscript))

        for i in range(len(prev_tx_id)):
            # Temporarily set IS content to 0, since data will be signed afterwards.
            iscript = InputScript()
            ins.append(iscript)

        # Once all inputs and outputs has been formatted as scripts, we could construct the transaction with the proper
        # builder.
        tx = cls.build_from_scripts(prev_tx_id, prev_out_index, value, ins, outs)

        return tx

    @classmethod
    def deserialize(cls, hex_tx):
        """ Builds a transaction object from the hexadecimal serialization format of a transaction that
        could be obtained, for example, from a blockexplorer.

        :param hex_tx: Hexadecimal serialized transaction.
        :type hex_tx: hex str
        :return: The transaction build using the provided hex serialized transaction.
        :rtype: TX
        """

        tx = cls()
        tx.hex = hex_tx

        tx.version = int(change_endianness(parse_element(tx, 4)), 16)

        # INPUTS
        tx.inputs = int(parse_varint(tx), 16)

        for i in range(tx.inputs):
            tx.prev_tx_id.append(change_endianness(parse_element(tx, 32)))
            tx.prev_out_index.append(int(change_endianness(parse_element(tx, 4)), 16))
            # ScriptSig
            tx.scriptSig_len.append(int(parse_varint(tx), 16))
            tx.scriptSig.append(InputScript.from_hex(parse_element(tx, tx.scriptSig_len[i])))
            tx.nSequence.append(int(parse_element(tx, 4), 16))

        # OUTPUTS
        tx.outputs = int(parse_varint(tx), 16)

        for i in range(tx.outputs):
            tx.value.append(int(change_endianness(parse_element(tx, 8)), 16))
            # ScriptPubKey
            tx.scriptPubKey_len.append(int(parse_varint(tx), 16))
            tx.scriptPubKey.append(OutputScript.from_hex(parse_element(tx, tx.scriptPubKey_len[i])))

        tx.nLockTime = int(parse_element(tx, 4), 16)

        if tx.offset != len(tx.hex):
            raise Exception("There is some error in the serialized transaction passed as input. Transaction can't"
                            " be built")
        else:
            tx.offset = 0

        return tx

    def serialize(self, rtype=hex):
        """ Serialize all the transaction fields arranged in the proper order, resulting in a hexadecimal string
        ready to be broadcast to the network.

        :param self: self
        :type self: TX
        :param rtype: Whether the serialized transaction is returned as a hex str or a byte array.
        :type rtype: hex or bool
        :return: Serialized transaction representation (hexadecimal or bin depending on rtype parameter).
        :rtype: hex str / bin
        """

        if rtype not in [hex, bin]:
            raise Exception("Invalid return type (rtype). It should be either hex or bin.")
        serialized_tx = change_endianness(int2bytes(self.version, 4))  # 4-byte version number (LE).

        # INPUTS
        serialized_tx += encode_varint(self.inputs)  # Varint number of inputs.

        for i in range(self.inputs):
            serialized_tx += change_endianness(self.prev_tx_id[i])  # 32-byte hash of the previous transaction (LE).
            serialized_tx += change_endianness(int2bytes(self.prev_out_index[i], 4))  # 4-byte output index (LE)
            serialized_tx += encode_varint(len(self.scriptSig[i].content) / 2)   # Varint input script length.
            # ScriptSig
            serialized_tx += self.scriptSig[i].content  # Input script.
            serialized_tx += int2bytes(self.nSequence[i], 4)  # 4-byte sequence number.

        # OUTPUTS
        serialized_tx += encode_varint(self.outputs)  # Varint number of outputs.

        if self.outputs != 0:
            for i in range(self.outputs):
                serialized_tx += change_endianness(int2bytes(self.value[i], 8))  # 8-byte field Satoshi value (LE)
                # ScriptPubKey
                serialized_tx += encode_varint(len(self.scriptPubKey[i].content) / 2)   # Varint Output script length.
                serialized_tx += self.scriptPubKey[i].content  # Output script.

        serialized_tx += int2bytes(self.nLockTime, 4)  # 4-byte lock time field

        # If return type has been set to binary, the serialized transaction is converted.
        if rtype is bin:
            serialized_tx = unhexlify(serialized_tx)

        return serialized_tx

    def get_txid(self, rtype=hex, endianness="LE"):
        """ Computes the transaction id (i.e: transaction hash for non-segwit txs).
        :param rtype: Defines the type of return, either hex str or bytes.
        :type rtype: str or bin
        :param endianness: Whether the id is returned in BE (Big endian) or LE (Little Endian) (default one)
        :type endianness: str
        :return: The hash of the transaction (i.e: transaction id)
        :rtype: hex str or bin, depending on rtype parameter.
        """

        if rtype not in [hex, bin]:
            raise Exception("Invalid return type (rtype). It should be either hex or bin.")
        if endianness not in ["BE", "LE"]:
            raise Exception("Invalid endianness type. It should be either BE or LE.")

        if rtype is hex:
            tx_id = hexlify(sha256(sha256(self.serialize(rtype=bin)).digest()).digest())
            if endianness == "BE":
                tx_id = change_endianness(tx_id)
        else:
            tx_id = sha256(sha256(self.serialize(rtype=bin)).digest()).digest()
            if endianness == "BE":
                tx_id = unhexlify(change_endianness(hexlify(tx_id)))

        return tx_id

    def sign(self, sk, index, hashflag=SIGHASH_ALL, compressed=True, orphan=False, deterministic=True, network='test'):
        """ Signs a transaction using the provided private key(s), index(es) and hash type. If more than one key and index
        is provides, key i will sign the ith input of the transaction.

        :param sk: Private key(s) used to sign the ith transaction input (defined by index).
        :type sk: SigningKey or list of SigningKey.
        :param index: Index(es) to be signed by the provided key(s).
        :type index: int or list of int
        :param hashflag: Hash type to be used. It will define what signature format will the unsigned transaction have.
        :type hashflag: int
        :param compressed: Indicates if the public key that goes along with the signature will be compressed or not.
        :type compressed: bool
        :param orphan: Whether the inputs to be signed are orphan or not. Orphan inputs are those who are trying to
        redeem from a utxo that has not been included in the blockchain or has not been seen by other nodes.
        Orphan inputs must provide a dict with the index of the input and an OutputScript that matches the utxo to be
        redeemed.
            e.g:
              orphan_input = dict({0: OutputScript.P2PKH(btc_addr))
        :type orphan:  dict(index, InputScript)
        :param deterministic: Whether the signature is performed using a deterministic k or not. Set by default.
        :type deterministic: bool
        :param network: Network from which the previous ScripPubKey will be queried (either main or test).
        :type network: str
        :return: Transaction signature.
        :rtype: str
        """

        # Normalize all parameters
        if isinstance(sk, list) and isinstance(index, int):
            # In case a list for multisig is received as only input.
            sk = [sk]
        if isinstance(sk, SigningKey):
            sk = [sk]
        if isinstance(index, int):
            index = [index]

        for i in range(len(sk)):

            # If the input to be signed is orphan, the OutputScript of the UTXO to be redeemed will be passed to
            # the signature_format function, otherwise False is passed and the UTXO will be requested afterwards.
            o = orphan if not orphan else orphan.get(i)
            # The unsigned transaction is formatted depending on the input that is going to be signed. For input i,
            # the ScriptSig[i] will be set to the scriptPubKey of the UTXO that input i tries to redeem, while all
            # the other inputs will be set blank.
            unsigned_tx = self.signature_format(index[i], hashflag, o, network)

            # Then, depending on the format how the private keys have been passed to the signing function
            # and the content of the ScripSig field, a different final scriptSig will be created.
            if isinstance(sk[i], list) and unsigned_tx.scriptSig[index[i]].type is "P2MS":
                sigs = []
                for k in sk[i]:
                    sigs.append(ecdsa_tx_sign(unsigned_tx.serialize(), k, hashflag, deterministic))
                iscript = InputScript.P2MS(sigs)
            elif isinstance(sk[i], SigningKey) and unsigned_tx.scriptSig[index[i]].type is "P2PK":
                s = ecdsa_tx_sign(unsigned_tx.serialize(), sk[i], hashflag, deterministic)
                iscript = InputScript.P2PK(s)
            elif isinstance(sk[i], SigningKey) and unsigned_tx.scriptSig[index[i]].type is "P2PKH":
                s = ecdsa_tx_sign(unsigned_tx.serialize(), sk[i], hashflag, deterministic)
                pk = serialize_pk(sk[i].get_verifying_key(), compressed)
                iscript = InputScript.P2PKH(s, pk)
            elif unsigned_tx.scriptSig[index[i]].type is "unknown":
                raise Exception("Unknown previous transaction output script type. Can't sign the transaction.")
            else:
                raise Exception("Can't sign input " + str(i) + " with the provided data.")

            # Finally, temporal scripts are stored as final and the length of the script is computed
            self.scriptSig[i] = iscript
            self.scriptSig_len[i] = len(iscript.content) / 2

        self.hex = self.serialize()

    def signature_format(self, index, hashflag=SIGHASH_ALL, orphan=False, network='test'):
        """ Builds the signature format an unsigned transaction has to follow in order to be signed. Basically empties
        every InputScript field but the one to be signed, identified by index, that will be filled with the OutputScript
        from the UTXO that will be redeemed.

        The format of the OutputScripts will depend on the hashflag:
            - SIGHASH_ALL leaves OutputScript unchanged.
            - SIGHASH_SINGLE should sign each input with the output of the same index (not implemented yet).
            - SIGHASH_NONE empies all the outputs.
            - SIGHASH_ANYONECANPAY not sure about what should do (obviously not implemented yet).

        :param index: The index of the input to be signed.
        :type index: int
        :param hashflag: Hash type to be used, see above description for further information.
        :type hashflag: int
        :param orphan: Whether the input is orphan or not. Orphan inputs must provide an OutputScript that matches the
        utxo to be redeemed.
        :type orphan: OutputScript
        :param network: Network into which the transaction will be published (either mainnet or testnet).
        :type network: str
        :return: Transaction properly formatted to be signed.
        :rtype TX
        """

        tx = deepcopy(self)
        for i in range(tx.inputs):
            if i is index:
                if not orphan:
                    script, t = get_prev_ScriptPubKey(tx.prev_tx_id[i], tx.prev_out_index[i], network)
                    # Once we get the previous UTXO script, the inputScript is temporarily set to it in order to sign
                    # the transaction.
                    tx.scriptSig[i] = InputScript.from_hex(script)
                    tx.scriptSig[i].type = t
                else:
                    # If input to be signed is orphan, the orphan InputScript is used when signing the transaction.
                    tx.scriptSig[i] = orphan
                tx.scriptSig_len[i] = len(tx.scriptSig[i].content) / 2
            elif tx.scriptSig[i].content != "":
                # All other scriptSig fields are emptied and their length is set to 0.
                tx.scriptSig[i] = InputScript()
                tx.scriptSig_len[i] = len(tx.scriptSig[i].content) / 2

        if hashflag is SIGHASH_SINGLE:
            # First we checks if the input that we are trying to sign has a corresponding output, if so, the execution
            # can continue. Otherwise, we abort the signature process since it could lead to a irreversible lose of
            # funds due to a bug in SIGHASH_SINGLE.
            # https://bitcointalk.org/index.php?topic=260595

            if index >= tx.outputs:
                raise Exception("You are trying to use SIGHASH_SINGLE to sign an input that does not have a "
                                "corresponding output (" + str(index) + "). This could lead to a irreversible lose "
                                "of funds. Signature process aborted.")
            # Otherwise, all outputs will set to empty scripts but the ith one (identified by index),
            # since SIGHASH_SINGLE should only sign the ith input with the ith output.
            else:
                # How to properly deal with SIGHASH_SINGLE signature format extracted from:
                # https://github.com/bitcoin/bitcoin/blob/3192e5278a/test/functional/test_framework/script.py#L869

                # First we backup the output that we will sign,
                t_script = tx.scriptPubKey[index]
                t_size = tx.scriptPubKey_len[index]
                t_value = tx.value[index]

                # Then, we delete every single output.
                tx.scriptPubKey = []
                tx.scriptPubKey_len = []
                tx.value = []
                for o in range(index):
                    # Once the all outputs have been deleted, we create empty outputs for every single index before
                    # the one that will be signed. Furthermore, the value of the output if set to maximum (2^64-1)
                    tx.scriptPubKey.append(OutputScript())
                    tx.scriptPubKey_len.append(len(tx.scriptPubKey[o].content) / 2)
                    tx.value.append(pow(2, 64) - 1)

                # Once we reach the index of the output that will be signed, we restore it with the one that we backed
                # up before.
                tx.scriptPubKey.append(t_script)
                tx.scriptPubKey_len.append(t_size)
                tx.value.append(t_value)

                # Finally, we recalculate the number of outputs for the signature format.
                # Notice that each signature format will have index number of outputs! Otherwise it will be invalid.
                tx.outputs = len(tx.scriptPubKey)

        elif hashflag is SIGHASH_NONE:
            # Empty all the scriptPubKeys and set the length and the output counter to 0.
            tx.outputs = 0
            tx.scriptPubKey = OutputScript()
            tx.scriptPubKey_len = len(tx.scriptPubKey.content) / 2

        elif hashflag is SIGHASH_ANYONECANPAY:
            # ToDo: Implement SIGHASH_ANYONECANPAY
            pass

        if hashflag in [SIGHASH_SINGLE, SIGHASH_NONE]:
            # All the nSequence from inputs except for the current one (index) is set to 0.
            # https://github.com/bitcoin/bitcoin/blob/3192e5278a/test/functional/test_framework/script.py#L880
            for i in range(tx.inputs):
                if i is not index:
                    tx.nSequence[i] = 0

        return tx

    def display(self):
        """ Displays all the information related to the transaction object, properly split and arranged.

        Data between parenthesis corresponds to the data encoded following the serialized transaction format.
        (replicates the same encoding being done in serialize method)

        :param self: self
        :type self: TX
        :return: None.
        :rtype: None
        """

        print "version: " + str(self.version) + " (" + change_endianness(int2bytes(self.version, 4)) + ")"
        print "number of inputs: " + str(self.inputs) + " (" + encode_varint(self.inputs) + ")"
        for i in range(self.inputs):
            print "input " + str(i)
            print "\t previous txid (little endian): " + self.prev_tx_id[i] + \
                  " (" + change_endianness(self.prev_tx_id[i]) + ")"
            print "\t previous tx output (little endian): " + str(self.prev_out_index[i]) + \
                  " (" + change_endianness(int2bytes(self.prev_out_index[i], 4)) + ")"
            print "\t input script (scriptSig) length: " + str(self.scriptSig_len[i]) \
                  + " (" + encode_varint((self.scriptSig_len[i])) + ")"
            print "\t input script (scriptSig): " + self.scriptSig[i].content
            print "\t decoded scriptSig: " + Script.deserialize(self.scriptSig[i].content)
            if self.scriptSig[i].type is "P2SH":
                print "\t \t decoded redeemScript: " + InputScript.deserialize(self.scriptSig[i].get_element(-1)[1:-1])
            print "\t nSequence: " + str(self.nSequence[i]) + " (" + int2bytes(self.nSequence[i], 4) + ")"
        print "number of outputs: " + str(self.outputs) + " (" + encode_varint(self.outputs) + ")"
        for i in range(self.outputs):
            print "output " + str(i)
            print "\t Satoshis to be spent (little endian): " + str(self.value[i]) + \
                  " (" + change_endianness(int2bytes(self.value[i], 8)) + ")"
            print "\t output script (scriptPubKey) length: " + str(self.scriptPubKey_len[i]) \
                  + " (" + encode_varint(self.scriptPubKey_len[i]) + ")"
            print "\t output script (scriptPubKey): " + self.scriptPubKey[i].content
            print "\t decoded scriptPubKey: " + Script.deserialize(self.scriptPubKey[i].content)

        print "nLockTime: " + str(self.nLockTime) + " (" + int2bytes(self.nLockTime, 4) + ")"
