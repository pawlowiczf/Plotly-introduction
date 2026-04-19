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
        title="Life expectancy by country (2007) - default",
    )

    return fig


def layout():
    return html.Div(
        className="page",
        children=[
            html.H2("Globe - default", className="page-title"),
            html.P(
                "Bazowa wersja mapy Plotly praktycznie bez tuningu.",
                className="page-subtitle",
            ),
            dcc.Graph(
                figure=build_figure(),
            ),
        ],
    )