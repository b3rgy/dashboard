import requests
import plotly
import json
import datetime
import pandas as pd
from sqlalchemy import create_engine, text, types 
from sqlalchemy.dialects.postgresql import JSON as postgres_json
from dotenv import dotenv_values
import os
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine
import pandas as pd 
import dash
from dash import Dash, dcc, html, callback
from dash.dependencies import Input, Output, State
import plotly.express as px
from dash import dash_table
import dash_bootstrap_components as dbc

# 1. import the packages
# 2. instantiate/load object
#connecting to thte database - extracting the data
# copied from the course materials because Render is not calling the .env from my local drive but from the environment variables that we have setup
load_dotenv()

weather_api_key = os.getenv("WEATHER_API_KEY")
host = os.getenv("POSTGRES_HOST")
password = os.getenv("POSTGRES_PASS")
db_name = os.getenv("POSTGRES_DB")

#config = dotenv_values('/Users/spiced/Documents/GitHub/SPICEDRepo/clovebases-student-code/Week7/token.env')

#host = config['POSTGRES_HOST'] # align the key label with your .env file !
#password = config['POSTGRES_PASS']
#db_name = config['POSTGRES_DB']

#weather_api_key = config['weatherapi']
# and other environmental variables you need

postgres_url = f'postgresql://postgres:{password}@{host}:5432/{db_name}'
engine = create_engine(postgres_url, echo=False)

# extracting the data

with engine.begin() as conn:
    result = conn.execute(text("SELECT * FROM mart_forecast_day;"))
    data = result.all()

df = pd.DataFrame(data)

# filtering the data + creation of figure

# Filter data for Berlin, Cagliari, and Hamburg
df_filtered = df[df['city'].isin(['Berlin', 'Cagliari', 'Hamburg'])]

# Create an interactive line plot for Berlin, Cagliari, and Hamburg
fig_avg_temp_BCH = px.line(df_filtered, x='date', y='avg_temp_c', color='city', 
              title='Average Temperatures in Berlin, Cagliari, and Hamburg', 
              labels={'date': 'Date', 'avg_temp_c': 'Average Temperature (°C)', 'city': 'Location'},
              template='plotly_dark')
graph_avg_temp = dcc.Graph(figure=fig_avg_temp_BCH)

# Create an interactive line plot for Berlin, Cagliari, and Hamburg
fig_max_temp_BCH = px.line(df_filtered, x='date', y='max_temp_c', color='city', 
              title='Max Temperatures in Berlin, Cagliari, and Hamburg', 
              labels={'date': 'Date', 'max_temp_c': 'Max Temperature (°C)', 'city': 'Location'},
              template='plotly_dark')
graph_max_temp = dcc.Graph(figure=fig_max_temp_BCH)

# create an interactive climate map for europe

# Average temperature per city on map
df_avg_temp = df.groupby(['city', 'lat', 'lon']).agg({'avg_temp_c': 'mean'}).reset_index()


fig_map = px.scatter_mapbox(df_avg_temp, 
                        lat='lat', 
                        lon='lon', 
                        hover_name='city', 
                        hover_data={'avg_temp_c': True}, 
                        color='city', 
                        title='Average Temperature in European Cities', 
                        color_continuous_scale='Viridis',
                        size_max=15, 
                        zoom=3)

fig_map.update_layout(mapbox_style='open-street-map')
graph_map = dcc.Graph(figure=fig_map)

# creating a chloropleth map of avg temp

# Aggregate the average temperature by country
df_avg_temp_choropleth = df.groupby(['country']).agg({'avg_temp_c': 'mean'}).reset_index()

# Create a choropleth map
fig_map_choropleth = px.choropleth(df_avg_temp_choropleth, 
                    locations='country',
                    locationmode='country names',
                    color='avg_temp_c',
                    hover_name='country',
                    color_continuous_scale='Viridis',
                    title='Average Temperature in European Countries')
graph_choropleth_map = dcc.Graph(figure=fig_map_choropleth)

app = dash.Dash()  # creating our app, the variable holds an empty dashboard
server = app.server

app.layout = html.Div(children=[
    html.H1(children='Temperature Dashboard'),
    html.Div([graph_max_temp,graph_avg_temp,graph_map,graph_choropleth_map])
    ])


if __name__ == '__main__':
     app.run_server()
