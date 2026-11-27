# Filters for per-operation and per-namespace docs. Signals are grouped by
# `annotations.docs.operation`; entities are not tied to an operation.

# Signals of one type (`spans`, `metrics`, `events`, `entities`) from
# `.refinements`, each tagged with `signal`. Refinements get `_refines_local`
# (the refined signal is documented here) and `_refines_operation`.
def _documented($signal):
  .deprecated == null and (.annotations.docs.operation != null or $signal == "entities");

def _signals($signal):
  [.refinements | to_entries[] | select(.key == $signal) | .key as $s | .value as $all | $all[]
   | select(_documented($s))
   | (.type // .name) as $b
   | . + {signal: $s,
          _refines_local: ([$all[] | select(.id == $b and _documented($s))] | length > 0),
          _refines_operation: ([$all[] | select(.id == $b) | .annotations.docs.operation] | first)}];

# Snippet: index table of an operation's signals, excluding refinements from
# other namespaces.
def operation_index_table($operation; $signal):
  {signal_overview: [_signals($signal)[]
    | select(.annotations.docs.operation == $operation
             and (.id | split(".") | first) == ($operation | split(".") | first))]};

# Snippet: index table of a namespace's signals and refinements.
def namespace_index_table($namespace; $signal):
  {signal_overview: [_signals($signal)[] | select((.id | split(".") | first) == $namespace)]};

# Entities (and entity refinements) grouped by namespace.
def entities_index:
  [.refinements.entities[] | select(.deprecated == null)]
  | group_by(.id | split(".") | first)
  | map({namespace: (.[0].id | split(".") | first), items: map(. + {signal: "entities"})});

# One item per signal page. Refinements get `_refines` (base id), `_refines_local`
# and `_refines_operation` (to link the base), and `_added` / `_changed`: attribute
# keys they add or whose requirement level they change. Base signals get
# `_refinements`, the documented refinements of them.
def signal_pages:
  (.registry | {
    spans: (.spans | map({key: .type, value: ((.attributes // []) | map({key: .key, value: .requirement_level}) | from_entries)}) | from_entries),
    metrics: (.metrics | map({key: .name, value: ((.attributes // []) | map({key: .key, value: .requirement_level}) | from_entries)}) | from_entries),
    events: (.events | map({key: .name, value: ((.attributes // []) | map({key: .key, value: .requirement_level}) | from_entries)}) | from_entries),
    entities: (.entities | map({key: .type, value: (((.identity // []) + (.description // [])) | map({key: .key, value: .requirement_level}) | from_entries)}) | from_entries)
  }) as $base
  | [ (.refinements.spans[] | {signal: "spans", item: .}),
      (.refinements.metrics[] | {signal: "metrics", item: .}),
      (.refinements.events[] | {signal: "events", item: .}),
      (.refinements.entities[] | {signal: "entities", item: .}) ]
  | map(select((.item.annotations.docs.operation != null or .signal == "entities") and .item.deprecated == null)
    | . + {operation: .item.annotations.docs.operation, id: .item.id, base: (.item.type // .item.name)})
  | . as $all
  | map(. as $e | ($base[$e.signal] // {})[$e.base] as $b
    | ((.item.attributes // []) + (.item.identity // []) + (.item.description // [])) as $attrs
    | .item = (.item + (if $e.id == $e.base then {
        _refinements: [$all[] | select(.signal == $e.signal and .base == $e.base and .id != $e.base) | {id, operation}]
      } else {
        _refines: $e.base,
        _refines_local: ([$all[] | select(.signal == $e.signal and .id == $e.base)] | length > 0),
        _refines_operation: ([$all[] | select(.signal == $e.signal and .id == $e.base) | .operation] | first),
        _added: (if $b == null then [] else [$attrs[] | select(.key as $k | $b | has($k) | not) | .key] end),
        _changed: (if $b == null then [] else [$attrs[] | select(.key as $k | ($b | has($k)) and $b[$k] != .requirement_level) | .key] end)
      } end)));
