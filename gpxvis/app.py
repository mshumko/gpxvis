import base64
import io

import gpxpy
import numpy as np
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px

Re_km = 6371

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Graph(id='map_plot'),

    dcc.Upload(
        id='upload-gpx',
        children=html.Div([
            'Drag and Drop, ',
            html.A('Select Files'), 'or', html.A('Load the example')
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
        multiple=True
    ),

    # Hidden div inside the app that stores the intermediate value
    html.Div(id='_track', style={'display': 'none'})
])

@app.callback(Output('_track', 'children'),
              [Input('upload-gpx', 'contents')],
              [State('upload-gpx', 'filename'),
               State('upload-gpx', 'last_modified')])
def load_gpx(contents, names, dates):
    """
    Load the gpx segment coordinate points, calculate the velocity, and save to
    pd.DataFrame. 
    """
    if contents is None:
        return ''
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    print(decoded)
    return ''
    #content_type, content_string = contents.split(',')
    # decoded = base64.b64decode(content_string)
    # file_path = io.StringIO(decoded.decode('utf-8'))

    # print(f'Opening {file_path}')
    # with open(file_path, 'r') as f:
    #     gpx = gpxpy.parse(f)
    #     for track in gpx.tracks:
    #         for segment in track.segments:
    #             n = len(segment.points)
    #             gpx_df = pd.DataFrame(
    #                 data={
    #                     'time':np.zeros(n, dtype=object),
    #                     'lat':np.zeros(n, dtype=float),
    #                     'lon':np.zeros(n, dtype=float),
    #                     'elevation_km':np.zeros(n, dtype=float)
    #                     }
    #                 )
    #             for row, point in enumerate(segment.points):
    #                 point_data = [point.time.replace(tzinfo=None), point.latitude, 
    #                               point.longitude, point.elevation/1000]
    #                 gpx_df.loc[row, ['time', 'lat', 'lon', 'elevation_km']] = point_data

    # # Calculate the speed
    # gpx_df['time'] = pd.to_datetime(gpx_df['time'])
    # gpx_df['dt'] = gpx_df['time'].diff(1).dt.total_seconds()
    # gpx_df.loc[1:, 'dx'] = haversine(
    #     gpx_df.loc[1:, ['lat', 'lon', 'elevation_km']], 
    #     gpx_df.loc[:gpx_df.shape[0]-2, ['lat', 'lon', 'elevation_km']]
    #                     )
    # gpx_df['vel_km_hr'] = gpx_df['dx']/(gpx_df['dt']/3600)
    # gpx_df = gpx_df.loc[1:, :]
    # gpx_df.set_index('time', inplace=True)
    # print(gpx_df)
    #return gpx_df

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