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

# map_fig = px.scatter_mapbox(color_discrete_sequence=["fuchsia"], zoom=8,
#                             center={'lat':39, 'lon':-100})
map_fix = px
app.layout = html.Div([

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

    dcc.Graph(id='map_plot'),
    # dcc.Graph(id='elevation_plot'),

    # Hidden div inside the app that stores the track data in json format.
    html.Div(id='_track', style={'display': 'none'})
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
    print('Making map')
    print(json_df[:100])
    map_df = pd.read_json(json_df, orient='split') # convert_dates=True
    #fig = px.line(map_df, x="lon", y="lat")

    fig = px.scatter_mapbox(map_df, lat="lat", lon="lon", zoom=12,
                  mapbox_style="outdoors") #  config={'displayModeBar': False}
    min_max = map_df.loc[:, ['lat', 'lon']].describe().loc[['min','max']]
    print(min_max)

    fig.update_xaxes(range=min_max.lon)
    fig.update_yaxes(range=min_max.lat)
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

# @app.callback(Output('elevation_plot', 'figure'),
#             [Input('_track', 'children')], 
#             prevent_initial_call=True)
# def make_map(json_df):
#     """

#     """
#     map_df = pd.read_json(json_df, orient='split') # convert_dates=True
#     fig = px.line(map_df, x="lon", y="lat")
#     # fig = px.scatter_mapbox(color_discrete_sequence=["fuchsia"], zoom=8,
#     #                         center={'lat':39, 'lon':-100})
#     # fig.update_layout(mapbox_style="stamen-terrain", mapbox_zoom=4)
#     # if not isinstance(json_df, pd.DataFrame):
#     #     fig = px.scatter_mapbox(color_discrete_sequence=["fuchsia"], zoom=3, height=300)
#     # else:
#     #     map_df = pd.read_json(json_df, orient='split') # convert_dates=True
#     #     fig = px.scatter_mapbox(map_df, lat="lat", lon="lon", hover_data=["elevation_km", "vel_km_hr"],
#     #                     color_discrete_sequence=["fuchsia"], zoom=3, height=300)
#     # fig.update_layout(mapbox_style="open-street-map")
#     # fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
#     return fig

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