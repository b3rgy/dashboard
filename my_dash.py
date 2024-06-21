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

# Define the start and end date for the range slider
start_date = df['date'].min()
end_date = df['date'].max()

# Instantiate/load the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Define the layout of the app
app.layout = html.Div(children=[
    html.H1(id='title', children='Temperature Dashboard'),
    dcc.Dropdown(
        id='city-dropdown',
        options=[{'label': city, 'value': city} for city in df['city'].unique()],
        value=['Berlin', 'Cagliari', 'Hamburg'],
        multi=True
    ),
    dcc.RangeSlider(
        id='date-slider',
        min=0,
        max=(end_date - start_date).days,
        value=[0, (end_date - start_date).days],
        marks={i: (start_date + pd.Timedelta(days=i)).strftime('%Y-%m-%d') for i in range(0, (end_date - start_date).days + 1, 30)}
    ),
    html.Div(id='graphs')
])

@app.callback(
    [Output('title', 'children'),
     Output('graphs', 'children')],
    [Input('city-dropdown', 'value'),
     Input('date-slider', 'value')]
)
def update_dashboard(selected_cities, date_range):
    start_date_range = start_date + pd.Timedelta(days=date_range[0])
    end_date_range = start_date + pd.Timedelta(days=date_range[1])

    filtered_df = df[
        (df['city'].isin(selected_cities)) &
        (df['date'] >= start_date_range) &
        (df['date'] <= end_date_range)
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
            {'name': 'Max Temperature (°C)', 'id': 'max_temp_c'}
        ],
        data=filtered_df[['date', 'city', 'max_temp_c']].to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': 'gray', 'fontWeight': 'bold'}
    )

    table_avg_temp = dash_table.DataTable(
        columns=[
            {'name': 'Date', 'id': 'date'},
            {'name': 'City', 'id': 'city'},
            {'name': 'Average Temperature (°C)', 'id': 'avg_temp_c'}
        ],
        data=filtered_df[['date', 'city', 'avg_temp_c']].to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '5px'},
        style_header={'backgroundColor': 'gray', 'fontWeight': 'bold'}
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

    # Aggregate the average temperature by country
    df_avg_temp_choropleth = filtered_df.groupby(['country']).agg({'avg_temp_c': 'mean'}).reset_index()

    # Create a choropleth map
    fig_map_choropleth = px.choropleth(df_avg_temp_choropleth, 
                        locations='country',
                        locationmode='country names',
                        color='avg_temp_c',
                        hover_name='country',
                        color_continuous_scale='Viridis',
                        title='Average Temperature in European Countries')
    graph_choropleth_map = dcc.Graph(figure=fig_map_choropleth)

    return title, [
        html.Div([
            dbc.Row([
                dbc.Col(graph_max_temp, width=8),
                dbc.Col(table_max_temp, width=4)
            ]),
            dbc.Row([
                dbc.Col(graph_avg_temp, width=8),
                dbc.Col(table_avg_temp, width=4)
            ]),
            graph_map,
            graph_choropleth_map
        ])
    ]

if __name__ == '__main__':
    app.run_server(debug=True)
