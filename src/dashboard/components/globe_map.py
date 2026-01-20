"""
Globe Map Visualization
"""

import plotly.graph_objects as go

def create_globe_figure(data_loader, view='all'):
    """
    Create 3D globe visualization
    """
    fig = go.Figure()
    
    # Add nodes based on view
    if view in ['all', 'factories'] and data_loader.factories:
        df = data_loader.factories.head(1000)  # Limit for performance
        fig.add_trace(go.Scattergeo(
            lon=df['lon'],
            lat=df['lat'],
            mode='markers',
            marker=dict(size=3, color='green', opacity=0.6),
            name='Factories',
            text=df['name'],
            hovertemplate='<b>%{text}</b><br>%{lat}, %{lon}<extra></extra>'
        ))
    
    if view in ['all', 'ports'] and data_loader.ports:
        df = data_loader.ports
        fig.add_trace(go.Scattergeo(
            lon=df['lon'],
            lat=df['lat'],
            mode='markers',
            marker=dict(size=8, color='blue', symbol='square', opacity=0.8),
            name='Ports',
            text=df['name'],
            hovertemplate='<b>%{text}</b><br>%{lat}, %{lon}<extra></extra>'
        ))
    
    if view in ['all', 'warehouses'] and data_loader.warehouses:
        df = data_loader.warehouses.head(500)  # Limit for performance
        fig.add_trace(go.Scattergeo(
            lon=df['lon'],
            lat=df['lat'],
            mode='markers',
            marker=dict(size=2, color='yellow', opacity=0.4),
            name='Warehouses',
            text=df['name'],
            hovertemplate='<b>%{text}</b><br>%{lat}, %{lon}<extra></extra>'
        ))
    
    # Layout
    fig.update_layout(
        geo=dict(
            projection_type='orthographic',
            showland=True,
            landcolor='rgb(20, 20, 20)',
            showcountries=True,
            countrycolor='rgb(60, 60, 60)',
            showocean=True,
            oceancolor='rgb(10, 10, 30)',
            bgcolor='rgba(0,0,0,0)'
        ),
        paper_bgcolor='rgb(20, 20, 20)',
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=True,
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.5)')
    )
    
    return fig
