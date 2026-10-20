import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from addr2repo.keccakutil import keccak256_hex, selector
from addr2repo.proxy import (
    ADMIN_SLOT_1967,
    ADMIN_SLOT_ZOS,
    BEACON_SLOT_1967,
    EIP1167_PREFIX,
    EIP1167_SUFFIX,
    IMPL_SLOT_1822,
    IMPL_SLOT_1967,
    IMPL_SLOT_ZOS,
    parse_eip1167_bytecode,
    word_to_address,
)


class TestKeccak(unittest.TestCase):
    def test_known_selectors(self):
        self.assertEqual(selector("implementation()"), "5c60da1b")
        self.assertEqual(selector("transfer(address,uint256)"), "a9059cbb")

    def test_eip1967_slots(self):
        self.assertEqual(IMPL_SLOT_1967, "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc")
        self.assertEqual(BEACON_SLOT_1967, "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50")
        self.assertEqual(ADMIN_SLOT_1967, "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103")
        self.assertEqual(IMPL_SLOT_1822, "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7")

    def test_zos_slots(self):
        self.assertEqual(IMPL_SLOT_ZOS, "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3")
        self.assertEqual(ADMIN_SLOT_ZOS, "0x10d6a54a4754c8869d6886b5f5d7fbfa5b4522237ea5c60d11bc4e7a1ff9390b")

    def test_keccak256_hex_empty(self):
        self.assertEqual(
            keccak256_hex(b""),
            "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470",
        )


class TestWordToAddress(unittest.TestCase):
    def test_padded(self):
        word = "0x" + "0" * 24 + "a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
        self.assertEqual(word_to_address(word), "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")

    def test_zero(self):
        self.assertIsNone(word_to_address("0x" + "0" * 64))

    def test_empty(self):
        self.assertIsNone(word_to_address("0x"))
        self.assertIsNone(word_to_address(""))


class TestEip1167(unittest.TestCase):
    def test_valid_clone(self):
        impl = "10ed43c718714eb63d5aa57b78b54704e256024e"
        code = "0x" + EIP1167_PREFIX + impl + EIP1167_SUFFIX
        self.assertEqual(parse_eip1167_bytecode(code), "0x" + impl)

    def test_not_a_clone(self):
        self.assertIsNone(parse_eip1167_bytecode("0x6080604052"))
        self.assertIsNone(parse_eip1167_bytecode("0x"))

    def test_truncated(self):
        impl = "10ed43c718714eb63d5aa57b78b54704e256024e"
        code = "0x" + EIP1167_PREFIX + impl + "5af4"
        self.assertIsNone(parse_eip1167_bytecode(code))


if __name__ == "__main__":
    unittest.main()
