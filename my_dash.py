import requests
import plotly
import json
import datetime
import pandas as pd
from sqlalchemy import create_engine, text, types 
from sqlalchemy.dialects.postgresql import JSON as postgres_json
from dotenv import load_dotenv
import os
import plotly.express as px
from dash import Dash, dcc, html, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_table

# Load environment variables from the .env file
load_dotenv()

weather_api_key = os.getenv("WEATHER_API_KEY")
host = os.getenv("POSTGRES_HOST")
password = os.getenv("POSTGRES_PASS")
db_name = os.getenv("POSTGRES_DB")

postgres_url = f'postgresql://postgres:{password}@{host}:5432/{db_name}'
engine = create_engine(postgres_url, echo=False)

# Extracting the data
with engine.begin() as conn:
    result = conn.execute(text("SELECT * FROM mart_forecast_day;"))
    data = result.all()

df = pd.DataFrame(data)

# Fetching the weather icons
def fetch_weather_icons(api_key, cities, start_date, end_date):
    weather_data = []
    for city in cities:
        for date in pd.date_range(start=start_date, end=end_date):
            response = requests.get(f"http://api.weatherapi.com/v1/history.json?key={api_key}&q={city}&dt={date.strftime('%Y-%m-%d')}")
            if response.status_code == 200:
                data = response.json()
                for forecast in data['forecast']['forecastday']:
                    weather_data.append({
                        'date': forecast['date'],
                        'city': city,
                        'country': data['location']['country'],
                        'avg_temp_c': forecast['day']['avgtemp_c'],
                        'max_temp_c': forecast['day']['maxtemp_c'],
                        'condition_text': forecast['day']['condition']['text'],
                        'condition_icon': forecast['day']['condition']['icon']
                    })
    return pd.DataFrame(weather_data)

cities = df['city'].unique()
start_date = df['date'].min()
end_date = df['date'].max()

df_weather = fetch_weather_icons(weather_api_key, cities, start_date, end_date)

# Instantiate/load the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE])  # Use Slate for dark theme
server = app.server

# Define the layout of the app
app.layout = html.Div(
    style={'font-family': 'Helvetica', 'backgroundColor': '#2c3e50', 'color': '#ecf0f1'}, 
    children=[
        html.H1(id='title', children='Temperature Dashboard'),
        dbc.Row([
            dbc.Col(dcc.Dropdown(
                id='city-dropdown',
                options=[{'label': city, 'value': city} for city in df['city'].unique()],
                value=['Berlin', 'Cagliari', 'Hamburg'],
                multi=True,
                style={'width': '100%'}
            ), width=6),
            dbc.Col(dcc.RangeSlider(
                id='date-slider',
                min=0,
                max=(end_date - start_date).days,
                value=[0, (end_date - start_date).days],
                marks={i: (start_date + pd.Timedelta(days=i)).strftime('%Y-%m-%d') for i in range(0, (end_date - start_date).days + 1, 30)},
                tooltip={"placement": "bottom", "always_visible": True}
            ), width=6)
        ]),
        html.Div(id='graphs')
    ]
)

@app.callback(
    [Output('title', 'children'),
     Output('graphs', 'children')],
    [Input('city-dropdown', 'value'),
     Input('date-slider', 'value')]
)
def update_dashboard(selected_cities, date_range):
    start_date_range = start_date + pd.Timedelta(days=date_range[0])
    end_date_range = start_date + pd.Timedelta(days=date_range[1])

    filtered_df = df_weather[
        (df_weather['city'].isin(selected_cities)) &
        (df_weather['date'] >= start_date_range) &
        (df_weather['date'] <= end_date_range)
    ]

    # Create the title
    date_range_str = f"{start_date_range.strftime('%Y-%m-%d')} to {end_date_range.strftime('%Y-%m-%d')}"
    title = f"Temperature Dashboard: {', '.join(selected_cities)} ({date_range_str})"

    # Create an interactive line plot for average temperatures
    fig_avg_temp_BCH = px.line(filtered_df, x='date', y='avg_temp_c', color='city', 
                  title='Average Temperatures in Selected Cities', 
                  labels={'date': 'Date', 'avg_temp_c': 'Average Temperature (°C)', 'city': 'Location'},
                  template='plotly_dark')
    graph_avg_temp = dcc.Graph(figure=fig_avg_temp_BCH)

    # Create an interactive line plot for max temperatures
    fig_max_temp_BCH = px.line(filtered_df, x='date', y='max_temp_c', color='city', 
                  title='Max Temperatures in Selected Cities', 
                  labels={'date': 'Date', 'max_temp_c': 'Max Temperature (°C)', 'city': 'Location'},
                  template='plotly_dark')
    graph_max_temp = dcc.Graph(figure=fig_max_temp_BCH)

    # Create tables for the datapoints
    table_max_temp = dash_table.DataTable(
        columns=[
            {'name': 'Date', 'id': 'date'},
            {'name': 'City', 'id': 'city'},
            {'name': 'Max Temperature (°C)', 'id': 'max_temp_c'},
            {'name': 'Weather', 'id': 'condition_text'},
            {'name': 'Icon', 'id': 'condition_icon', 'presentation': 'markdown'}
        ],
        data=filtered_df[['date', 'city', 'max_temp_c', 'condition_text', 'condition_icon']].to_dict('records'),
        style_table={'overflowX': 'auto', 'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},
        style_cell={'textAlign': 'left', 'padding': '5px', 'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},
        style_header={'backgroundColor': '#1f2c39', 'fontWeight': 'bold', 'color': '#ecf0f1'},
        markdown_options={"html": True}
    )

    table_avg_temp = dash_table.DataTable(
        columns=[
            {'name': 'Date', 'id': 'date'},
            {'name': 'City', 'id': 'city'},
            {'name': 'Average Temperature (°C)', 'id': 'avg_temp_c'},
            {'name': 'Weather', 'id': 'condition_text'},
            {'name': 'Icon', 'id': 'condition_icon', 'presentation': 'markdown'}
        ],
        data=filtered_df[['date', 'city', 'avg_temp_c', 'condition_text', 'condition_icon']].to_dict('records'),
        style_table={'overflowX': 'auto', 'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},
        style_cell={'textAlign': 'left', 'padding': '5px', 'backgroundColor': '#2c3e50', 'color': '#ecf0f1'},
        style_header={'backgroundColor': '#1f2c39', 'fontWeight': 'bold', 'color': '#ecf0f1'},
        markdown_options={"html": True}
    )

    # Average temperature per city on map
    df_avg_temp = filtered_df.groupby(['city', 'lat', 'lon']).agg({'avg_temp_c': 'mean'}).reset_index()

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

    # Filter for Germany
    df_germany = filtered_df[filtered_df['country'] == 'Germany']
    df_avg_temp_choropleth = df_germany.groupby(['city']).agg({'avg_temp_c': 'mean'}).reset_index()

    # Create a choropleth map for Germany
    fig_map_choropleth = px.choropleth(df_avg_temp_choropleth, 
                        locations='city',
                        locationmode='geojson-id',
                        color='avg_temp_c',
                        hover_name='city',
                        geojson='https://raw.githubusercontent.com/deldersveld/topojson/master/countries/germany/germany-splitted.json',
                        featureidkey='properties.name',
                        color_continuous_scale='Viridis',
                        title='Average Temperature in Germany')
    fig_map_choropleth.update_geos(fitbounds="locations", visible=False)
    graph_choropleth_map = dcc.Graph(figure=fig_map_choropleth)
