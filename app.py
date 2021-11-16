import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import requests
import json
import pandas as pd
import datetime as dt
import plotly.express as px
import plotly.graph_objects as go


#######################################
########DATAFRAME######################
#######################################
def earthquake(path, starttime, endtime, alert):
    paramss = {"format": "geojson", "starttime": starttime, "endtime": endtime, "alertlevel": alert}
    data = requests.get(path, params = paramss)
    data = json.loads(data.text)
    return data

path = r"https://earthquake.usgs.gov/fdsnws/event/1/query?"
green = earthquake(path, '2010-01-01', '2021-10-1', 'green')
yellow = earthquake(path, '2010-01-01', '2021-10-1', 'yellow')
orange = earthquake(path, '2010-01-01', '2021-10-1', 'orange')
red = earthquake(path, '2010-01-01', '2021-10-1', 'red')

# Convert the JSON to Pandas dataframe
df_green = pd.json_normalize(green['features'])
df_yellow = pd.json_normalize(yellow['features'])
df_orange = pd.json_normalize(orange['features'])
df_red = pd.json_normalize(red['features'])

df = pd.concat([df_green, df_yellow, df_orange, df_red])

def refactor_date(row):
    actual_value = row['properties.time']
    actual_time = dt.datetime.fromtimestamp(actual_value // 1000.0)
    row['properties.time'] = actual_time
    return row

df = df.apply(refactor_date, axis='columns')

df2 = df[['id', 'properties.mag', 'properties.place', 'properties.time', 'properties.detail', \
'properties.felt', 'properties.cdi', 'properties.mmi', 'properties.alert', 'properties.tsunami', \
'properties.sig', 'properties.net', 'properties.dmin', 'properties.type', 'geometry.coordinates']]
df2.set_axis(['id', 'magnitude', 'location', 'time', 'detail', 'felt', 'cdi', 'mmi', 'alert', 'tsunami', 'sig', 'net', 'dmin', 'type', 'coordinates'], axis=1, inplace=True)
df2.head()

df2[['latitud', 'longitud', 'depth']] = pd.DataFrame(df2.coordinates.tolist(), index= df2.index) 

# Filling Missing Values
df2.felt = df2.felt.fillna(0)
df2.cdi = df2.cdi.fillna(0)
df2.dmin = df2.dmin.fillna(df2.dmin.median())
df2.location = df2.location.fillna('Unknown')
green_mag = df2.magnitude[df2.alert == 'green']
df2.magnitude = df2.magnitude.fillna(green_mag.mean())

#######################################
############ Dash App #################
#######################################

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([
        html.H1('Earthquake Dash App'),
        html.Div([
            dcc.Link('Page 1', href='/page-1'),
            dcc.Link('Page 2', href='/page-2'),
            dcc.Link('Page 3', href='/page-3')
        ], className='nav_div')
    ], className='nav'),
    html.Div(id='page-content'),
    html.Footer([
        html.P('© 2021 Fernando Sirias / David Mairena'),
        html.Div([
            html.P('Data Source: '),
            html.A('USGS', href='https://earthquake.usgs.gov/fdsnws/event/1/?ref=springboard', target='_blank')
        ], className='source')
    ])
], className='content_container')

default_layout= html.Div([
    html.Div([
        html.H2('PLEASE SELECT A PAGE'),
        html.Img(src='https://media0.giphy.com/media/xT1R9JFTKhIpOYBvos/giphy.gif?cid=790b761186ce2b415be65a3c705bea87481b3dad7a3b6985&rid=giphy.gif&ct=g')
    ], className='default_container')
], className='default_layout')

