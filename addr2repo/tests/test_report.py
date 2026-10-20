import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from addr2repo.models import AddressResult, FetchedContract, ProxyInfo
from addr2repo.report import group_by_implementation, render_csv, render_json, render_markdown, render_text


def make_result(addr, impl, conf="IDENTICAL", repo="contracts/Pool.sol", kind="eip1967", name="Pool"):
    r = AddressResult(address=addr, chain=1, chain_name="ethereum")
    r.target_address = impl
    r.proxy = ProxyInfo(kind=kind, implementation=impl)
    r.fetch = FetchedContract(address=impl, name=name, compiler="0.8.20", explorer="sourcify", sources=[])
    r.primary_repo_path = repo
    r.primary_confidence = conf
    return r


class TestReport(unittest.TestCase):
    def test_grouping_collapses_proxies(self):
        a = make_result("0x" + "aa" * 20, "0x" + "11" * 20)
        b = make_result("0x" + "bb" * 20, "0x" + "11" * 20)
        c = make_result("0x" + "cc" * 20, "0x" + "22" * 20)
        groups = group_by_implementation([a, b, c])
        self.assertEqual(len(groups), 2)
        impl1, members1 = groups[0]
        self.assertEqual(impl1, "0x" + "11" * 20)
        self.assertEqual(len(members1), 2)

    def test_formats_smoke(self):
        a = make_result("0x" + "aa" * 20, "0x" + "11" * 20)
        groups = group_by_implementation([a])
        self.assertIn("implementation group", render_text([a], groups))
        self.assertIn("| address |", render_markdown([a], groups))
        csv_out = render_csv([a], groups)
        self.assertIn("repo_path", csv_out.splitlines()[0])
        json_out = render_json([a], groups)
        self.assertIn('"implementation"', json_out)

    def test_unverified_address_renders(self):
        r = AddressResult(address="0x" + "dd" * 20, chain=1, chain_name="ethereum")
        r.primary_confidence = "UNVERIFIED"
        r.errors.append("no verified source found")
        groups = group_by_implementation([r])
        out = render_text([r], groups)
        self.assertIn("NOT VERIFIED", out)
        self.assertIn("UNVERIFIED", out)


if __name__ == "__main__":
    unittest.main()
