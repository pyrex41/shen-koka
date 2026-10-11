# Numeric and character observations

These are exact CLI observations, not a pass/fail replacement for the full suite.
Strings are quoted by Koka eval but printed without quotes by the reference CLIs.
The report retains byte-for-byte output as hexadecimal, including invalid UTF-8.

| Probe | Koka | Go | Lua |
|---|---|---|---|
| mixed | `'1.5'` (exit 0) | `'1.5'` (exit 0) | `'1.5'` (exit 0) |
| division | `'1.5'` (exit 0) | `'1.5'` (exit 0) | `'1.5'` (exit 0) |
| zero-division | `'caught'` (exit 0) | `'caught'` (exit 0) | `'caught'` (exit 0) |
| negative-zero | `'"0"'` (exit 0) | `'0'` (exit 0) | `'0'` (exit 0) |
| large-integer | `'true'` (exit 0) | `'true'` (exit 0) | `'true'` (exit 0) |
| exponent | `'true'` (exit 0) | `'true'` (exit 0) | `'true'` (exit 0) |
| integer-predicate | `'[true false]'` (exit 0) | `'[true false]'` (exit 0) | `'[true false]'` (exit 0) |
| unicode-pos | `'"x"'` (exit 0) | `'x'` (exit 0) | `'\\xbb'` (exit 0) |
| unicode-code | `'955'` (exit 0) | `'955'` (exit 0) | `'206'` (exit 0) |
| unicode-tail | `'"x"'` (exit 0) | `'x'` (exit 0) | `'\\xbbx'` (exit 0) |
| unicode-roundtrip | `'"λ"'` (exit 0) | `''` (exit 1) | `''` (exit 1) |
| nul-roundtrip | `'0'` (exit 0) | `'0'` (exit 0) | `'0'` (exit 0) |
| empty-code | `'caught'` (exit 0) | `'#<err trap-error result is not Obj>'` (exit 0) | `'caught'` (exit 0) |
| negative-pos | `'caught'` (exit 0) | `'caught'` (exit 0) | `'caught'` (exit 0) |
| past-end-pos | `'caught'` (exit 0) | `'caught'` (exit 0) | `'caught'` (exit 0) |
| fraction-pos | `'"a"'` (exit 0) | `'a'` (exit 0) | `'a'` (exit 0) |

Lua uses byte-oriented pos/tlstr/string->n; Koka uses codepoints, matching Go for
those probes. Go CLI rejects n->string 955 even though the pinned interpreter
primitive permits Unicode scalar-range integers; its compiled path therefore
needs separate comparison. Do not normalize this discrepancy into agreement.
The large-integer probe confirms the observed float64 precision boundary.
These observations do not yet cover non-finite numbers or every conversion bound.