##################################### First Page ######################################### 
first_page_layout = html.Div([
        html.H1('Earthquakes from 2010 to 2021'),
    html.Div([
        html.Div(html.Label([
            'Select an alert to filter:',
            dcc.Dropdown(
            id='page-1-dropdown', value='all', clearable=False,
            options=[
                {'label': 'Green', 'value': 'green'}, 
                {'label': 'Yellow', 'value' : 'yellow'},
                {'label': 'Orange', 'value': 'orange'},
                {'label': 'Red', 'value': 'red'},
                {'label': 'All', 'value': 'all'}]
            )], className='filter_text'), className='inline'),
            html.Div([
                html.Label([
                    'Tsunami alert:',
                    dcc.RadioItems(
                        id='tsunami_alert',
                        value='default',
                        options=[
                            {'label': 'Default', 'value': 'default'},
                            {'label': 'Yes', 'value': 0},
                            {'label': 'No', 'value': 1}
                        ]
                    )
                ])
            ], className='inline'),
            html.Div([
                html.Label([
                    'Select a year to filter:',
                    dcc.Slider(
                        id='slider',
                        min=2010,
                        max=2022,
                        value=2022,
                        marks={
                            2010: {'label': '2010', 'style': {'color': 'white'}}, 2011: {'label': '2011', 'style': {'color': 'white'}}, 2012: {'label': '2012', 'style': {'color': 'white'}},
                            2013: {'label': '2013', 'style': {'color': 'white'}}, 2014: {'label': '2014', 'style': {'color': 'white'}}, 2015: {'label': '2015', 'style': {'color': 'white'}},
                            2016: {'label': '2016', 'style': {'color': 'white'}}, 2017: {'label': '2017', 'style': {'color': 'white'}},
                            2018: {'label': '2018', 'style': {'color': 'white'}}, 2019: {'label': '2019', 'style': {'color': 'white'}}, 2020: {'label': '2020', 'style': {'color': 'white'}},
                            2021: {'label': '2021', 'style': {'color': 'white'}}, 2022: {'label': '2022', 'style': {'color': 'white'}}
                        }
                    )
                ])
            ], className='inline'),
    ], className='filter_container'),
        dcc.Graph(id='scatterplot', figure={}),
    html.Div([
        dcc.Graph(id='barplot', figure={})
    ])
], className='content')

@app.callback(Output('scatterplot', 'figure'),
              [Input('page-1-dropdown', 'value')],
              Input('tsunami_alert', 'value'),
              Input('slider', 'value')
              )
def scatter_out(value1, value2, value3):
    if value1 == 'all':
        if value2 == 'default':
                fig = px.scatter(df2, x = 'time', y = 'magnitude', color='alert', size='cdi', color_discrete_sequence=['green', '#d6c800', '#fa9602', 'red'], hover_name='location')
                fig.update_layout(yaxis_range=[0,9], xaxis_range=[dt.datetime(2009,10,1), dt.datetime(value3, 3 if value3 == 2022 else 12, 30)])
                return fig
        else:
            temp = df2[df2.tsunami == value2]
            fig = px.scatter(temp, x = 'time', y = 'magnitude', color='alert', size='cdi', color_discrete_sequence=['green', '#d6c800', '#fa9602', 'red'], hover_name='location')
            fig.update_layout(yaxis_range=[0,9], xaxis_range=[dt.datetime(2009,10,1), dt.datetime(2022, 4, 1)])
            return fig
    else:
        if value2 == 'default':
            temp = df2[df2.alert == value1]
            fig = px.scatter(temp, x = 'time', y = 'magnitude', color='alert', size='cdi', color_discrete_sequence=[value1], hover_name='location')
            fig.update_layout(yaxis_range=[0,9], xaxis_range=[dt.datetime(2009,10,1), dt.datetime(2022, 4, 1)])
            return fig
        else:
            temp = df2[(df2.alert == value1) & (df2.tsunami == value2)]
            fig = px.scatter(temp, x = 'time', y = 'magnitude', color='alert', size='cdi', color_discrete_sequence=[value1], hover_name='location')
            fig.update_layout(yaxis_range=[0,9], xaxis_range=[dt.datetime(2009,10,1), dt.datetime(2022, 4, 1)])
            return fig


@app.callback(Output('barplot', 'figure'),
              [Input('page-1-dropdown', 'value')],
              Input('tsunami_alert', 'value'),
              Input('slider', 'value')
              )
def barplot_out(value1, value2, value3):
    if value1 == 'all':
        if value2 == 'default':
            df2_temp = df2.time.dt.year.value_counts().reset_index()
            fig = px.bar(df2_temp, x = 'index', y = 'time', labels={'x': 'Year', 'y': 'number of earthquakes'}, title='Amount of earthquakes registered by year')
            fig.update_layout(xaxis_range=[2009, value3])
            return fig
        else:
            temp = df2[df2.tsunami == value2]
            df2_temp = temp.time.dt.year.value_counts().reset_index()
            fig = px.bar(df2_temp, x = 'index', y = 'time', labels={'x': 'Year', 'y': 'number of earthquakes'}, title='Amount of earthquakes registered by year')
            fig.update_layout(xaxis_range=[2009, value3])
            return fig
    else:
        if value2 == 'default':
            temp = df2[df2.alert == value1]
            df2_temp = temp.time.dt.year.value_counts().reset_index()
            fig = px.bar(df2_temp, x = 'index', y = 'time', labels={'x': 'Year', 'y': 'number of earthquakes'}, title='Amount of earthquakes registered by year')
            fig.update_layout(xaxis_range=[2009, value3])
            return fig
        else:
            temp = df2[(df2.alert == value1) & (df2.tsunami == value2)]
            df2_temp = temp.time.dt.year.value_counts().reset_index()
            fig = px.bar(df2_temp, x = 'index', y = 'time', labels={'x': 'Year', 'y': 'number of earthquakes'}, title='Amount of earthquakes registered by year')
            fig.update_layout(xaxis_range=[2009, value3])
            return fig



