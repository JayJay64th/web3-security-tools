import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from addr2repo.sources import (
    abi_function_names,
    extract_contract_names,
    extract_function_names,
    normalize_hash,
    normalize_source,
    parse_abi,
    parse_standard_json,
)

SINGLE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
/// docs
contract Foo {
    function bar(uint256 x) external returns (uint256) { return x; }
    /* block
       comment */
    function baz() external view returns (address) { return address(0); }
}
"""

SINGLE_WITH_DIFFERENT_COMMENTS = """
pragma solidity ^0.8.0;
contract Foo {
    function bar(uint256 x) external returns (uint256) { return x; }
    function baz() external view returns (address) { return address(0); }
}
"""


class TestNormalize(unittest.TestCase):
    def test_comments_do_not_change_hash(self):
        self.assertEqual(normalize_hash(SINGLE), normalize_hash(SINGLE_WITH_DIFFERENT_COMMENTS))

    def test_whitespace_collapse(self):
        a = "contract  Foo  {  function bar()  }"
        b = "contract Foo { function bar() }"
        self.assertEqual(normalize_source(a), normalize_source(b))

    def test_different_code_different_hash(self):
        c = SINGLE.replace("return x", "return x + 1")
        self.assertNotEqual(normalize_hash(SINGLE), normalize_hash(c))


class TestStandardJson(unittest.TestCase):
    def test_double_wrapped(self):
        inner = {
            "sources": {
                "contracts/Foo.sol": {"content": SINGLE},
                "contracts/Bar.sol": {"content": SINGLE},
            }
        }
        wrapped = "{" + json.dumps(inner) + "}"
        out = parse_standard_json(wrapped)
        self.assertEqual(set(out), {"contracts/Foo.sol", "contracts/Bar.sol"})
        self.assertIn("contract Foo", out["contracts/Foo.sol"])

    def test_plain_json(self):
        inner = {"sources": {"A.sol": {"content": "contract A {}"}}}
        out = parse_standard_json(json.dumps(inner))
        self.assertEqual(out, {"A.sol": "contract A {}"})

    def test_single_file_passthrough(self):
        self.assertIsNone(parse_standard_json(SINGLE))

    def test_garbage(self):
        self.assertIsNone(parse_standard_json("not json"))


class TestExtractors(unittest.TestCase):
    def test_contract_names(self):
        names = extract_contract_names(SINGLE)
        self.assertIn("Foo", names)

    def test_function_names(self):
        fns = extract_function_names(SINGLE)
        self.assertEqual(fns, {"bar", "baz"})

    def test_abi_function_names(self):
        abi = [
            {"type": "function", "name": "transfer", "inputs": []},
            {"type": "event", "name": "Transfer"},
            {"type": "constructor", "inputs": []},
        ]
        self.assertEqual(abi_function_names(abi), {"transfer"})

    def test_parse_abi_string(self):
        self.assertEqual(parse_abi('[{"type":"function","name":"x"}]'), [{"type": "function", "name": "x"}])
        self.assertIsNone(parse_abi("Contract source code not verified"))
        self.assertIsNone(parse_abi(None))


if __name__ == "__main__":
    unittest.main()
