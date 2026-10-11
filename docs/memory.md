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

Experimental compiled callbacks carry code IDs and captured Shen values rather
than opaque host closures. Before calling native code, the machine registers its
pending frames and the callback's local roots. Nested interpreter calls therefore
see both kinds of roots. Normal and exceptional returns restore the preceding
root stack. Generated code addresses are installed once per world; this private
interface is not a hot-module-loading API.

## Raw vector allocation bound

Finite lengths are truncated before conversion to a host integer. The runtime
rejects results outside 0 through 2^28 slots, matching the explicit maximum in
the pinned Go primitive. This check occurs before host allocation or narrowing.
Attempt 081 showed an enormous finite request returning a vector instead of a
catchable error; attempt 083 verifies the repaired range behavior. Non-finite
lengths are also rejected. This limit is not a long-running memory qualification.