#####################################Second Page######################################### 
second_page_layout = html.Div([
        html.H1('Earthquakes from 2010 to 2021'),
    html.Div([
        html.Div(html.Label([
            'Select an alert to filter the first plot:',
           dcc.Dropdown(
            id='page-2-dropdown', value='all', clearable=False,
                options=[
                    {'label': 'Green', 'value': 'green'}, 
                    {'label': 'Yellow', 'value' : 'yellow'},
                    {'label': 'Orange', 'value': 'orange'},
                    {'label': 'Red', 'value': 'red'},
                    {'label': 'All', 'value': 'all'}
                ]
            )],
            className='filter_text'), className='inline'),
            html.Div([
                html.Label([
                    'Select an alert to filter the second plot:',
                    dcc.RadioItems(
                        id='page-2-dropdown_strip', value='all',
                        options=[
                            {'label': 'Green', 'value': 'green'}, 
                            {'label': 'Yellow', 'value' : 'yellow'},
                            {'label': 'Orange', 'value': 'orange'},
                            {'label': 'Red', 'value': 'red'},
                            {'label': 'All', 'value': 'all'}
                        ]
                    )
                ])
            ], className='inline'),
            html.Div([
                html.Label([
                    'Sig factor (how significant the event is):',
                    dcc.Slider(
                        id='strip_slider',
                        value=0,
                        min = 0,
                        max = 2910,
                        updatemode = 'drag',
                        marks={0: {'label': '0', 'style': {'color': 'white'}},
                            100: {'label': '100', 'style': {'color': 'white'}}, 300: {'label': '300', 'style': {'color': 'white'}}, 500: {'label': '500', 'style': {'color': 'white'}},
                            700: {'label': '700', 'style': {'color': 'white'}}, 900: {'label': '900', 'style': {'color': 'white'}}, 1100: {'label': '1100', 'style': {'color': 'white'}},
                            1300: {'label': '1300', 'style': {'color': 'white'}}, 1500: {'label': '1500', 'style': {'color': 'white'}}, 1700: {'label': '1700', 'style': {'color': 'white'}},
                            1900: {'label': '1900', 'style': {'color': 'white'}}, 2100: {'label': '2100', 'style': {'color': 'white'}}, 2300: {'label': '2300', 'style': {'color': 'white'}},
                            2500: {'label': '2500', 'style': {'color': 'white'}}, 2700: {'label': '2700', 'style': {'color': 'white'}}, 2910: {'label': '2910', 'style': {'color': 'white'}},
                        }
                    )
                ])
            ])
     ], className='filter_container'),
        dcc.Graph(id='boxplot', figure={}),
    html.Div([
        dcc.Graph(id='stripplot', figure={})
    ]),
    html.Div([
        html.A('Nuclear Explosion?', id='notice', href='https://www.bbc.com/mundo/noticias-internacional-42309219', target='_blank')
    ], className='notice_container')
], className='content')


@app.callback(
    Output(component_id='boxplot', component_property='figure'),
    [Input(component_id='page-2-dropdown', component_property='value')]
)
def boxplot_out(value):
    if value == 'all':
        box =px.box(df2, x = 'alert', y = 'magnitude', color='alert', color_discrete_sequence=['green', '#d6c800', '#fa9602', 'red'], height=600)
        return box
    else:
        temp = df2[df2.alert == value]
        box = px.box(temp, x = 'alert', y = 'magnitude', color='alert', color_discrete_sequence=[str(value)], height=600)
        return box

@app.callback(
    Output(component_id='stripplot', component_property='figure'),
    [Input(component_id='page-2-dropdown_strip', component_property='value')],
    Input('strip_slider','value')
)
def strip_out(drop,slider):
    if drop == 'all':
        if slider == 0:
            fig = px.strip(df2, x = 'type', y = 'magnitude', color='type', height=530)
            fig.update_traces(marker=dict(size=12, line= dict(width=2, color='DarkSlateGrey')))
            fig.update_layout(yaxis_range=[0,9])
            return fig
        else:
            temp = df2[df2.sig <= slider]
            fig = px.strip(temp, x = 'type', y = 'magnitude', color='type', height=530)
            fig.update_traces(marker=dict(size=12, line= dict(width=2, color='DarkSlateGrey')))
            fig.update_layout(yaxis_range=[0,9])
            return fig
    else:
        if slider == 0:  
            temp = df2[df2.alert == drop]
            fig = px.strip(temp, x = 'type', y = 'magnitude', color='type', height=530)
            fig.update_traces(marker=dict(size=12, line= dict(width=2, color='DarkSlateGrey')))
            fig.update_layout(yaxis_range=[0,9])
            return fig
        else:
            temp = df2[(df2.alert == drop) & (df2.sig <= slider)]
            fig = px.strip(temp, x = 'type', y = 'magnitude', color='type', height=530)
            fig.update_traces(marker=dict(size=12, line= dict(width=2, color='DarkSlateGrey')))
            fig.update_layout(yaxis_range=[0,9])
            return fig


