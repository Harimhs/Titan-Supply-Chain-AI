#!/usr/bin/env python3
"""
TITAN Supply Chain Dashboard
3D Interactive Global Supply Chain Visualization
"""

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime
import asyncio

from src.dashboard.components.globe_map import create_globe_figure
from src.dashboard.components.chat_panel import create_chat_panel
from src.dashboard.utils.data_loader import DashboardDataLoader
from src.orchestrator.state_graph import StateGraphOrchestrator


# ============================================================================
# INITIALIZATION
# ============================================================================

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],  # Dark theme
    suppress_callback_exceptions=True,
    title="TITAN Supply Chain AI"
)

# Load data
data_loader = DashboardDataLoader()
orchestrator = StateGraphOrchestrator()

# Global state
app_state = {
    'selected_disaster': None,
    'zoom_level': 1.0,
    'chat_history': []
}


# ============================================================================
# LAYOUT
# ============================================================================

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🌍 TITAN Supply Chain AI", 
                   className="text-center text-primary mb-0"),
            html.P("Real-time Global Supply Chain Intelligence",
                  className="text-center text-muted mb-3")
        ])
    ]),
    
    # Main Content
    dbc.Row([
        # Left Panel: 3D Globe
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("🗺️ Global Supply Chain Network", className="mb-0"),
                    html.Small("Interactive 3D Visualization", className="text-muted")
                ]),
                dbc.CardBody([
                    dcc.Graph(
                        id='globe-map',
                        figure=create_globe_figure(data_loader),
                        style={'height': '70vh'},
                        config={'displayModeBar': True, 'scrollZoom': True}
                    ),
                    
                    # Controls
                    dbc.Row([
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button("🏭 Factories", id="btn-factories", 
                                          color="success", outline=True, size="sm"),
                                dbc.Button("⚓ Ports", id="btn-ports", 
                                          color="info", outline=True, size="sm"),
                                dbc.Button("🏢 Warehouses", id="btn-warehouses", 
                                          color="warning", outline=True, size="sm"),
                                dbc.Button("🔥 Disasters", id="btn-disasters", 
                                          color="danger", outline=True, size="sm"),
                            ], className="w-100")
                        ], width=12)
                    ], className="mt-3")
                ])
            ], className="h-100")
        ], width=8),
        
        # Right Panel: Chat & Stats
        dbc.Col([
            # Chat Panel
            dbc.Card([
                dbc.CardHeader([
                    html.H5("💬 AI Assistant", className="mb-0"),
                    html.Small("Ask about supply chain", className="text-muted")
                ]),
                dbc.CardBody([
                    # Chat messages
                    html.Div(id='chat-messages', 
                            style={
                                'height': '40vh',
                                'overflowY': 'scroll',
                                'padding': '10px',
                                'backgroundColor': '#1a1a1a',
                                'borderRadius': '5px',
                                'marginBottom': '10px'
                            },
                            children=[
                                html.P("👋 Hello! Ask me about supply chains, disasters, or routes.",
                                      className="text-muted")
                            ]),
                    
                    # Input
                    dbc.InputGroup([
                        dbc.Input(
                            id='chat-input',
                            placeholder="e.g., Impact of Taiwan earthquake?",
                            type="text"
                        ),
                        dbc.Button("Send", id='chat-send', color="primary")
                    ])
                ])
            ], className="mb-3"),
            
            # Stats Panel
            dbc.Card([
                dbc.CardHeader(html.H5("📊 Network Statistics", className="mb-0")),
                dbc.CardBody([
                    html.Div(id='stats-panel', children=[
                        dbc.Row([
                            dbc.Col([
                                html.H4(f"{data_loader.stats['factories']:,}", 
                                       className="text-success mb-0"),
                                html.Small("Factories", className="text-muted")
                            ], width=6),
                            dbc.Col([
                                html.H4(f"{data_loader.stats['ports']:,}", 
                                       className="text-info mb-0"),
                                html.Small("Ports", className="text-muted")
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.H4(f"{data_loader.stats['warehouses']:,}", 
                                       className="text-warning mb-0"),
                                html.Small("Warehouses", className="text-muted")
                            ], width=6),
                            dbc.Col([
                                html.H4(f"{data_loader.stats['disasters']}", 
                                       className="text-danger mb-0"),
                                html.Small("Disasters", className="text-muted")
                            ], width=6)
                        ], className="mb-3"),
                        html.Hr(),
                        html.P(f"Last updated: {datetime.now().strftime('%H:%M:%S')}", 
                              className="text-muted small mb-0")
                    ])
                ])
            ])
        ], width=4)
    ], className="g-3"),
    
    # Hidden stores for state
    dcc.Store(id='map-state', data={'view': 'all'}),
    dcc.Interval(id='update-interval', interval=5000, n_intervals=0)  # 5s refresh
    
], fluid=True, className="p-4")


# ============================================================================
# CALLBACKS
# ============================================================================

@app.callback(
    Output('chat-messages', 'children'),
    Input('chat-send', 'n_clicks'),
    State('chat-input', 'value'),
    State('chat-messages', 'children'),
    prevent_initial_call=True
)
def handle_chat(n_clicks, message, current_messages):
    """Handle chat messages"""
    if not message:
        return current_messages
    
    # Add user message
    user_msg = html.Div([
        html.Strong("👤 You: ", className="text-primary"),
        html.Span(message)
    ], className="mb-2")
    current_messages.append(user_msg)
    
    # Get AI response (sync wrapper for async)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(orchestrator.run(message))
    loop.close()
    
    # Add AI response
    ai_msg = html.Div([
        html.Strong("🤖 TITAN: ", className="text-success"),
        html.Span(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer']),
        html.Br(),
        html.Small(f"⏱️ {result['processing_time']['total']:.1f}s | "
                  f"📊 {result['intent']}", 
                  className="text-muted")
    ], className="mb-3", style={'backgroundColor': '#2a2a2a', 'padding': '10px', 'borderRadius': '5px'})
    current_messages.append(ai_msg)
    
    return current_messages


@app.callback(
    Output('globe-map', 'figure'),
    [Input('btn-factories', 'n_clicks'),
     Input('btn-ports', 'n_clicks'),
     Input('btn-warehouses', 'n_clicks'),
     Input('btn-disasters', 'n_clicks')],
    prevent_initial_call=True
)
def update_map_view(factories_click, ports_click, warehouses_click, disasters_click):
    """Update map based on button clicks"""
    ctx = callback_context
    if not ctx.triggered:
        return create_globe_figure(data_loader)
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Update view based on button
    view_filter = {
        'btn-factories': 'factories',
        'btn-ports': 'ports',
        'btn-warehouses': 'warehouses',
        'btn-disasters': 'disasters'
    }.get(button_id, 'all')
    
    return create_globe_figure(data_loader, view=view_filter)


# ============================================================================
# RUN
# ============================================================================

if __name__ == '__main__':
    print("🚀 Starting TITAN Dashboard...")
    print("📡 Loading data from Neo4j...")
    print(f"✅ Loaded {data_loader.stats['factories']:,} factories")
    print(f"✅ Loaded {data_loader.stats['ports']:,} ports")
    print(f"✅ Loaded {data_loader.stats['warehouses']:,} warehouses")
    print(f"✅ Loaded {data_loader.stats['disasters']} disasters")
    print("\n🌐 Dashboard running at: http://127.0.0.1:8050")
    print("Press Ctrl+C to stop\n")
    
    app.run_server(debug=True, host='127.0.0.1', port=8050)
