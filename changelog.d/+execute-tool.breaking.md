Move execute tool span, specialized tool call spans, and `gen_ai.execute_tool.duration` metric to `execute-tool.md`. Span type is renamed from `gen_ai.execute_tool.internal` to `gen_ai.execute_tool`, and refinement ids drop the `.internal` suffix.

Execute tool operations SHOULD NOT be reported on `gen_ai.client.operation.duration` - use `gen_ai.execute_tool.duration` instead.
