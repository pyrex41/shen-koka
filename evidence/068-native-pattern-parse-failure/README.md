The generated match body was insufficiently indented for Koka's layout parser.
No case executed. The original harness emitted an empty cases object on compile
failure; all 37 intended cases are UNKNOWN, not zero required tests. The harness
now populates every case as UNKNOWN before compilation and retains a generator
snapshot. The full Shen runner's fixed 134 + 8 denominator was unaffected.
