enum ChartType {
  Bar @alias("bar")
  Line @alias("line")
  Area @alias("area")
  Pie @alias("pie")
  Scatter @alias("scatter")
}

class QueryPlan {
  sql string
  plot_required bool
  chart_type ChartType?
  title string?
  x_key string?
  y_keys string[]
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