#####################################Third Page######################################### 
third_page_layout = html.Div([
        html.H1('Earthquake Map'),
        html.Div([
            html.Label([
                'Select an alert to filter:',
                dcc.RadioItems(
                id='page-3-radios',
                options=[
                    {'label': 'Green', 'value': 'green'}, 
                    {'label': 'Yellow', 'value' : 'yellow'},
                    {'label': 'Orange', 'value': 'orange'},
                    {'label': 'Red', 'value': 'red'},
                    {'label': 'All', 'value': 'all'}],
                value='all'
        )
        ]),
        html.Label([
                'Filter by Tsunami:',
                dcc.RadioItems(
                id='tsunami',
                options=[
                            {'label': 'Default', 'value': 'default'},
                            {'label': 'Yes', 'value': 0},
                            {'label': 'No', 'value': 1}
                        ],
                value='default'
        )
        ])
        ], className='filter_container'),
        dcc.Graph(id='page-3-content', figure={}),
    html.Div([
        dcc.Graph(id='page-3-content-2', figure={})
    ])
], className='content')

@app.callback(Output('page-3-content', 'figure'),
              [Input('page-3-radios', 'value')],
              Input('tsunami', 'value')
                )
def page_3_radios(value1, value2):
    if value1 == 'all':
        if value2 == 'default':
            return px.density_mapbox(df2, lat='longitud', lon='latitud', z='magnitude', radius=5,
                            center=dict(lat=7, lon=37), zoom=0.5,
                            mapbox_style="stamen-terrain", hover_name='location')
        else:
            temp = df2[df2.tsunami == value2]
            return px.density_mapbox(temp, lat='longitud', lon='latitud', z='magnitude', radius=7,
                            center=dict(lat=7, lon=37), zoom=0.5,
                            mapbox_style="stamen-terrain", hover_name='location')
    else:
        if value2 == 'default':
            temp = temp = df2[df2.alert == value1]
            return px.density_mapbox(temp, lat='longitud', lon='latitud', z='magnitude', radius=7,
                            center=dict(lat=7, lon=37), zoom=0.5,
                            mapbox_style="stamen-terrain", hover_name='location')
        else:
            temp = temp = df2[(df2.alert == value1) & (df2.tsunami == value2)]
            return px.density_mapbox(temp, lat='longitud', lon='latitud', z='magnitude', radius=7,
                            center=dict(lat=7, lon=37), zoom=0.5,
                            mapbox_style="stamen-terrain", hover_name='location')

@app.callback(Output('page-3-content-2', 'figure'),
              [Input('page-3-radios', 'value')],
              Input('tsunami', 'value')
              )
def page_3_second(value1, value2):
    if value1 == 'all':
        if value2 == 'default':
            fig = go.Figure(data=go.Scattergeo(
                lon = df2.latitud,
                lat = df2.longitud,
                text = df2.location,
                mode = 'markers',
                marker_color = df2.alert,
                ))
            fig.update_layout(
                autosize=False,
                margin=dict(
                    l=0,
                    r=0,
                    b=0,
                    t=0,
                    pad=90
                )
            )
            return fig
        else:
            temp = df2[df2.tsunami == value2]
            fig = go.Figure(data=go.Scattergeo(
                lon = temp.latitud,
                lat = temp.longitud,
                text = temp.location,
                mode = 'markers',
                marker_color = temp.alert
                ))
            return fig
    else:
        if value2 == 'default':
            temp = df2[df2.alert == value1]
            fig = go.Figure(data=go.Scattergeo(
                lon = temp.latitud,
                lat = temp.longitud,
                text = temp.location,
                mode = 'markers',
                marker_color = temp.alert
                ))
            return fig
        else:
            temp = df2[(df2.alert == value1) & (df2.tsunami == value2)]
            fig = go.Figure(data=go.Scattergeo(
                lon = temp.latitud,
                lat = temp.longitud,
                text = temp.location,
                mode = 'markers',
                marker_color = temp.alert
                ))
            return fig


# Update the index
@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/page-1':
        return first_page_layout
    elif pathname == '/page-2':
        return second_page_layout
    elif pathname == '/page-3':
        return third_page_layout
    else:
        return default_layout
    # You could also return a 404 "URL not found" page here


if __name__ == '__main__':
    app.run_server(debug=True)