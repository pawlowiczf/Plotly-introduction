from dash import html


def layout():
    return html.Div(
        className="page",
        children=[
            html.Div(
                className="home-card",
                children=[
                    html.H1("Do It Yourself", className="home-title"),
                    html.P(
                        "Zdeploy'uj swoją własną appkę Dash z użyciem Plotly Cloud w kilka minut.",
                        className="home-text",
                    ),
                    html.Ol(
                        className="list-clean",
                        children=[
                            html.Li(
                                [
                                    "Sklonuj repo z GitHuba:",
                                    html.Br(),
                                    html.Code("git clone https://github.com/pawlowiczf/Plotly-introduction"),
                                ]
                            ),
                            html.Li(
                                [
                                    "Wejdź do katalogu ",
                                    html.Code("do_it_yourself"),
                                    " i zacznij wykonywać instrukcje z ",
                                    html.Code("README.md"),
                                    ".",
                                ]
                            ),
                        ],
                    ),
                    html.P(
                        "Po wykonaniu kroków uruchomisz aplikację lokalnie i wrzucisz ją do Plotly Cloud.",
                        className="home-text",
                    ),
                    html.Div(
                        style={"marginTop": "16px"},
                        children=[
                            html.A(
                                "Otwórz repozytorium",
                                href="https://github.com/pawlowiczf/Plotly-introduction",
                                target="_blank",
                                rel="noopener noreferrer",
                                className="nav-link",
                            )
                        ],
                    ),
                ],
            )
        ],
    )