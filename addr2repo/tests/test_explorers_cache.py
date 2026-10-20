import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from addr2repo.cache import Cache
from addr2repo.explorers import _parse_etherscan_like


class TestCache(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_roundtrip(self):
        c = Cache(self.dir, enabled=True)
        c.set("fetch:ethereum:1:0xabc", {"name": "Pool"})
        self.assertEqual(c.get("fetch:ethereum:1:0xabc"), {"name": "Pool"})

    def test_disabled(self):
        c = Cache(self.dir, enabled=False)
        c.set("k", {"a": 1})
        self.assertIsNone(c.get("k"))

    def test_missing(self):
        c = Cache(self.dir, enabled=True)
        self.assertIsNone(c.get("nope"))

    def test_path_sanitized(self):
        path = Cache._path(self.dir, "fetch:ethereum:1:0xabc:sourcify")
        self.assertTrue(os.path.exists(os.path.dirname(path)))
        self.assertNotIn(":", os.path.basename(path))


class TestEtherscanParse(unittest.TestCase):
    ADDR = "0x" + "11" * 20

    def test_verified_multifile(self):
        inner = {"sources": {"contracts/Pool.sol": {"content": "contract Pool {}"}}}
        import json as _json

        payload = {
            "status": "1",
            "result": [
                {
                    "SourceCode": "{" + _json.dumps(inner) + "}",
                    "ContractName": "Pool",
                    "CompilerVersion": "v0.8.20+commit.a1b79de6",
                    "ABI": '[{"type":"function","name":"deposit"}]',
                    "Proxy": "0",
                    "Implementation": "",
                }
            ],
        }
        fetch = _parse_etherscan_like(payload, self.ADDR, "etherscan")
        self.assertTrue(fetch.verified)
        self.assertEqual(fetch.name, "Pool")
        self.assertEqual(len(fetch.sources), 1)
        self.assertEqual(fetch.abi[0]["name"], "deposit")

    def test_unverified_with_impl_hint(self):
        payload = {
            "status": "1",
            "result": [
                {
                    "SourceCode": "",
                    "ContractName": "",
                    "CompilerVersion": "",
                    "ABI": "Contract source code not verified",
                    "Proxy": "1",
                    "Implementation": "0x" + "22" * 20,
                }
            ],
        }
        fetch = _parse_etherscan_like(payload, self.ADDR, "etherscan")
        self.assertFalse(fetch.verified)
        self.assertEqual(fetch.proxy_hint_implementation, "0x" + "22" * 20)

    def test_not_found(self):
        payload = {"status": "0", "result": "No records found"}
        self.assertIsNone(_parse_etherscan_like(payload, self.ADDR, "etherscan"))


if __name__ == "__main__":
    unittest.main()
