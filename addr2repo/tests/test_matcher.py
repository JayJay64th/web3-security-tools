import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from addr2repo.matcher import match_contract
from addr2repo.models import DeployedSource, FetchedContract, RepoFile
from addr2repo.sources import extract_contract_names, extract_function_names, normalize_hash

POOL_SRC = """
pragma solidity ^0.8.0;
contract Pool {
    function deposit(uint256 a) external {}
    function withdraw(uint256 a) external {}
    function borrow(uint256 a) external {}
    function repay(uint256 a) external {}
}
"""

OLD_POOL_SRC = """
pragma solidity ^0.8.0;
contract Pool {
    function deposit(uint256 a) external {}
    function withdraw(uint256 a) external {}
    function borrow(uint256 a) external {}
}
"""

OTHER_SRC = """
pragma solidity ^0.8.0;
contract Vault {
    function mint(uint256 a) external {}
}
"""


def repo_file(path, content):
    return RepoFile(
        path=path,
        normalized_hash=normalize_hash(content),
        contract_names=extract_contract_names(content),
        function_names=extract_function_names(content),
    )


class TestMatcher(unittest.TestCase):
    def setUp(self):
        self.repo = [
            repo_file("contracts/Pool.sol", POOL_SRC),
            repo_file("contracts/Vault.sol", OTHER_SRC),
            repo_file("contracts/vendor/OldPool.sol", OLD_POOL_SRC),
        ]

    def _fetch(self, content, name="Pool", abi=None):
        return FetchedContract(
            address="0x" + "11" * 20,
            name=name,
            compiler="0.8.20",
            explorer="test",
            sources=[DeployedSource("contracts/Pool.sol", content)],
            abi=abi,
        )

    def test_identical(self):
        matches, confidence, path = match_contract(self._fetch(POOL_SRC), self.repo)
        self.assertEqual(confidence, "IDENTICAL")
        self.assertEqual(path, "contracts/Pool.sol")
        self.assertEqual(matches[0].confidence, "IDENTICAL")

    def test_selector_match_drift(self):
        drifted = POOL_SRC.replace("function repay", "function repay2")
        matches, confidence, path = match_contract(self._fetch(drifted), self.repo)
        self.assertEqual(confidence, "SELECTOR_MATCH")
        self.assertEqual(path, "contracts/Pool.sol")
        self.assertGreater(matches[0].overlap, 0.5)

    def test_partial_selector_still_matches(self):
        drifted = POOL_SRC.replace("function withdraw", "function withdrawX").replace(
            "function borrow", "function borrowX"
        )
        matches, confidence, path = match_contract(self._fetch(drifted), self.repo)
        self.assertEqual(path, "contracts/Pool.sol")
        self.assertEqual(confidence, "SELECTOR_MATCH")

    def test_name_only_candidate(self):
        alien = """
pragma solidity ^0.8.0;
contract Pool {
    function alpha() external {}
    function beta() external {}
    function gamma() external {}
}
"""
        matches, confidence, path = match_contract(self._fetch(alien), self.repo)
        self.assertEqual(path, "contracts/Pool.sol")
        self.assertEqual(confidence, "NAME_CANDIDATE")

    def test_no_sources(self):
        fetch = FetchedContract("0x" + "11" * 20, "Pool", "x", "test", sources=[])
        matches, confidence, path = match_contract(fetch, self.repo)
        self.assertEqual(confidence, "NONE")
        self.assertIsNone(path)

    def test_prefers_canonical_path_over_vendor(self):
        matches, confidence, path = match_contract(self._fetch(POOL_SRC), self.repo)
        self.assertEqual(path, "contracts/Pool.sol")


if __name__ == "__main__":
    unittest.main()
