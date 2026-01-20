#!/usr/bin/env python3
"""
TITAN Supply Chain Dashboard - Simplified Working Version
"""

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import sys
from pathlib import Path

# Add to path
sys.path.append(str(Path(__file__).parent))

from src.orchestrator.state_graph import StateGraphOrchestrator
from src.simulation.god_mode import GodMode

# Initialize
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.CYBORG],
    suppress_callback_exceptions=True,
    title="TITAN Supply Chain AI"
)

orchestrator = StateGraphOrchestrator()
god_mode = GodMode()

# Layout
app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🌍 TITAN Supply Chain AI", className="text-center mb-0", 
                   style={'color': '#00d9ff'}),
            html.P("Real-time Global Supply Chain Intelligence with DCBA", 
                  className="text-center text-muted mb-3")
        ])
    ], className="mt-4"),
    
    html.Hr(),
    
    # Main Content
    dbc.Row([
        # Left Panel: Chat Interface
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("💬 AI Assistant", className="mb-0"),
                    html.Small("Ask about supply chains, cascades, or disasters", 
                             className="text-muted")
                ]),
                dbc.CardBody([
                    # Chat messages
                    html.Div(
                        id='chat-messages',
                        style={
                            'height': '50vh',
                            'overflowY': 'scroll',
                            'padding': '15px',
                            'backgroundColor': '#1a1a1a',
                            'borderRadius': '8px',
                            'marginBottom': '15px',
                            'border': '1px solid #333'
                        },
                        children=[
                            html.Div([
                                html.Strong("🤖 TITAN: ", style={'color': '#00d9ff'}),
                                html.Span("Hello! Ask me about supply chain disruptions, "
                                        "cascade impacts, or try God Mode below!",
                                        style={'color': '#bbb'})
                            ])
                        ]
                    ),
                    
                    # Input
                    dbc.InputGroup([
                        dbc.Input(
                            id='chat-input',
                            placeholder="e.g., What happens if FAC-00042 fails?",
                            type="text",
                            style={'backgroundColor': '#2a2a2a', 'color': '#fff', 'border': '1px solid #444'}
                        ),
                        dbc.Button("Send", id='chat-send', color="primary", n_clicks=0)
                    ]),
                    
                    # Loading indicator
                    dbc.Spinner(html.Div(id='loading-output'), color="primary", size="sm")
                ])
            ])
        ], width=7),
        
        # Right Panel: God Mode + Stats
        dbc.Col([
            # God Mode Panel
            dbc.Card([
                dbc.CardHeader([
                    html.H4("🎮 God Mode", className="mb-0"),
                    html.Small("Disable nodes & simulate disasters", className="text-muted")
                ]),
                dbc.CardBody([
                    html.Label("Node ID to Disable:", className="mb-2"),
                    dbc.InputGroup([
                        dbc.Input(
                            id='disable-input',
                            placeholder="e.g., FAC-00042",
                            type="text",
                            style={'backgroundColor': '#2a2a2a', 'color': '#fff'}
                        ),
                        dbc.Button("Disable", id='disable-button', 
                                 color="danger", outline=True, n_clicks=0)
                    ], className="mb-3"),
                    
                    dbc.Button("🔄 Reset All Nodes", id='reset-button', 
                             color="warning", outline=True, className="w-100 mb-3", n_clicks=0),
                    
                    html.Hr(),
                    
                    html.Div(id='god-output', style={
                        'padding': '10px',
                        'backgroundColor': '#2a2a2a',
                        'borderRadius': '5px',
                        'minHeight': '100px',
                        'color': '#bbb'
                    }, children="Ready for action...")
                ])
            ], className="mb-3"),
            
            # Stats Panel
            dbc.Card([
                dbc.CardHeader(html.H5("📊 System Stats", className="mb-0")),
                dbc.CardBody([
                    html.Div(id='stats-panel', children=[
                        html.P("⚡ System: Online", className="mb-2", style={'color': '#0f0'}),
                        html.P("🔧 DCBA Engine: Active", className="mb-2"),
                        html.P("🗄️ Neo4j: Connected", className="mb-2"),
                        html.P("💾 ChromaDB: Ready", className="mb-2"),
                        html.Hr(),
                        html.Small("TITAN v1.0 - Dynamic Context Budget Allocator", 
                                 className="text-muted")
                    ])
                ])
            ])
        ], width=5)
    ], className="g-3")
    
], fluid=True, className="p-4", style={'backgroundColor': '#0a0a0a', 'minHeight': '100vh'})


