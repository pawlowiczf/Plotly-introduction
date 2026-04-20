from dash import Dash, Input, Output, dcc, html
from endpoints import globe, globe_better, globe_with_css, tutorial

app = Dash(__name__, suppress_callback_exceptions=True) # bo przez kilka endpointów może zacząc krzyczeć
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
                        "To jest główna aplikacja Dash z czterema podstronami. Trzy z nich pokazują kolejne wersje wizualizacji mapy świata - od podstawowej po bardziej dopracowaną. Czwarta prowadzi do tutoriala, gdzie możesz stworzyć i zdeployować własną apke Dash.",
                        className="home-text",
                    ),
                    html.Ul(
                        className="list-clean",
                        children=[
                            html.Li("'/globe' - wersja bazowa"),
                            html.Li("'/globe-better' - poprawione marginesy i proporcje"),
                            html.Li("'/globe-with-css' - wersja stylowana"),
                            html.Li("'/do-it-yourself' - mini tutorial do własnego deployu"),
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
                                dcc.Link("Do It Yourself", href="/do-it-yourself", className="nav-link"),
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

    if pathname == "/do-it-yourself":
        return tutorial.layout()

    return not_found_layout(pathname)


if __name__ == "__main__":
    app.run(debug=True, port=8050)