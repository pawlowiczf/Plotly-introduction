from dash import dcc, html
import plotly.express as px


def build_figure():
    df = px.data.gapminder()
    df_2007 = df[df["year"] == 2007]

    fig = px.choropleth(
        df_2007,
        locations="iso_alpha",
        color="lifeExp",
        hover_name="country",
        color_continuous_scale="Plasma",
        projection="natural earth",
        title="Life expectancy by country (2007) - styled",
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=60, b=0),
        height=820,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e8ecf3"),
    )

    fig.update_geos(
        projection_scale=1.42,
        showcountries=True,
        countrycolor="rgba(220,220,220,0.35)",
        showcoastlines=True,
        coastlinecolor="rgba(220,220,220,0.35)",
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
    )

    return fig


def layout():
    df = px.data.gapminder()
    df_2007 = df[df["year"] == 2007]

    avg_life = round(df_2007["lifeExp"].mean(), 2)
    max_life = round(df_2007["lifeExp"].max(), 2)
    min_life = round(df_2007["lifeExp"].min(), 2)

    return html.Div(
        className="globe-css-page",
        children=[
            html.Link(rel="stylesheet", href="/assets/globe.css"),

            html.Div(
                className="hero-panel",
                children=[
                    html.H2("Globe - with CSS", className="hero-title"),
                    html.P(
                        "Ta wersja pokazuje osobny styling dla konkretnej podstrony. "
                        "W praktyce Dash i tak ładuje CSS z assets globalnie, ale tutaj "
                        "dorzucamy też stylesheet explicite i ograniczamy jego działanie "
                        "do tej strony przez klasy CSS.",
                        className="hero-subtitle",
                    ),
                ],
            ),

            html.Div(
                className="globe-stats",
                children=[
                    html.Div(
                        className="globe-stat-card",
                        children=[
                            html.Div("Average life expectancy", className="globe-stat-label"),
                            html.Div(f"{avg_life}", className="globe-stat-value"),
                        ],
                    ),
                    html.Div(
                        className="globe-stat-card",
                        children=[
                            html.Div("Max life expectancy", className="globe-stat-label"),
                            html.Div(f"{max_life}", className="globe-stat-value"),
                        ],
                    ),
                    html.Div(
                        className="globe-stat-card",
                        children=[
                            html.Div("Min life expectancy", className="globe-stat-label"),
                            html.Div(f"{min_life}", className="globe-stat-value"),
                        ],
                    ),
                ],
            ),

            html.Div(
                className="globe-graph-wrap",
                children=[
                    dcc.Graph(
                        figure=build_figure(),
                        className="main-graph",
                    )
                ],
            ),

            html.Div(
                className="globe-note",
                children=[
                    "Tutaj widać, że sam wykres Plotly to tylko część całości - "
                    "Dash pozwala też stylować całe otoczenie aplikacji jak normalny UI."
                ],
            ),
        ],
    )