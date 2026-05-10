from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go

# Load bundled sample data - fast, no download
df = px.data.gapminder()

# Precompute constants used in the layout
YEARS = sorted(df.year.unique())
POP_MAX = int(df["pop"].max())
CONTINENTS = sorted(df.continent.unique())

app = Dash()

app.layout = html.Div([
    html.H1("Gapminder explorer", style={"textAlign": "center"}),

    html.Div([
        # LEFT COLUMN: controls
        html.Div([
            html.Label("Year", style={"fontWeight": "bold"}),
            dcc.Slider(
                id="year", min=min(YEARS), max=max(YEARS), step=None,
                value=2007,
                marks={int(y): str(y) for y in YEARS},
            ),

            html.Br(),
            html.Label("Population range", style={"fontWeight": "bold"}),
            dcc.RangeSlider(
                id="pop-range",
                min=0, max=POP_MAX, step=10_000_000,
                value=[0, POP_MAX],
                marks={
                    0: "0",
                    100_000_000: "100M",
                    500_000_000: "500M",
                    1_000_000_000: "1B",
                    POP_MAX: f"{POP_MAX/1e9:.1f}B",
                },
            ),

            html.Br(),
            html.Label("Continents", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="continents",
                options=[{"label": c, "value": c} for c in CONTINENTS],
                value=CONTINENTS,
                multi=True,
            ),

            html.Br(),
            html.Label("Chart type", style={"fontWeight": "bold"}),
            dcc.RadioItems(
                id="chart-type",
                options=[
                    {"label": " Scatter", "value": "scatter"},
                    {"label": " Bar (top 20 by GDP)", "value": "bar"},
                    {"label": " Box plot", "value": "box"},
                ],
                value="scatter",
                labelStyle={"display": "block", "margin": "4px 0"},
            ),

            html.Br(),
            html.Label("Options", style={"fontWeight": "bold"}),
            dcc.Checklist(
                id="options",
                options=[
                    {"label": " Log scale X", "value": "log-x"},
                    {"label": " Log scale Y", "value": "log-y"},
                    {"label": " Show country labels", "value": "labels"},
                ],
                value=["log-x"],
                labelStyle={"display": "block", "margin": "4px 0"},
            ),
        ], style={"width": "25%", "padding": "20px",
                  "backgroundColor": "#f7f7f7", "borderRadius": "8px"}),

        # RIGHT COLUMN: chart + stats
        html.Div([
            dcc.Graph(id="main-chart"),
            html.Div(id="stats", style={"padding": "10px 20px",
                                         "fontSize": "16px"}),
        ], style={"width": "73%", "paddingLeft": "20px"}),
    ], style={"display": "flex"}),
])


@callback(
    Output("main-chart", "figure"),
    Output("stats", "children"),
    Input("year", "value"),
    Input("pop-range", "value"),
    Input("continents", "value"),
    Input("chart-type", "value"),
    Input("options", "value"),
)
def update(year, pop_range, continents, chart_type, options):
    # Filter dataset based on current control values
    dff = df[
        (df.year == year)
        & (df["pop"] >= pop_range[0])
        & (df["pop"] <= pop_range[1])
        & (df.continent.isin(continents))
    ]

    # Handle empty selection gracefully
    if dff.empty:
        fig = go.Figure().update_layout(
            annotations=[dict(text="No data matches the filters",
                              xref="paper", yref="paper",
                              x=0.5, y=0.5, showarrow=False,
                              font=dict(size=18))],
            height=550,
        )
        return fig, "0 countries"

    log_x = "log-x" in options
    log_y = "log-y" in options
    show_labels = "labels" in options

    # Build chart based on selected type
    if chart_type == "scatter":
        fig = px.scatter(
            dff, x="gdpPercap", y="lifeExp",
            size="pop", color="continent",
            hover_name="country",
            text="country" if show_labels else None,
            log_x=log_x, log_y=log_y,
            size_max=55,
        )
    elif chart_type == "bar":
        top20 = dff.nlargest(20, "gdpPercap")
        fig = px.bar(
            top20, x="country", y="gdpPercap",
            color="continent",
            log_y=log_y,
        )
    else:  # box
        fig = px.box(
            dff, x="continent", y="lifeExp",
            color="continent", points="all",
            log_y=log_y,
        )

    fig.update_layout(
        height=550,
        margin=dict(l=40, r=40, t=40, b=40),
        title=f"{len(dff)} countries in {year}",
    )

    # Build summary stats panel
    stats = html.Div([
        html.Span(f"Countries: {len(dff)}   ", style={"marginRight": "20px"}),
        html.Span(f"Avg life exp: {dff.lifeExp.mean():.1f} years   ",
                  style={"marginRight": "20px"}),
        html.Span(f"Total pop: {dff['pop'].sum()/1e9:.2f}B   ",
                  style={"marginRight": "20px"}),
        html.Span(f"Median GDP/capita: ${dff.gdpPercap.median():,.0f}"),
    ])

    return fig, stats


if __name__ == "__main__":
    app.run(debug=True)