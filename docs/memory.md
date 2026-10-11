# Runtime memory and roots

Koka reference counting owns immutable lists, terms and lexical environments.
Mutable vectors have stable numeric identities in a binary lookup trie. Their
cells are mutable Koka references: aliases always observe the same updates.
Identities are never reused, including after collection.

After each 1024 vector allocations, the machine collects between transitions.
Roots include globals, installed functions, the current expression/application/
result, lexical environments and every pending frame. Frames retain operands,
remaining expressions, handlers and overapplication arguments. The tracer visits
literal values inside executable terms as well as closure environments. A shared
identity set terminates closure/vector cycles. Sweeping removes unreachable
vector cells and prunes empty lookup branches. Immutable objects then follow
Koka's normal reference counting.

The focused suite checks discarded self-cycles and retained vectors in closures,
error handlers and already-evaluated operands. `shen-koka.heap-live` is a
port-specific diagnostic primitive returning the number of live arena entries.
It is not a Shen standard primitive. More retained-root, RSS and long-running
stress qualification remains required.

The current host API is private to the CLI and slice builder. A future embedding
API must register values retained outside the machine as roots; callers cannot
assume a bare numeric handle remains live after subsequent evaluations. Streams
currently use explicit close and a separate bounded host table, not vector GC.