# Callbacks
@app.callback(
    [Output('chat-messages', 'children'),
     Output('chat-input', 'value'),
     Output('loading-output', 'children')],
    Input('chat-send', 'n_clicks'),
    State('chat-input', 'value'),
    State('chat-messages', 'children'),
    prevent_initial_call=True
)
def handle_chat(n_clicks, message, current_messages):
    """Handle chat messages"""
    if not message or not message.strip():
        return current_messages, "", ""
    
    # Add user message
    user_msg = html.Div([
        html.Strong("👤 You: ", style={'color': '#4CAF50'}),
        html.Span(message, style={'color': '#ddd'})
    ], className="mb-3", style={'padding': '8px', 'backgroundColor': '#1a2a1a', 'borderRadius': '5px'})
    current_messages.append(user_msg)
    
    try:
        # Get AI response
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(orchestrator.run(message))
        loop.close()
        
        # Format response
        answer = result['answer'][:800] + "..." if len(result['answer']) > 800 else result['answer']
        
        # Add AI response with details
        ai_msg = html.Div([
            html.Strong("🤖 TITAN: ", style={'color': '#00d9ff'}),
            html.Span(answer, style={'color': '#ddd'}),
            html.Br(),
            html.Hr(style={'margin': '8px 0', 'opacity': '0.3'}),
            html.Small([
                f"⏱️ {result['processing_time']['total']:.2f}s | ",
                f"📊 Intent: {result['intent']} | ",
                f"🎯 Confidence: {result['confidence']:.0%}"
            ], style={'color': '#888'}),
            html.Br(),
            html.Small([
                f"💰 Allocation: GraphRAG={result['allocation'].get('graph_rag', 0)} | ",
                f"VectorRAG={result['allocation'].get('vector_rag', 0)} tokens"
            ], style={'color': '#666'})
        ], className="mb-3", style={
            'padding': '12px', 
            'backgroundColor': '#1a1a2a', 
            'borderRadius': '5px',
            'borderLeft': '3px solid #00d9ff'
        })
        current_messages.append(ai_msg)
        
    except Exception as e:
        # Error message
        error_msg = html.Div([
            html.Strong("❌ Error: ", style={'color': '#ff4444'}),
            html.Span(str(e), style={'color': '#ddd'})
        ], className="mb-3", style={'padding': '8px', 'backgroundColor': '#2a1a1a', 'borderRadius': '5px'})
        current_messages.append(error_msg)
    
    return current_messages, "", ""  # Clear input


@app.callback(
    Output('god-output', 'children'),
    [Input('disable-button', 'n_clicks'),
     Input('reset-button', 'n_clicks')],
    State('disable-input', 'value'),
    prevent_initial_call=True
)
def handle_god_mode(disable_clicks, reset_clicks, node_id):
    """Handle God Mode actions"""
    from dash import callback_context
    
    ctx = callback_context
    if not ctx.triggered:
        return "Ready for action..."
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'disable-button' and node_id:
        result = god_mode.disable_node(node_id, reason="Dashboard God Mode")
        
        if result['success']:
            # Find affected warehouses
            affected = god_mode.get_affected_warehouses_by_disabled_node(node_id)
            
            return html.Div([
                html.H6("✅ Node Disabled", style={'color': '#ff4444'}),
                html.P(f"Name: {result['name']}", className="mb-1"),
                html.P(f"Type: {result['type']}", className="mb-1"),
                html.Hr(),
                html.P(f"⚠️ {len(affected)} downstream warehouses affected", 
                      style={'color': '#ffaa00'}),
                html.Small("Try querying: 'What happens if this node fails?'", 
                         className="text-muted")
            ])
        else:
            return html.Div([
                html.H6("❌ Error", style={'color': '#ff4444'}),
                html.P(result['error'])
            ])
    
    elif button_id == 'reset-button':
        result = god_mode.reset_all()
        return html.Div([
            html.H6("♻️ System Reset", style={'color': '#4CAF50'}),
            html.P(f"Re-enabled {result['re_enabled']} nodes"),
            html.Small("All nodes are now active", className="text-muted")
        ])
    
    return "Enter node ID and click Disable"


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 TITAN Supply Chain AI Dashboard")
    print("="*70)
    print("\n✅ Orchestrator initialized")
    print("✅ DCBA engine ready")
    print("✅ God Mode enabled")
    print("\n🌐 Dashboard: http://127.0.0.1:8050")
    print("⌨️  Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='127.0.0.1', port=8050)
