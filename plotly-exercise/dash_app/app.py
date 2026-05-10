from dash import Dash, dcc, html
import numpy as np
import plotly.graph_objects as go


# 🚀✨🎯👉 TU wpisz swój customowy tekst! 🌟🔥💫💥
CUSTOM_TEXT = "twój customowy napis"


def rastrigin(x, y):
    a = 10
    return 2 * a + (x**2 - a * np.cos(2 * np.pi * x)) + (y**2 - a * np.cos(2 * np.pi * y))


def build_figure():
    x_vals = np.linspace(-5.12, 5.12, 150)
    y_vals = np.linspace(-5.12, 5.12, 150)
    X, Y = np.meshgrid(x_vals, y_vals)
    Z = rastrigin(X, Y)

    fig = go.Figure(
        data=go.Surface(
            x=X,
            y=Y,
            z=Z,
            colorscale="Viridis",
        )
    )

    fig.update_layout(
        title="Rastrigin function - 3D surface",
        scene=dict(
            xaxis_title="x",
            yaxis_title="y",
            zaxis_title="f(x, y)",
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        height=700,
    )

    return fig


app = Dash(__name__)
server = app.server

app.layout = html.Div(
    className="container",
    children=[
        html.H1(CUSTOM_TEXT, className="title"),
        html.P("Minimalna aplikacja Dash + Plotly", className="subtitle"),

        html.Div(
            className="graph-card",
            children=[
                dcc.Graph(figure=build_figure())
            ],
        ),
    ]
)


if __name__ == "__main__":
    app.run(debug=True, port=8050)