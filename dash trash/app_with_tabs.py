#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  5 17:33:17 2019

@author: mike
"""

import os
os.chdir('/home/mike/Analytics/NJ Transit/')
import summarize_tweets
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

""" Pull Data """
data, phrases = summarize_tweets.summarized()
testing = summarize_tweets.reason_counts(data, phrases, 5)


""" Tabs """
app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Tabs(id="tabs", value='tab-main', children=[
        dcc.Tab(label='Main', value='tab-main'),
        dcc.Tab(label='Donate', value='tab-donate'),
    ]),
    html.Div(id='tabs-content')
])


""" Content """
@app.callback(Output('tabs-content', 'children'),
              [Input('tabs', 'value')])
def render_content(tab):
    
    ### Main Tab
    if tab == 'tab-main':
        return html.Div([
            html.Div([
                html.H1('NJ Transit Delays & Cancellations', style={'font-family': 'Dosis'})
            ]), 
            
            ### Inputs ###
            html.Div([
                html.P('Select Train Lines:', style={'font-family': 'Dosis'}),
                dcc.Dropdown(
                    id = 'line-selection', 
                    options=[
                        {'label': 'RVL', 'value': 'RVL'},
                        {'label': 'NJCL', 'value': 'NJCL'},
                        {'label': 'NEC', 'value': 'NEC'}
                    ],
                    multi = True,
                    value = None, 
                    style = {'width' : 400}
                ),
                html.Br(), 
                html.P('Select Chart Type:', style={'font-family': 'Dosis'}),
                dcc.RadioItems(
                    options=[
                        {'label': 'Summary', 'value': 'hist'},
                        {'label': 'Trend', 'value': 'trend'}
                    ],
                    value = 'hist', 
                    style = {'width' : 400}
                ), 
                html.Br(), 
                ]), 
    
    
            ### Graph ###
            html.Div([
                html.H3('Graph', style={'font-family': 'Dosis'}), 
                dcc.Graph(
                    figure=go.Figure(
                        data=[
                            go.Bar(
                                x=testing['reason_str'], 
                                y=testing['count'],
                                name='All Failures',
                                marker=go.bar.Marker(
                                    color='rgb(55, 83, 109)'
                                )
                            ),
                            go.Bar(
                                x=testing['reason_str'], 
                                y=testing['count'],
                                name='Same Thing...Filler for now Failures',
                                marker=go.bar.Marker(
                                    color='rgb(128, 128, 128)'
                                )
                            ),
                        ],
                        layout=go.Layout(
                            title='Delays and Cancellations',
                            showlegend=True, 
                            legend=go.layout.Legend(
                                x=0,
                                y=1.0
                            ),
                            margin=go.layout.Margin(l=40, r=0, t=40, b=30)
                        )
                    ),
                    style={'height': 300, 'width': 800},
                    id='my-graph'
                    ), 
                    
                    
            ])
        ])
    
    
    
    
    ### Donate Tab
    elif tab == 'tab-donate':
        return html.Div([
            html.H3('Donation Page'), 
            html.P('Like what you see? Feel free to donate using this link!')
        ])


""" Run App """
if __name__ == '__main__':
    app.run_server(debug=True)