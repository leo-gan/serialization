# Results

Read numbers on the [live dashboard](https://leo-gan.github.io/GLD.SerializerBenchmark/dashboard/). This page names the measurements. It does not copy values from a run, because the next run would make the copy stale.

{{ measurement_table() }}

The column names in the detail cells are the benchmark runner's names. The [metrics catalog](https://leo-gan.github.io/GLD.SerializerBenchmark/analysis/METRICS/) is the full dictionary, including medians, percentiles, and how important each column is on the dashboard.

## Planned measurements

The benchmark's metrics catalog names the following items as planned. They are not results on this site.

{{ planned_table() }}

## How a number reaches the dashboard

A language runner writes a CSV log. Times in that log are nanoseconds. The benchmark site builds the dashboard from those logs. This hub links to the dashboard.

A later step could turn those logs into tables on this site. That step is not built.
