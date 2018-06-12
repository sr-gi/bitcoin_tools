from bitcoin_tools.wallet import btc_addr_to_hash_160
from bitcoin_tools.utils import check_public_key, check_signature, check_address
from abc import ABCMeta, abstractmethod
from binascii import unhexlify, hexlify
from bitcoin.core.script import *


class Script:
    """ Defines the class Script which includes two subclasses, InputScript and OutputScript. Every script type have two
    custom 'constructors' (from_hex and from_human), and four templates for the most common standard script types
    (P2PK, P2PKH, P2MS and P2PSH).
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        self.content = ""
        self.type = "unknown"

    @classmethod
    def from_hex(cls, hex_script):
        """ Builds a script from a serialized one (it's hexadecimal representation).
        
        :param hex_script: Serialized script.
        :type hex_script: hex str
        :return: Script object with the serialized script as it's content.
        :rtype Script
        """
        script = cls()
        script.content = hex_script

        return script

    @classmethod
    def from_human(cls, data):
        """ Builds a script from a human way of writing them, using the Bitcoin Scripting language terminology.
        
        e.g: OP_DUP OP_HASH160 <hash_160> OP_EQUALVERIFY OP_CHECKSIG
        
        Every piece of data included in the script (everything except for op_codes) must be escaped between '<' '>'.
        
        :param data: Human readable Bitcoin Script (with data escaped between '<' '>')
        :type data: hex str
        :return: Script object with the serialization from the input script as it's content.
        :rtype. hex Script
        """

        script = cls()
        script.content = script.serialize(data)

        return script

    @staticmethod
    def deserialize(script):
        """ Deserializes a serialized script (goes from hex to human).
        
        e.g: deserialize('76a914b34bbaac4e9606c9a8a6a720acaf3018c9bc77c988ac') =   OP_DUP OP_HASH160 
            <b34bbaac4e9606c9a8a6a720acaf3018c9bc77c9> OP_EQUALVERIFY OP_CHECKSIG
            
        :param script: Serialized script to be deserialized.
        :type script: hex str
        :return: Deserialized script
        :rtype: hex str
        """

        start = "CScript(["
        end = "])"

        ps = CScript(unhexlify(script)).__repr__()
        ps = ps[ps.index(start) + len(start): ps.index(end)].split(", ")

        for i in range(len(ps)):
            if ps[i].startswith('x('):
                ps[i] = ps[i][3:-2]
                ps[i] = '<' + ps[i] + '>'

        return " ".join(ps)

    @staticmethod
    def serialize(data):
        """ Serializes a scrip from a deserialized one (human readable) (goes from human to hex)
        :param data: Human readable script.
        :type data: hex str
        :return: Serialized script.
        :rtype: hex str
        """

        hex_string = ""
        for e in data.split(" "):
            if e[0] == "<" and e[-1] == ">":
                hex_string += hexlify(CScriptOp.encode_op_pushdata(unhexlify(e[1:-1])))
            elif eval(e) in OPCODE_NAMES:
                hex_string += format(eval(e), '02x')
            else:
                raise Exception

        return hex_string

    def get_element(self, i):
        """
        Returns the ith element from the script. If -1 is passed as index, the last element is returned.
        :param i: The index of the selected element.
        :type i: int
        :return: The ith elements of the script.
        :rtype: str
        """

        return Script.deserialize(self.content).split()[i]


    @abstractmethod
    def P2PK(self):
        pass

    @abstractmethod
    def P2PKH(self):
        pass

    @abstractmethod
    def P2MS(self):
        pass

    @abstractmethod
    def P2SH(self):
        pass


class InputScript(Script):
    """ Defines an InputScript (ScriptSig) class that inherits from script.
    """

    @classmethod
    def P2PK(cls, signature):
        """ Pay-to-PubKey template 'constructor'. Builds a P2PK InputScript from a given signature.
        
        :param signature: Transaction signature.
        :type signature: hex str
        :return: A P2PK sScriptSig built using the given signature.
        :rtype: hex str
        """

        script = cls()
        if check_signature(signature):
            script.type = "P2PK"
            script.content = script.serialize("<" + signature + ">")

        return script

    @classmethod
    def P2PKH(cls, signature, pk):
        """ Pay-to-PubKeyHash template 'constructor'. Builds a P2PKH InputScript from a given signature and a
        public key.

        :param signature: Transaction signature.
        :type signature: hex str
        :param pk: Public key from the same key pair of the private key used to perform the signature.
        :type pk: hex str
        :return: A P2PKH ScriptSig built using the given signature and the public key.
        :rtype: hex str
        """

        script = cls()
        if check_signature(signature) and check_public_key(pk):
            script.type = "P2PKH"
            script.content = script.serialize("<" + signature + "> <" + pk + ">")

        return script

    @classmethod
    def P2MS(cls, sigs):
        """ Pay-to-Multisig template 'constructor'. Builds a P2MS InputScript from a given list of signatures.

        :param sigs: List of transaction signatures.
        :type sigs: list
        :return: A P2MS ScriptSig built using the given signatures list.
        :rtype: hex str
        """

        script = cls()
        s = "OP_0"
        for sig in sigs:
            if check_signature(sig):
                s += " <" + sig + ">"

        script.type = "P2MS"
        script.content = script.serialize(s)

        return script

    @classmethod
    def P2SH(cls, data, s):
        """ Pay-to-ScriptHash template 'constructor'. Builds a P2SH InputScript from a given script.

        :param data: Input data that will be evaluated with the script content once its hash had been checked against
        the hash provided by the OutputScript.
        :type data: list
        :param s: Human readable script that hashes to the UTXO script hash that the transaction tries to redeem.
        :type s: hex str
        :return: A P2SH ScriptSig (RedeemScript) built using the given script.
        :rtype: hex str
        """

        script = cls()
        for d in data:
            if isinstance(d, str) and d.startswith("OP"):
                # If an OP_CODE is passed as data (such as OP_0 in multisig transactions), the element is encoded as is.
                script.content += d + " "
            else:
                # Otherwise, the element is encoded as data.
                script.content += "<" + str(d) + "> "
        script.type = "P2SH"
        script.content = script.serialize(script.content + "<" + script.serialize(s) + ">")

        return script


class OutputScript(Script):
    """ Defines an OutputScript (ScriptPubKey) class that inherits from script.
    """

    @classmethod
    def P2PK(cls, pk):
        """ Pay-to-PubKey template 'constructor'. Builds a P2PK OutputScript from a given public key.

        :param pk: Public key to which the transaction output will be locked to.
        :type pk: hex str
        :return: A P2PK ScriptPubKey built using the given public key.
        :rtype: hex str
        """

        script = cls()
        if check_public_key(pk):
            script.type = "P2PK"
            script.content = script.serialize("<"+pk+"> OP_CHECKSIG")

        return script

    @classmethod
    def P2PKH(cls, data, network='test', hash160=False):
        """ Pay-to-PubKeyHash template 'constructor'. Builds a P2PKH OutputScript from a given Bitcoin address / hash160
        of a Bitcoin address and network.

        :param data: Bitcoin address or hash160 of a Bitcoin address to which the transaction output will be locked to.
        :type data: hex str
        :param network: Bitcoin network (either mainnet or testnet)
        :type network: hex str
        :param hash160: If set, the given data is the hash160 of a Bitcoin address, otherwise, it is a Bitcoin address.
        :type hash160: bool
        :return: A P2PKH ScriptPubKey built using the given bitcoin address and network.
        :rtype: hex str
        """

        if network in ['testnet', 'test', 'mainnet', 'main']:
            script = cls()
            if not hash160 and check_address(data, network):
                h160 = btc_addr_to_hash_160(data)
            else:
                h160 = data
            script.type = "P2PKH"
            script.content = script.serialize("OP_DUP OP_HASH160 <" + h160 + "> OP_EQUALVERIFY OP_CHECKSIG")

            return script
        else:
            raise Exception("Unknown Bitcoin network.")

    @classmethod
    def P2MS(cls, m, n, pks):
        """ Pay-to-Multisig template 'constructor'. Builds a P2MS OutputScript from a given list of public keys, the total
        number of keys and a threshold.

        :param m: Threshold, minimum amount of signatures needed to redeem from the output.
        :type m: int
        :param n: Total number of provided public keys.
        :type n: int
        :param pks: List of n public keys from which the m-of-n multisig output will be created.
        :type pks: list
        :return: A m-of-n Pay-to-Multisig script created using the provided public keys.
        :rtype: hex str
        """

        script = cls()
        if n != len(pks):
            raise Exception("The provided number of keys does not match the expected one: " + str(len(pks)) +
                            "!=" + str(n))
        elif m not in range(1, 15) or n not in range(1, 15):
            raise Exception("Multisig transactions must be 15-15 at max")
        else:
            s = "OP_" + str(m)
            for pk in pks:
                if check_public_key(pk):
                    s += " <" + pk + ">"

        script.type = "P2MS"
        script.content = script.serialize(s + " OP_" + str(n) + " OP_CHECKMULTISIG")

        return script

    @classmethod
    def P2SH(cls, script_hash):
        """ Pay-to-ScriptHash template 'constructor'. Builds a P2SH OutputScript from a given script hash.

        :param script_hash: Script hash to which the output will be locked to.
        :type script_hash: hex str
        :return: A P2SH ScriptPubKey built using the given script hash.
        :rtype: hex str
        """

        script = cls()
        l = len(script_hash)
        if l != 40:
            raise Exception("Wrong RIPEMD-160 hash length: " + str(l))
        else:
            script.type = "P2SH"
            script.content = script.serialize("OP_HASH160 <" + script_hash + "> OP_EQUAL")

        return script
