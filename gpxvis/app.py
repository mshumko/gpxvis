import json
import base64
import io
import pathlib

import gpxpy
import numpy as np
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

Re_km = 6371

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Load the mapbox token if it exists.
if pathlib.Path('mapbox_token').exists():
    with open('mapbox_token') as f:
        mapbox_token = f.read()
    px.set_mapbox_access_token(mapbox_token)

int_map=px.scatter_mapbox(lat=[0], lon=[0], center={'lat':39, 'lon':-100}, zoom=3)
int_map.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0},
    )
int_evel_fig=px.line(x=[0], y=[0], 
    labels={'x':'distance [km]', 'y':'elevation [km]'})
int_evel_fig.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0},
    )

app.layout = html.Div(children=[

    html.H1('gpxvis: a gpx file visualizer', style={"textAlign":"center"}),
        
    dcc.Upload(
        id='upload-gpx',
        children=html.Div(children=[
            'Drag and Drop, ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),

    html.Div([
    dcc.Graph(id='map_plot', figure=int_map, style={'height':'48vh'}),
    dcc.Graph(id='elevation_plot', style={'height':'30vh'}, figure=int_evel_fig),
    ]),

    # Hidden div inside the app that stores the track data in json format.
    html.Div(id='_track', style={'display': 'none'}),

    # Hidden div inside the app that stores the user's last mouse position
    # in the distance vs elevation plot.
    html.Div(id='hover_data', style={'display': 'none'}),
])

@app.callback(Output('_track', 'children'),
              [Input('upload-gpx', 'contents')],
              # prevent_initial_call or dash.exceptions.PreventUpdate works
              prevent_initial_call=True)
def load_gpx(contents):
    """
    Load the gpx segment coordinate points, calculate the velocity, and save to
    pd.DataFrame. 
    """
    # if contents is None:
    #     return PreventUpdate
    if isinstance(contents, pathlib.Path):
        with open(contents, 'r') as f:
            gpx_df = parse_gpx(gpxpy.parse(f))
    elif isinstance(contents, str):
        content_string = contents.split(',')[1]
        decoded = base64.b64decode(content_string)
        gpx = gpxpy.parse(io.StringIO(decoded.decode('utf-8')))
        gpx_df = parse_gpx(gpx)
    else:
        raise TypeError('Unknown contens type.')
    return gpx_df.to_json(date_format='iso', orient='split')

def parse_gpx(gpx_obj):
    """
    Parse the gpx segment coordinate points, calculate the velocity, and save to
    pd.DataFrame. 
    """
    for track in gpx_obj.tracks:
        for segment in track.segments:
            n = len(segment.points)
            gpx_df = pd.DataFrame(
                data={
                    'time':np.zeros(n, dtype=object),
                    'lat':np.zeros(n, dtype=float),
                    'lon':np.zeros(n, dtype=float),
                    'elevation_km':np.zeros(n, dtype=float)
                    }
                )
            for row, point in enumerate(segment.points):
                point_data = [point.time.replace(tzinfo=None), point.latitude, 
                                point.longitude, point.elevation/1000]
                gpx_df.loc[row, ['time', 'lat', 'lon', 'elevation_km']] = point_data

    # Calculate the speed
    gpx_df['time'] = pd.to_datetime(gpx_df['time'])
    gpx_df['dt'] = gpx_df['time'].diff(1).dt.total_seconds()
    gpx_df.loc[1:, 'dx'] = haversine(
        gpx_df.loc[1:, ['lat', 'lon', 'elevation_km']], 
        gpx_df.loc[:gpx_df.shape[0]-2, ['lat', 'lon', 'elevation_km']]
                        )
    gpx_df.loc[1:, 'distance'] = np.cumsum(gpx_df.loc[1:, 'dx'])
    gpx_df['vel_km_hr'] = gpx_df['dx']/(gpx_df['dt']/3600)
    gpx_df = gpx_df.loc[1:, :]
    gpx_df.set_index('time', inplace=True)
    return gpx_df

@app.callback(Output('map_plot', 'figure'),
            [Input('_track', 'children')], 
            prevent_initial_call=True)
def make_map(json_df):
    """

    """
    fig=px.scatter_mapbox(lat=[0], lon=[0], center={'lat':39, 'lon':-100}, zoom=3)
    map_df = pd.read_json(json_df, orient='split') # convert_dates=True

    fig = px.scatter_mapbox(map_df, lat="lat", lon="lon", zoom=13,
                  mapbox_style="outdoors") #  config={'displayModeBar': False}
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        )
    return fig

@app.callback(Output('elevation_plot', 'figure'),
            [Input('_track', 'children')], 
            prevent_initial_call=True)
def make_elev_plot(json_df):
    """

    """
    fig=px.scatter_mapbox(lat=[0], lon=[0], center={'lat':39, 'lon':-100}, zoom=3)
    map_df = pd.read_json(json_df, orient='split') # convert_dates=True

    fig = px.area(map_df, x='distance', y='elevation_km', 
        range_y=[map_df.loc[:, 'elevation_km'].min(), 1.1*map_df.loc[:, 'elevation_km'].max()])
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        )
    return fig

@app.callback(
    Output('hover_data', 'children'),
    [Input('elevation_plot', 'hoverData')])
def display_hover_data(hoverData):
    print(json.dumps(hoverData, indent=2))
    return json.dumps(hoverData, indent=2)

def haversine(x1, x2):
    """
    Implementation of the haversine equation to calculate total distance
    on a globe at an average elevation. x1 and x2 are arrays of shape 
    (N_points, 3) with columns corresponding to latitude, longitude, and
    elevation. Units of latitude and longitude are degrees and elevation in
    kilometers.
    """
    x1 = np.asarray(x1)
    x2 = np.asarray(x2)
    R = (Re_km+(x1[:, 2]+x2[:, 2])/2) # mean altitude
    # The angle between the each lat-lon point pairs.
    s = 2*np.arcsin(np.sqrt( 
                    np.sin(np.deg2rad(x1[:, 0]-x2[:, 0])/2)**2 + 
                    np.cos(np.deg2rad(x1[:, 0]))*np.cos(np.deg2rad(x2[:, 0]))*\
                    np.sin(np.deg2rad(x1[:, 1]-x2[:, 1])/2)**2 
                    ))
    return R*s

if __name__ == '__main__':
    app.run_server(debug=True)