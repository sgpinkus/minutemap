"""Tests for parse_range — range, step, and list syntax."""

from __future__ import annotations

import sys
from os.path import dirname, realpath

sys.path.append(dirname(realpath(__file__ + "/../../")))
sys.path.append(dirname(realpath(__file__ + "/../")))

import unittest
from minutemap.main import (
    parse_range,
    RangeToken,
    LstToken,
    ParseError,
    NormalTokenKey,
    Token,
)


ValidCase = tuple[NormalTokenKey, str, Token, str]
InvalidCase = tuple[NormalTokenKey, str, str, str]


class TestParseRange(unittest.TestCase):
    def test_valid(self) -> None:
        cases: list[ValidCase] = [
            # (kind, text, expected_token, description)
            # Simple single value
            ("m", "30", RangeToken("m", 30, 30), "single minute value"),
            ("h", "9", RangeToken("h", 9, 9), "single hour value"),
            ("moy", "6", RangeToken("moy", 6, 6), "single month value"),
            # Range
            ("m", "0-29", RangeToken("m", 0, 29), "minute range"),
            ("h", "9-17", RangeToken("h", 9, 17), "hour range"),
            ("moy", "1-3", RangeToken("moy", 1, 3), "month range"),
            ("dow", "1-5", RangeToken("dow", 1, 5), "weekday range"),
            # Step
            ("m", "0-59/15", RangeToken("m", 0, 59, 15), "every 15 minutes"),
            ("m", "0-30/10", RangeToken("m", 0, 30, 10), "every 10 minutes up to 30"),
            ("h", "0-23/6", RangeToken("h", 0, 23, 6), "every 6 hours"),
            ("h", "6-18/3", RangeToken("h", 6, 18, 3), "every 3 hours 6-18"),
            # List
            ("m", "0,15,30,45", LstToken("m", [0, 15, 30, 45]), "minute list"),
            ("h", "6,12,18", LstToken("h", [6, 12, 18]), "hour list"),
            ("dow", "1,3,5", LstToken("dow", [1, 3, 5]), "weekday list"),
            (
                "moy",
                "3,6,9,12",
                LstToken("moy", [3, 6, 9, 12]),
                "quarterly months list",
            ),
        ]

        for kind, text, expected, description in cases:
            with self.subTest(description):
                result = parse_range(kind, text)
                self.assertEqual(result, expected, description)

    def test_invalid(self) -> None:
        cases: list[InvalidCase] = [
            # (kind, text, expected_error_fragment, description)
            ("h", "25", "out of bounds", "hour too high"),
            ("m", "60", "out of bounds", "minute too high"),
            ("moy", "13", "out of bounds", "month too high"),
            ("dow", "0", "out of bounds", "dow too low"),
            ("doy", "367", "out of bounds", "doy too high"),
            ("m", "30-10", "lo > hi", "range lo > hi"),
            ("h", "0-23/0", "step", "step of zero"),
            ("m", "abc", "invalid", "non-numeric"),
            ("h", "", "invalid", "empty string"),
            ("m", "0-70/5", "out of bounds", "range hi out of bounds with step"),
        ]

        for kind, text, fragment, description in cases:
            with self.subTest(description):
                with self.assertRaises(ParseError, msg=description) as ctx:
                    parse_range(kind, text)
                self.assertIn(fragment, str(ctx.exception).lower(), description)


if __name__ == "__main__":
    unittest.main(verbosity=2)
