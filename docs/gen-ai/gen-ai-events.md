<!--- Hugo front matter used to generate the website version of this page:
linkTitle: Events
--->

# Semantic conventions for Generative AI events

**Status**: [Development][DocumentStatus]

<!-- toc -->

- [Event: `gen_ai.evaluation.result`](#event-gen_aievaluationresult)

<!-- tocstop -->

GenAI instrumentations MAY capture user inputs sent to the model and responses received from it as [events](https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/specification/logs/data-model.md#events).
Capturing message content on events is controlled by [content capture configuration](gen-ai-spans.md#content-capture-configuration) (e.g. `OTEL_INSTRUMENTATION_GENAI_CAPTURE_CONTENT=EVENT_ONLY` or `SPAN_AND_EVENT`).

> [!Note]
> Events are in-development and not yet available in some languages. Check [spec-compliance matrix](https://github.com/open-telemetry/opentelemetry-specification/blob/v1.55.0/spec-compliance-matrix.md#logs) to see the implementation status in corresponding language.

For events describing inference operations, see [Client Inference](client-inference/README.md#events).

## Event: `gen_ai.evaluation.result`

See [`gen_ai.evaluation.result`](evaluation/events/gen_ai.evaluation.result.md) for the definition.

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
