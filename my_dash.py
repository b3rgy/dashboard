import dash
from dash import Dash, html

app =dash.Dash()

app.layout = html.Div(html.H1(children = 'My First Spicy Dash'))

if __name__ == '__main__':
     app.run_server() 