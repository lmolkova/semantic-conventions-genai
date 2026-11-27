# Filters for the docs layout: hand-written operation READMEs embed index
# tables (snippets), the generated registry documents every signal.

# Base attribute requirement levels per signal type, keyed by signal id.
def _base_attrs:
  .registry | {
    spans: (.spans | map({key: .type, value: ((.attributes // []) | map({key: .key, value: .requirement_level}) | from_entries)}) | from_entries),
    metrics: (.metrics | map({key: .name, value: ((.attributes // []) | map({key: .key, value: .requirement_level}) | from_entries)}) | from_entries),
    events: (.events | map({key: .name, value: ((.attributes // []) | map({key: .key, value: .requirement_level}) | from_entries)}) | from_entries),
    entities: (.entities | map({key: .type, value: (((.identity // []) + (.description // [])) | map({key: .key, value: .requirement_level}) | from_entries)}) | from_entries)
  };

# Every signal and refinement, tagged with `signal`, `base` (the refined id or
# its own id) and `_refines_local` (the refined signal is defined here).
def _all_signals:
  [ (.refinements.spans[] | . + {signal: "spans"}),
    (.refinements.metrics[] | . + {signal: "metrics"}),
    (.refinements.events[] | . + {signal: "events"}),
    (.refinements.entities[] | . + {signal: "entities"}) ]
  | map(. + {base: (.type // .name)})
  | . as $all
  | map(. as $e | . + {_refines_local: ([$all[] | select(.signal == $e.signal and .id == $e.base)] | length > 0)});

def _ns: .id | split(".") | first;

# Snippet: index table of an operation's signals, excluding deprecated ones
# and refinements from other namespaces.
def operation_index_table($operation; $signal):
  {signal_overview: [_all_signals[]
    | select(.signal == $signal and .deprecated == null
             and .annotations.docs.operation == $operation
             and _ns == ($operation | split(".") | first))]};

# Snippet: index table of a namespace's signals and refinements.
def namespace_index_table($namespace; $signal):
  {signal_overview: [_all_signals[] | select(.signal == $signal and .deprecated == null and _ns == $namespace)]};

# One item per signal page. Refinements get `_refines` and `_added` /
# `_changed`: attribute keys they add or whose requirement level they change.
# Base signals get `_refinements`.
def signal_pages:
  _base_attrs as $base
  | _all_signals
  | . as $all
  | map(. as $e | ($base[$e.signal] // {})[$e.base] as $b
    | ((.attributes // []) + (.identity // []) + (.description // [])) as $attrs
    | {signal, id, operation: .annotations.docs.operation,
       item: (. + (if $e.id == $e.base then {
         _refinements: [$all[] | select(.signal == $e.signal and .base == $e.base and .id != $e.base) | {id}]
       } else {
         _refines: $e.base,
         _added: (if $b == null then [] else [$attrs[] | select(.key as $k | $b | has($k) | not) | .key] end),
         _changed: (if $b == null then [] else [$attrs[] | select(.key as $k | ($b | has($k)) and $b[$k] != .requirement_level) | .key] end)
       } end))});

# Registry README per namespace: all its signals and attributes.
def namespace_registry:
  (semconv_grouped_attributes({"v2": true}) | map({key: .root_namespace, value: .attributes}) | from_entries) as $attrs
  | _all_signals as $sigs
  | ([$sigs[] | _ns] + ($attrs | keys)) | unique
  | map(. as $ns | {namespace: $ns, items: [$sigs[] | select(_ns == $ns)], attributes: ($attrs[$ns] // [])});
