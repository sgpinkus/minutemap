# (YEARLY) MINUTE MAP
Python library to specify a value (`int` by default) for any and every minute of an entire year. Which particular year isn't representable. Specifiers are like crontab's but hierarchical. Hierarchy and priority matching rules are used to determine the value for any given minute of the year.

Create a `YearMinuteMap` instance then call `YearMinuteMap.get_value()` with a `datetime` to resolve a value:

```python
my_minute_map =  {
  "*": 8,
  "h5-10": 28,
  "q1": {
    "*": 18,
    "h18-22": 22
  },
  "q4": {
    "*": 14,
     "h18-22": 18
  },
  "q2": {
    "*": 10,
    "h5-10": 30,
    "h19-23": 20
  },
  "q3": {
    "h0-4": 12,
    "h5-10": 32,
    "h11-18": 12,
    "h19-23": 20
    "sun": {
      "h0-4": 14,
      "h5-10": 34,
      "h11-18": 14,
      "h19-23": 23
    }
  }
}
spec = YearMinuteMap(my_minute_map)
spec.get_value(my_date) # -> value
```

As shown above, a specification takes the form of a set of `<expression, value>` pairs in JSON or as a dictionary. `expressions` are a sequence of time tokens. The wildcard "\*" may appear as a standalone spec or as a leaf segment, and means "everything else" not matched my siblings at this level. Input may be a flat nested form. Both dict and JSON string are accepted. Flat Example:

```
  {
    "*": 1,
    "q1": 2,
    "q1.sun.h1-10.m1": 3
    "q1.sun.h1-10.m2": 4
  }
```

Crontab like steps and lists are supported:

```
{
    "h0-11.m*/2": 1,
    "h12-22.m*/3": 2,
    "h23.m1,2,3,5,8,13,21,34,55": 3,
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
