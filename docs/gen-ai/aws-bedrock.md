<!--- Hugo front matter used to generate the website version of this page:
linkTitle: AWS Bedrock
--->

# Semantic conventions for AWS Bedrock operations

**Status**: [Development][DocumentStatus]

## AWS Bedrock Spans

The Semantic Conventions for [AWS Bedrock](https://aws.amazon.com/bedrock/) extend and override the semantic conventions
for [Gen AI Spans](gen-ai-spans.md).

`gen_ai.provider.name` MUST be set to `"aws.bedrock"`.

These attributes track input data and metadata for a request to an AWS Bedrock model. The attributes include general Generative AI
attributes and ones specific the AWS Bedrock.

See [`aws.bedrock.gen_ai.client.inference`](client-inference/spans/aws.bedrock.gen_ai.client.inference.md) for the definition.

[DocumentStatus]: https://opentelemetry.io/docs/specs/otel/document-status
