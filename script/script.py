from abc import ABCMeta, abstractmethod
from wallet.wallet import btc_addr_to_hash_160
from bitcoin.core.script import *
from binascii import a2b_hex, b2a_hex
from utils.utils import check_public_key, check_signature, check_address


class Script:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.content = ""
        self.type = "unknown"

    @classmethod
    def from_hex(cls, hex):
        script = cls()
        script.content = hex

        return script

    @classmethod
    def from_human(cls, data):
        script = cls()
        script.content = script.serialize(data)

        return script

    @staticmethod
    def deserialize(script):
        start = "CScript(["
        end = "])"

        ps = CScript(a2b_hex(script)).__repr__()
        ps = ps[ps.index(start) + len(start): ps.index(end)].split(", ")

        for i in range(len(ps)):
            if ps[i].startswith('x('):
                ps[i] = ps[i][3:-2]
                ps[i] = '<' + ps[i] + '>'

        return " ".join(ps)

    @staticmethod
    def serialize(data):
        hex_string = ""
        for e in data.split(" "):
            if e[0] == "<" and e[-1] == ">":
                hex_string += b2a_hex(CScriptOp.encode_op_pushdata(a2b_hex(e[1:-1])))
            elif eval(e) in OPCODE_NAMES:
                hex_string += format(eval(e), '02x')
            else:
                raise Exception

        return hex_string

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

    @classmethod
    def P2PK(cls, signature):
        script = cls()
        if check_signature(signature):
            script.type = "P2PK"
            script.content = script.serialize("<" + signature + ">")

        return script

    @classmethod
    def P2PKH(cls, signature, pk):
        script = cls()
        if check_signature(signature) and check_public_key(pk):
            script.type = "P2PKH"
            script.content = script.serialize("<" + signature + "> <" + pk + ">")

        return script

    @classmethod
    def P2MS(cls, sigs):
        script = cls()
        s = "OP_0"
        for sig in sigs:
            if check_signature(sig):
                s += " <" + sig + ">"

        script.type = "P2MS"
        script.content = script.serialize(s)

        return script

    @classmethod
    def P2SH(cls, s):
        script = cls()
        # ToDo: Should we run any validation?
        script.type = "P2SH"
        script.content = script.serialize("<" + script.serialize(s) + ">")

        return script


class OutputScript(Script):
    @classmethod
    def P2PK(cls, pk):
        script = cls()
        if check_public_key(pk):
            script.type = "P2PK"
            script.content = script.serialize("<"+pk+"> OP_CHECKSIG")

        return script

    @classmethod
    def P2PKH(cls, btc_addr, network='test'):
        script = cls()
        if check_address(btc_addr, network):
            script.type = "P2PKH"
            script.content = script.serialize("OP_DUP OP_HASH160 <" + btc_addr_to_hash_160(btc_addr)
                                              + "> OP_EQUALVERIFY OP_CHECKSIG")

        return script

    @classmethod
    def P2MS(cls, m, n, pks):
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
        script = cls()
        l = len(script_hash)
        if l != 40:
            raise Exception("Wrong RIPEMD-160 hash length: " + str(l))
        else:
            script.type = "P2SH"
            script.content = script.serialize("OP_HASH160 <" + script_hash + "> OP_EQUAL")

        return script