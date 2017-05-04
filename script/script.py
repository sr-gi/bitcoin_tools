from abc import ABCMeta, abstractmethod
from wallet.wallet import btc_address_to_hash_160
from bitcoin.core.script import *
from binascii import a2b_hex, b2a_hex
from utils.utils import check_public_key, check_signature, check_address


class Script:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.content = ""
        self.type = "unknown"

    def from_hex(self, script):
        self.__init__()
        self.content = script

    def from_human(self, data):
        self.__init__()
        self.content = self.serialize(data)

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
    def P2PK(self, signature):
        if check_signature(signature):
            self.type = "P2PK"
            self.content = self.serialize("<" + signature + ">")

    def P2PKH(self, signature, pk):
        if check_signature(signature) and check_public_key(pk):
            self.type = "P2PKH"
            self.content = self.serialize("<" + signature + "> <" + pk + ">")

    def P2MS(self, sigs):
        script = "OP_0"
        for sig in sigs:
            if check_signature(sig):
                script += " <" + sig + ">"

        self.type = "P2MS"
        self.content = self.serialize(script)

    def P2SH(self, script):
        # ToDo: Should we run any validation?
        self.type = "P2SH"
        self.content = self.serialize("<" + self.serialize(script) + ">")


class OutputScript(Script):
    def P2PK(self, pk):
        if check_public_key(pk):
            self.type = "P2PK"
            self.content = self.serialize("<"+pk+"> OP_CHECKSIG")

    def P2PKH(self, btc_addr, network='test'):
        if check_address(btc_addr, network):
            self.type = "P2PKH"
            self.content = self.serialize("OP_DUP OP_HASH160 <" + btc_address_to_hash_160(btc_addr)
                                          + "> OP_EQUALVERIFY OP_CHECKSIG")

    def P2MS(self, m, n, pks):
        if n != len(pks):
            raise Exception("The provided number of keys does not match the expected one: " + str(len(pks)) +
                            "!=" + str(n))
        else:
            script = "OP_" + str(m)
            for pk in pks:
                if check_public_key(pk):
                    script += " <" + pk + ">"

        self.type = "P2MS"
        self.content = self.serialize(script + " OP_" + str(n) + " OP_CHECKMULTISIG")

    def P2SH(self, script_hash):
        l = len(script_hash)
        if l != 40:
            raise Exception("Wrong RIPEMD-160 hash length: " + str(l))
        else:
            self.type = "P2SH"
            self.content = self.serialize("OP_HASH160 <" + script_hash + "> OP_EQUAL")
