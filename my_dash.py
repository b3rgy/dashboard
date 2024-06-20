import dash
from dash import html

# 1. import the packages
# 2. instantiate/load object

app = dash.Dash()  # creating our app, the variable holds an empty dashboard

app.layout = html.Div(html.H1(children = 'My First Spicy Dash'))

meep = 'Hello guys'


if __name__ == '__main__':
     app.run_server()


# my_dash.py
#  |
#  ---> meep

#  my_test.py
#  |
#  ---> import my_dash
#  ---> my_dash.meep

#  Terminal: ```python my_dash.py```  -> __name__ = '__main__'
#  Import:      import my_dash        -> __name__ != '__main__'

