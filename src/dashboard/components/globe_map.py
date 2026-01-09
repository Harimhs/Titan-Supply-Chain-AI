#!/usr/bin/env python3
"""
Ultra-Modern 3D Globe Map Component
Beautiful interactive visualization with neon effects
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np


def create_globe_figure(data_loader, view='all', selected_disaster=None):
    """
    Create stunning interactive 3D globe figure
    
    Args:
        data_loader: DashboardDataLoader instance
        view: 'all', 'factories', 'ports', 'warehouses', 'disasters'
        selected_disaster: disaster_id to highlight
    
    Returns:
        Plotly figure with modern design
    """
    fig = go.Figure()
    
    # ========================================================================
    # MODERN GEO STYLING
    # ========================================================================
    fig.update_geos(
        projection_type="orthographic",
        showcountries=True,
        countrycolor="rgba(100,100,255,0.2)",  # Subtle blue borders
        showcoastlines=True,
        coastlinecolor="rgba(0,200,255,0.4)",  # Cyan coastlines
        showland=True,
        landcolor="rgba(15,15,35,1)",  # Deep dark blue
        showocean=True,
        oceancolor="rgba(5,5,25,1)",  # Darker ocean
        showlakes=True,
        lakecolor="rgba(10,10,30,1)",
        bgcolor="rgba(0,0,10,1)",  # Black space background
        lataxis_showgrid=False,
        lonaxis_showgrid=False
    )
    
    # ========================================================================
    # FACTORIES - Green Pulse Effect
    # ========================================================================
    if view in ['all', 'factories']:
        factories = data_loader.factories.sample(min(800, len(data_loader.factories)))
        
        # Create pulsing effect with multiple layers
        for layer, (size, opacity) in enumerate([(6, 0.8), (4, 0.6), (2, 0.3)]):
            fig.add_trace(go.Scattergeo(
                lon=factories['lon'],
                lat=factories['lat'],
                text='<b>🏭 Factory</b><br>' + 
                     'ID: ' + factories['id'] + '<br>' +
                     'Region: ' + factories['region'].fillna('Unknown') + '<br>' +
                     'Tier: ' + factories['tier'].astype(str),
                mode='markers',
                name='Factories' if layer == 0 else None,
                showlegend=(layer == 0),
                marker=dict(
                    size=size,
                    color='#00ff88',  # Neon green
                    opacity=opacity,
                    line=dict(width=0.5, color='rgba(0,255,136,0.8)'),
                    symbol='circle'
                ),
                hovertemplate=(
                    '<b style="color:#00ff88; font-size:14px">🏭 FACTORY</b><br>'
                    '<span style="color:#ffffff">%{text}</span><br>'
                    '<span style="color:#00bbff">📍 Lat: %{lat:.2f}°, Lon: %{lon:.2f}°</span>'
                    '<extra></extra>'
                ),
                hoverlabel=dict(
                    bgcolor='rgba(0,0,0,0.9)',
                    bordercolor='#00ff88',
                    font=dict(size=12, color='white')
                )
            ))
    
    # ========================================================================
    # PORTS - Cyan Diamond with Glow
    # ========================================================================
    if view in ['all', 'ports']:
        ports = data_loader.ports
        
        # Size based on TEU capacity with glow effect
        base_sizes = np.log10(ports['teu'] + 1) * 3 + 8
        
        # Outer glow layer
        fig.add_trace(go.Scattergeo(
            lon=ports['lon'],
            lat=ports['lat'],
            mode='markers',
            name=None,
            showlegend=False,
            marker=dict(
                size=base_sizes + 8,
                color='rgba(0,187,255,0.2)',
                line=dict(width=0),
                symbol='diamond'
            ),
            hoverinfo='skip'
        ))
        
        # Main port markers
        fig.add_trace(go.Scattergeo(
            lon=ports['lon'],
            lat=ports['lat'],
            text='<b>⚓ Port</b><br>' +
                 'Name: ' + ports['name'].fillna('Unknown') + '<br>' +
                 'City: ' + ports['city'].fillna('Unknown') + '<br>' +
                 'Tier: ' + ports['tier'].astype(str) + '<br>' +
                 'Annual TEU: ' + ports['teu'].apply(lambda x: f'{int(x):,}'),
            mode='markers',
            name='Ports',
            marker=dict(
                size=base_sizes,
                color='#00bbff',  # Neon cyan
                opacity=0.9,
                line=dict(width=2, color='rgba(255,255,255,0.6)'),
                symbol='diamond'
            ),
            hovertemplate=(
                '<b style="color:#00bbff; font-size:14px">⚓ PORT</b><br>'
                '<span style="color:#ffffff">%{text}</span><br>'
                '<span style="color:#00ff88">📍 Lat: %{lat:.2f}°, Lon: %{lon:.2f}°</span>'
                '<extra></extra>'
            ),
            hoverlabel=dict(
                bgcolor='rgba(0,0,0,0.9)',
                bordercolor='#00bbff',
                font=dict(size=12, color='white')
            )
        ))
    
    # ========================================================================
    # WAREHOUSES - Orange Clusters
    # ========================================================================
    if view in ['all', 'warehouses']:
        warehouses = data_loader.warehouses.sample(min(2000, len(data_loader.warehouses)))
        
        # Subtle glow
        fig.add_trace(go.Scattergeo(
            lon=warehouses['lon'],
            lat=warehouses['lat'],
            mode='markers',
            name=None,
            showlegend=False,
            marker=dict(
                size=6,
                color='rgba(255,170,0,0.15)',
                line=dict(width=0)
            ),
            hoverinfo='skip'
        ))
        
        # Main warehouse markers
        fig.add_trace(go.Scattergeo(
            lon=warehouses['lon'],
            lat=warehouses['lat'],
            text='<b>🏢 Warehouse</b><br>' +
                 'ID: ' + warehouses['id'] + '<br>' +
                 'City: ' + warehouses['city'].fillna('Unknown') + '<br>' +
                 'Type: ' + warehouses['type'].fillna('Standard'),
            mode='markers',
            name='Warehouses',
            marker=dict(
                size=4,
                color='#ffaa00',  # Neon orange
                opacity=0.7,
                line=dict(width=0.5, color='rgba(255,255,255,0.4)'),
                symbol='square'
            ),
            hovertemplate=(
                '<b style="color:#ffaa00; font-size:14px">🏢 WAREHOUSE</b><br>'
                '<span style="color:#ffffff">%{text}</span><br>'
                '<span style="color:#00ff88">📍 Lat: %{lat:.2f}°, Lon: %{lon:.2f}°</span>'
                '<extra></extra>'
            ),
            hoverlabel=dict(
                bgcolor='rgba(0,0,0,0.9)',
                bordercolor='#ffaa00',
                font=dict(size=12, color='white')
            )
        ))
    
    # ========================================================================
    # DISASTERS - Pulsing Red Danger Zones
    # ========================================================================
    if view in ['all', 'disasters'] and not data_loader.disasters.empty:
        disasters = data_loader.disasters
        
        for _, disaster in disasters.iterrows():
            radius_km = disaster['radius']
            
            # Multiple pulse layers for dramatic effect
            for pulse, (size_mult, opacity) in enumerate([(1.5, 0.2), (1.2, 0.3), (1.0, 0.5)]):
                # Create circle points
                angles = np.linspace(0, 2*np.pi, 80)
                lat_offset = (radius_km * size_mult) / 111
                lon_offset = (radius_km * size_mult) / (111 * np.cos(np.radians(disaster['lat'])))
                
                circle_lats = disaster['lat'] + lat_offset * np.sin(angles)
                circle_lons = disaster['lon'] + lon_offset * np.cos(angles)
                
                # Filled circle (danger zone)
                fig.add_trace(go.Scattergeo(
                    lon=circle_lons,
                    lat=circle_lats,
                    mode='lines',
                    fill='toself',
                    fillcolor=f'rgba(255,50,50,{opacity * 0.3})',
                    name=None,
                    line=dict(color=f'rgba(255,50,50,{opacity})', width=2),
                    showlegend=False,
                    hoverinfo='skip'
                ))
            
            # Disaster epicenter - glowing icon
            fig.add_trace(go.Scattergeo(
                lon=[disaster['lon']],
                lat=[disaster['lat']],
                text=f'<b>🔥 DISASTER ALERT</b><br>' +
                     f'Location: {disaster["location"]}<br>' +
                     f'Type: {disaster["type"]}<br>' +
                     f'Severity: {disaster["severity"]}<br>' +
                     f'Radius: {disaster["radius"]:.0f} km<br>' +
                     f'Recovery: {disaster["recovery_days"]} days',
                mode='markers',
                name='Disasters' if _ == 0 else None,
                showlegend=(_ == 0),
                marker=dict(
                    size=25,
                    color='#ff3333',
                    opacity=1.0,
                    line=dict(width=3, color='#ffffff'),
                    symbol='x'
                ),
                hovertemplate=(
                    '<b style="color:#ff3333; font-size:16px">🔥 DISASTER ZONE</b><br>'
                    '<span style="color:#ffffff">%{text}</span><br>'
                    '<span style="color:#ff3333">⚠️ CRITICAL ALERT</span>'
                    '<extra></extra>'
                ),
                hoverlabel=dict(
                    bgcolor='rgba(255,0,0,0.9)',
                    bordercolor='#ffffff',
                    font=dict(size=13, color='white', family='Arial Black')
                )
            ))
    
    # ========================================================================
    # SUPPLY ROUTES - Animated Flow Lines
    # ========================================================================
    if view == 'all' and data_loader.routes:
        sample_routes = data_loader.routes[:150]
        
        for route in sample_routes:
            # Route type determines color
            if route['src_type'] == 'Factory':
                color = 'rgba(0,255,136,0.25)'  # Green from factories
            elif route['src_type'] == 'Port':
                color = 'rgba(0,187,255,0.25)'  # Cyan from ports
            else:
                color = 'rgba(255,170,0,0.25)'  # Orange default
            
            # Curved flight path
            fig.add_trace(go.Scattergeo(
                lon=[route['src_lon'], route['dst_lon']],
                lat=[route['src_lat'], route['dst_lat']],
                mode='lines',
                line=dict(color=color, width=1.5),
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # ========================================================================
    # MODERN LAYOUT WITH GRADIENT BACKGROUND
    # ========================================================================
    fig.update_layout(
        title=dict(
            text=(
                '<span style="font-size:28px; font-weight:bold; '
                'background: linear-gradient(90deg, #00ff88, #00bbff, #ff3333); '
                '-webkit-background-clip: text; -webkit-text-fill-color: transparent;">'
                '🌍 TITAN GLOBAL SUPPLY CHAIN</span>'
            ),
            x=0.5,
            xanchor='center',
            y=0.98,
            yanchor='top',
            font=dict(size=28, color='white', family='Arial Black')
        ),
        geo=dict(
            projection_rotation=dict(lon=20, lat=20, roll=0),
            center=dict(lon=20, lat=20)
        ),
        height=800,
        margin=dict(l=0, r=0, t=60, b=0),
        
        # Gradient background
        paper_bgcolor='#000000',
        plot_bgcolor='#000000',
        
        font=dict(color='white', family='Arial'),
        
        # Modern legend
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(10,10,30,0.85)',
            bordercolor='rgba(0,200,255,0.5)',
            borderwidth=2,
            font=dict(size=12, color='white', family='Arial')
        ),
        
        hovermode='closest',
        
        # Smooth transitions
        transition=dict(
            duration=500,
            easing='cubic-in-out'
        )
    )
    
    # Add custom config for better interactivity
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.5,
                y=0.02,
                xanchor="center",
                yanchor="bottom",
                bgcolor='rgba(10,10,30,0.8)',
                bordercolor='rgba(0,200,255,0.5)',
                borderwidth=2,
                buttons=[
                    dict(label="▶️ Rotate", method="animate",
                         args=[None, {"frame": {"duration": 50, "redraw": True},
                                     "fromcurrent": True, "mode": "immediate"}]),
                    dict(label="⏸️ Pause", method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False},
                                       "mode": "immediate"}])
                ],
                font=dict(color='white', size=11)
            )
        ]
    )
    
    return fig


# Test
if __name__ == "__main__":
    from src.dashboard.utils.data_loader import DashboardDataLoader
    
    print("🎨 Testing Ultra-Modern Globe Map...")
    
    loader = DashboardDataLoader()
    fig = create_globe_figure(loader, view='all')
    
    print(f"✅ Created stunning figure with {len(fig.data)} traces")
    
    # Save to HTML with custom template
    fig.write_html(
        "test_globe_modern.html",
        config={
            'displayModeBar': True,
            'scrollZoom': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d']
        }
    )
    print("✅ Saved to test_globe_modern.html")
    print("🌐 Open in browser to see the magic! ✨")
    
    loader.close()
