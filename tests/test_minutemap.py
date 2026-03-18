"""
Unit tests for YearMinuteMap.
"""
import sys
from os.path import dirname, realpath
sys.path.append(dirname(realpath(__file__ + '/../../')))
sys.path.append(dirname(realpath(__file__ + '/../')))

import unittest
from datetime import datetime
from minutemap import YearMinuteMap


class TestYearMinuteMap(unittest.TestCase):

    def test_valid(self):
        cases = [
            # (spec, datetime, expected_value, description)

            # Wildcard fallback
            ({"*": 7}, datetime(2024, 7, 4, 14, 0), 7, "bare wildcard"),

            # Leaf wildcard is a no-op
            ({"h19.*": 18}, datetime(2024, 1, 1, 19, 0), 18, "leaf wildcard stripped"),

            # More specific spec wins over wildcard
            ({"*": 1, "q1": 2}, datetime(2024, 2, 1, 0, 0), 2, "q1 beats wildcard"),

            # Quarter aliases
            ({"q2": 10}, datetime(2024, 4, 1, 0, 0), 10, "q2 matches April"),
            ({"q2": 10}, datetime(2024, 6, 30, 23, 59), 10, "q2 matches June"),
            ({"q2": 10}, datetime(2024, 7, 1, 0, 0), None, "q2 does not match July"),

            # Month aliases
            ({"apr": 30}, datetime(2024, 4, 10, 0, 0), 30, "apr alias"),
            ({"dec": 12}, datetime(2024, 12, 25, 0, 0), 12, "dec alias"),

            # DOW aliases
            ({"mon": 1}, datetime(2024, 1, 1, 0, 0), 1, "mon alias (2024-01-01 is Monday)"),
            ({"sun": 7}, datetime(2024, 1, 7, 0, 0), 7, "sun alias (2024-01-07 is Sunday)"),

            # Ranges
            ({"moy1-3": 55}, datetime(2024, 2, 15, 0, 0), 55, "moy range matches February"),
            ({"moy1-3": 55}, datetime(2024, 4, 1, 0, 0), None, "moy range does not match April"),
            ({"dow1-5": 10}, datetime(2024, 1, 1, 0, 0), 10, "dow1-5 matches Monday"),
            ({"dow6-7": 20}, datetime(2024, 1, 6, 0, 0), 20, "dow6-7 matches Saturday"),
            ({"h9-17": 5}, datetime(2024, 3, 1, 12, 0), 5, "h9-17 matches noon"),
            ({"h9-17": 5}, datetime(2024, 3, 1, 18, 0), None, "h9-17 does not match 18:00"),

            # Depth wins over breadth
            ({"q1": 1, "q1.h9": 2}, datetime(2024, 1, 15, 9, 0), 2, "deeper path wins"),
            ({"q1": 1, "q1.h9": 2}, datetime(2024, 1, 15, 10, 0), 1, "shallower path fallback"),

            # Nested dict input
            ({"h19": {"*": 18, "m30-59": 22}}, datetime(2024, 6, 1, 19, 0), 18, "nested: h19.*"),
            ({"h19": {"*": 18, "m30-59": 22}}, datetime(2024, 6, 1, 19, 45), 22, "nested: h19.m30-59"),

            # No match returns None
            ({"q1": 1}, datetime(2024, 7, 4, 0, 0), None, "no match returns None"),

            # Specificity
            ({"*": 1, "q1": 2, "q1.dow7": 3, "q1.dow7.h9": 4, "q1.dow7.h9.m30": 5},
            datetime(2024, 1, 7, 9, 30), 5, "specificity: full path wins over all shallower"),
            ({"q1": 1, "jan": 2},
            datetime(2024, 1, 15, 0, 0), 2, "specificity: MOY beats QTR at depth 1"),
            ({"q1.dow1": 1, "q1.dom1": 2},
            datetime(2024, 1, 1, 0, 0), 2, "specificity: DOM beats DOW at depth 2 (2024-01-01 is Monday)"),
            ({"woy1": 1, "doy1": 2},
            datetime(2024, 1, 1, 0, 0), 2, "specificity: DOY beats WOY at depth 1"),
            ({"h9": {"*": 1, "m0": 2}},
            datetime(2024, 6, 1, 9, 1), 1, "specificity: h9.* loses to h9.m0 for non-matching minute"),
        ]
        for spec, dt, expected, description in cases:
            with self.subTest(description):
                ymm = YearMinuteMap(spec)
                self.assertEqual(ymm.get_value(dt), expected, description)

    def test_invalid(self):
        cases = [
            # (spec_dict, expected_error_fragment, description)
            ({"*": 7.7},          "expected int",    "not an int"),
            ({"h25": 1},          "out of bounds",   "hour out of range"),
            ({"m60": 1},          "out of bounds",   "minute out of range"),
            ({"moy13": 1},        "out of bounds",   "month out of range"),
            ({"dom32": 1},        "out of bounds",   "day of month out of range"),
            ({"dow8": 1},         "out of bounds",   "day of week out of range"),
            ({"doy367": 1},       "out of bounds",   "day of year out of range"),
            ({"woy54": 1},        "out of bounds",   "week of year out of range"),
            ({"moy6-3": 1},       "lo > hi",         "range lo > hi"),
            ({"moy2.woy5": 1},    "cannot follow",   "woy cannot follow moy"),
            ({"moy1.h5.dom3": 1}, "cannot follow",   "dom cannot follow h"),
            ({"h9.moy3": 1},      "cannot follow",   "moy cannot follow h"),
            ({"doy100.woy5": 1},  "cannot follow",   "woy cannot follow doy"),
            ({"*": "eight"},      "int",             "non-integer value"),
            ({"*": 3.14},         "int",             "float value"),
        ]
        for spec, fragment, description in cases:
            with self.subTest(description):
                with self.assertRaises(ValueError) as ctx:
                    YearMinuteMap(spec)
                self.assertIn(fragment, str(ctx.exception).lower(), description)

    def test_valid_float_value(self):
        cases = [({"*": 7.7}, datetime(2024, 7, 4, 14, 0), 7.7, "bare wildcard"),
        ]
        for spec, dt, expected, description in cases:
            with self.subTest(description):
                ymm = YearMinuteMap(spec, float)
                self.assertEqual(ymm.get_value(dt), expected, description)

    def test_invalid_float_value(self):
        cases = [({"*": 7},          "expected float",    "not a float"),
        ]
        for spec, fragment, description in cases:
            with self.subTest(description):
                with self.assertRaises(ValueError) as ctx:
                    YearMinuteMap(spec, float)
                self.assertIn(fragment, str(ctx.exception).lower(), description),


if __name__ == "__main__":
    unittest.main(verbosity=2)