from dash import html, dcc
import dash_bootstrap_components as dbc

def create_chat_panel():
    """Simple reusable chat panel for the right side."""
    return dbc.Card([
        dbc.CardHeader([
            html.H5("💬 AI Assistant", className="mb-0"),
            html.Small("Ask about supply chain, disasters, or routes", className="text-muted")
        ]),
        dbc.CardBody([
            # Chat messages container
            html.Div(
                id='chat-messages',
                style={
                    'height': '40vh',
                    'overflowY': 'scroll',
                    'padding': '10px',
                    'backgroundColor': '#1a1a1a',
                    'borderRadius': '5px',
                    'marginBottom': '10px'
                },
                children=[
                    html.P(
                        "👋 Hello! Ask me about disruptions, routes, or factories.",
                        className="text-muted"
                    )
                ]
            ),
            # Input + send button
            dbc.InputGroup([
                dbc.Input(
                    id='chat-input',
                    placeholder="e.g., Impact of Taiwan earthquake?",
                    type="text"
                ),
                dbc.Button("Send", id='chat-send', color="primary")
            ])
        ])
    ])
