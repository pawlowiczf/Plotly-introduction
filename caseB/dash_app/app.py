from dash import Dash, Input, Output, dcc, html
from endpoints import globe, globe_better, globe_with_css

app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server


def home_layout():
    return html.Div(
        className="page",
        children=[
            html.Div(
                className="home-card",
                children=[
                    html.H1("Plotly / Dash - globe demo", className="home-title"),
                    html.P(
                        "To jest główna apka Dash z trzema podstronami. Każda z nich pokazuje inną wersję tej samej mapy świata - od wersji bazowej po bardziej dopracowaną wizualnie.",
                        className="home-text",
                    ),
                    html.Ul(
                        className="list-clean",
                        children=[
                            html.Li("'/globe' - wersja bazowa"),
                            html.Li("'/globe-better' - poprawione marginesy i proporcje"),
                            html.Li("'/globe-with-css' - wersja stylowana"),
                        ],
                    ),
                ],
            )
        ],
    )


def not_found_layout(pathname: str):
    return html.Div(
        className="page",
        children=[
            html.Div(
                className="not-found-card",
                children=[
                    html.H2("404 - nie znaleziono strony", className="not-found-title"),
                    html.P(f"Ścieżka '{pathname}' nie istnieje.", className="page-subtitle"),
                ],
            )
        ],
    )


app.layout = html.Div(
    className="app-shell",
    children=[
        dcc.Location(id="url", refresh=False),
        html.Header(
            className="topbar",
            children=[
                html.Div(
                    className="topbar-inner",
                    children=[
                        html.Div("Dash Globe Demo", className="brand"),
                        html.Nav(
                            className="nav-links",
                            children=[
                                dcc.Link("Home", href="/", className="nav-link"),
                                dcc.Link("Globe", href="/globe", className="nav-link"),
                                dcc.Link("Globe Better", href="/globe-better", className="nav-link"),
                                dcc.Link("Globe With CSS", href="/globe-with-css", className="nav-link"),
                            ],
                        ),
                    ],
                )
            ],
        ),
        html.Main(id="page-content", className="content-shell"),
    ],
)


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
)
def render_page(pathname):
    if pathname == "/" or pathname is None:
        return home_layout()

    if pathname == "/globe":
        return globe.layout()

    if pathname == "/globe-better":
        return globe_better.layout()

    if pathname == "/globe-with-css":
        return globe_with_css.layout()

    return not_found_layout(pathname)


if __name__ == "__main__":
    app.run(debug=True, port=8050)