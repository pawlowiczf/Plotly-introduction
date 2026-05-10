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
        title="Life expectancy by country (2007) - better",
    )

    fig.update_layout(
        margin=dict(l=0, r=0, t=60, b=0),
        height=820,
        paper_bgcolor="rgba(0,0,0,0)",
    )

    fig.update_geos(
        projection_scale=1.45,
        showcountries=True,
        countrycolor="rgba(40,40,40,0.85)",
        showcoastlines=True,
        coastlinecolor="rgba(70,70,70,0.7)",
        showframe=False,
        bgcolor="rgba(0,0,0,0)",
    )

    return fig


def layout():
    return html.Div(
        className="page",
        children=[
            html.H2("Globe - better", className="page-title"),
            html.P(
                "Ta wersja ma wyraźnie większą mapę, mniej pustego miejsca i poprawione proporcje.",
                className="page-subtitle",
            ),
            html.Div(
                style={"padding": "8px"},
                children=[
                    dcc.Graph(
                        figure=build_figure(),
                        className="main-graph",
                    )
                ],
            ),
        ],
    )