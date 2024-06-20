import dash
from dash import Dash, html
import plotly
import plotly.express as px
import pandas as pd


app =dash.Dash()
app.layout = html.Div(html.H1(children = 'My First Spicy Dash'))

if __name__ == '__main__':
     app.run_server() 



server= app.server