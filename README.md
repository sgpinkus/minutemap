# (YEARLY) MINUTE MAP
The idea is you can specify a value (`int` by default) for any and every minute of an entire year. Which particular year isn't representable. Hierarchical specifiiers and priority matching rules are employed to determine the value for any given minute of the year. A specification takes the form of a set of `<expression, value>` pairs in JSON or as a dictionary.

An `expression` is a dot-separated sequence of time tokens. The wildcard "\*" may appear as a standalone spec or as a leaf segment, and means "everything else" not matched my siblings at this level.

The method `YearMinuteMap.get_value()` takes a `datetime`, and returns a value by selecting the most specific matching spec's value . Example:

```
my_minute_map =  {
  "*": 8,
  "h5-10": 28,
  "h19": {
    "*": 18,
    "m30-59": 22
  },
  "q2": {
    "h0-4": 10,
    "h5-10": 30,
    "h11-18": 10,
    "h19-23": 20,
  },
  "q3": {
    "h0-4": 12,
    "h5-10": 32,
    "h11-18": 12,
    "h19-23": 20,
    "sun": {
      "h0-4": 14,
      "h5-10": 34,
      "h11-18": 14,
      "h19-23": 23,
    }
  }
}
spec = YearMinuteMap(my_minute_map)
spec.get_value(my_date) # -> value
```

Input may be a flat or arbitrarily nested dict; nested dicts are flattened by joining their key paths with ".".  Both dict and JSON string are accepted. Flat Example:


```
  {
    "*": 1,
    "q1": 2,
    "q1.sun.h1-10.m1": 3
    "q1.sun.h1-10.m2": 4
  }
```

**EBNF for expression:**

```
SPEC      ::= "*" | PATH
PATH      ::=
  ( QTR | ( "." ( DOM_PATH | DOW_PATH | HH_PATH | MM ) )? )
  | ( MOY | ( "." ( DOM_PATH | DOW_PATH | HH_PATH | MM ) )? )
  | WOY ( "." ( DOW_PATH | HH_PATH | MM ) )?
  | DOY ( "." ( HH_PATH | MM ) )?
  | DOM_PATH
  | DOW_PATH
  | HH_PATH
  | MM
DOM_PATH  ::= DOM ( "." ( HH_PATH | MM ) )?
DOW_PATH  ::= DOW ( "." ( HH_PATH | MM ) )?
HH_PATH   ::= HH ( "." MM )?
QTR       ::= "q1" | "q2" | "q3" | "q4" // Quarter (maps to moy range internally)
MOY       ::= "moy" RANGE      // Month of year    1-12   (aliases: jan…dec)
WOY       ::= "woy" RANGE      // ISO week         1-53
DOY       ::= "doy" RANGE      // Day of year      1-366
DOM       ::= "dom" RANGE      // Day of month     1-31
DOW       ::= "dow" RANGE      // Day of week      1-7    (aliases: mon…sun, 1=Mon)
HH        ::= "h" RANGE        // Hour             0-23
MM        ::= "m" RANGE        // Minute           0-59
RANGE     ::= ( ( DIGITS | DIGITS "-" DIGITS ) | "*" ) ("/" DIGITS) | ( DIGITS (,DIGITS)+ )
```

The grammar does not allow use of the same type of token twice (ex "dom12.dom13") or certain chaining (ex "q1.apr").

MOY and DOW have aliases MONTH and WEEKDAY not shown in EBNF:

```
MONTH     ::= "jan" | "feb" | "mar" | "apr" | "may" | "jun" |
              "jul" | "aug" | "sep" | "oct" | "nov" | "dec"
WEEKDAY   ::= "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun"
```

**Tie breaking:**
Longer (more dots) paths beat shorter ones. The following order is used for tie breaks where path length is the same:

        QTR < MOY < DOW < DOM < WOY < DOY < HH < MM

Then specificity of the RANGE expression is used.

TODO: allow user to specify ordering by inputing a OrderDict or array.