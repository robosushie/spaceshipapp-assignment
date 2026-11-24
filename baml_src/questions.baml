enum ChartType {
  Bar @alias("bar")
  Line @alias("line")
  Area @alias("area")
  Pie @alias("pie")
  Scatter @alias("scatter")
}

enum ToolName {
  Query @alias("query")
  Forecast @alias("forecast")
}

enum ForecastMethod {
  Auto @alias("auto")
  MovingAverage @alias("moving_average")
  ExponentialSmoothing @alias("exponential_smoothing")
  HoltTrend @alias("holt_trend")
  SeasonalNaive @alias("seasonal_naive")
  LinearTrend @alias("linear_trend")
  Mean @alias("mean")
  Naive @alias("naive")
  Drift @alias("drift")
  DampedTrend @alias("damped_trend")
  Theta @alias("theta")
  Croston @alias("croston")
  Sba @alias("sba")
  Tsb @alias("tsb")
}

class ToolChoice {
  tool ToolName
  sku string?
  horizon_months int?
  start_month string?
  end_month string?
  method ForecastMethod?
}

class QueryPlan {
  sql string
  plot_required bool
  chart_type ChartType?
  title string?
  x_key string?
  y_keys string[]
  filters string[]
  metrics string[]
  dimensions string[]
}

function ChooseTool(question: string, as_of: string) -> ToolChoice {
  client AnthropicSonnet
  prompt #"
    Choose the tool for this question about a shipping book that ends on {{ as_of }}.
    Use forecast when the question asks to predict, forecast, or project demand,
    or to recommend how much inventory to hold.
    Use query for counts, filters, comparisons, trends in the book, and charts of past orders.
    sku is the product SKU when the question names one. Otherwise leave sku null.
    start_month and end_month are YYYY-MM when the question names a month or a range.
    June 2027 sets both to 2027-06.
    March 2026 through June 2027 sets start_month to 2026-03 and end_month to 2027-06.
    "through December 2026" sets end_month to 2026-12 and leaves start_month null.
    "next 4 months" leaves both null and sets horizon_months to 4.
    Leave horizon_months null when start_month or end_month is set.
    horizon_months is how many future months to forecast, from 1 to 60.
    Use 4 when the question names no month and does not say how far.
    Leave horizon_months, start_month, and end_month null for a query.
    Pass a month inside the book through as written. Do not move it into the future.
    method is auto unless the question names a forecasting method.
    Use moving_average for a moving average, exponential_smoothing for exponential smoothing,
    holt_trend for Holt or a trend, seasonal_naive for seasonal or the same month last year,
    linear_trend for a linear trend, mean for the historical average,
    naive for the last month repeated, drift for drift,
    damped_trend for a damped trend, theta for theta,
    croston for Croston, sba for Syntetos-Boylan, and tsb for Teunter-Syntetos-Babai.
    Leave method null for a query.

    Question:
    {{ question }}

    {{ ctx.output_format }}
  "#
}

function WriteQuery(
  question: string,
  schema: string,
  as_of: string,
  previous_sql: string,
  error: string
) -> QueryPlan {
  client AnthropicSonnet
  prompt #"
    Write one PostgreSQL SELECT that answers the question from this shipping book.
    Use only the tables and columns in the schema. Do not use users or refresh_tokens.
    The book ends on {{ as_of }}. Treat that date as today.
    "Last 3 months" is 2025-10-01 through {{ as_of }} when {{ as_of }} is 2025-12-30.
    Return exactly one statement. Alias every selected expression.
    Do not write INSERT, UPDATE, DELETE, DROP, or ALTER.

    Set plot_required to true when the question asks for a plot, chart, graph, trend,
    or a breakdown over time or by a category. Otherwise set it to false and leave
    chart_type, title, and x_key null, with y_keys empty.
    When plot_required is true, choose chart_type from the question and the result shape.
    line is a series over time, such as weeks or months.
    area is volume or a running total over time.
    bar is a comparison across categories.
    pie is one measure as a share of a whole, with few categories such as status, region,
    or carrier. Do not use pie for a time series. Pie uses a single y_key.
    scatter is two numeric columns, such as quantity against order value. Its x_key is numeric.
    x_key and y_keys must be the output column aliases. Use a line and a week column
    formatted YYYY-MM-DD for a week-by-week series.

    filters, metrics, and dimensions are short labels for how the question is read.
    filters are constraints such as a status, a date range, a carrier, or a region.
    metrics are the measures, such as orders or order value.
    dimensions are the groupings, such as month or carrier.
    Leave a list empty when the question has none. Do not put numbers in these lists.

    If error is not empty, the previous SQL failed. Fix it using the error. Do not repeat it.

    <schema>
    {{ schema }}
    </schema>

    Question:
    {{ question }}

    Previous SQL:
    {{ previous_sql }}

    Error:
    {{ error }}

    {{ ctx.output_format }}
  "#
}

function ExplainRows(question: string, rows_json: string, plot_required: bool) -> string {
  client AnthropicSonnet
  prompt #"
    Answer the question in one short paragraph using only these rows.
    The rows were returned by Postgres. If a number is zero or the row list is empty, say so.
    Do not invent orders, weeks, money, or causes.
    When plot_required is true, the same rows are drawn as a chart. Describe them.
    Do not say a plot is impossible when rows are present.

    Question:
    {{ question }}

    plot_required: {{ plot_required }}

    Rows:
    {{ rows_json }}

    {{ ctx.output_format }}
  "#
}
