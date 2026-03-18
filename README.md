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
  ( QTR | ( "." ( _DOM | _DOW | _HH | MM ) )? )
  | ( MOY | ( "." ( _DOM | _DOW | _HH | MM ) )? )
  | WOY ( "." ( _DOW | _HH | MM ) )?
  | DOY ( "." ( _HH | MM ) )?
  | _DOM
  | _DOW
  | _HH
  | MM
_DOM        = DOM ( "." ( _HH | MM ) )?
_DOW        = DOW ( "." ( _HH | MM ) )?
_HH         = HH ( "." MM )?
QTR       ::= "q1" | "q2" | "q3" | "q4"
MOY       ::= "moy" RANGE      // 1-12
WOY       ::= "woy" RANGE      // 1–53 (ISO weeks can be 53)
DOY       ::= "doy" RANGE      // 1–366
DOM       ::= "dom" RANGE      // 1–31
DOW       ::= "dow" RANGE      // 1-7
HH        ::= "h" RANGE        // 0–23
MM        ::= "m" RANGE        // 0–59
RANGE     ::= DIGITS | DIGITS "-" DIGITS
```

The grammar does not allow use of the same type of token twice (ex "dom12.dom13") or certain chaining (ex "q1.apr").

MOY and DOW have aliases MONTH and WEEKDAY not shown in EBNF:

```
MONTH     ::= "jan" | "feb" | "mar" | "apr" | "may" | "jun" |
              "jul" | "aug" | "sep" | "oct" | "nov" | "dec"
WEEKDAY   ::= "mon" | "tue" | "wed" | "thu" | "fri" | "sat" | "sun"
```

**Token reference:**

        q1..q4          Quarter (maps to moy range internally)
        moy<range>      Month of year    1-12   (aliases: jan…dec)
        woy<range>      ISO week         1-53
        doy<range>      Day of year      1-366
        dom<range>      Day of month     1-31
        dow<range>      Day of week      1-7    (aliases: mon…sun, 1=Mon)
        h<range>        Hour             0-23
        m<range>        Minute           0-59
        *               Wildcard leaf — "match everything from here"
        RANGE ::= DIGITS | DIGITS "-" DIGITS

**Tie breaking:**

Longer (more dots) paths beat shorter ones. The following order is used for tie breaks (TODO: allow user to specify ordering):

        QTR < MOY < DOW < DOM < WOY < DOY < HH < MM
