# Standards

A serialization standard is the published specification for a format. A reader and a writer follow that specification so they agree on the bytes.

The full list of standards is on the benchmark's [Compliance](https://leo-gan.github.io/GLD.SerializerBenchmark/compliance/) page.

## Types

Schema means a decoder needs a schema. Schema-less means a decoder can walk a value without one.

The Mojo libraries on this site cover these standards:

{{ standards_table() }}

The benchmark groups serializers into families, including schema-driven formats and schema-less formats. That grouping is explained on [Serialization categories](https://leo-gan.github.io/GLD.SerializerBenchmark/analysis/serialization_categories/).
