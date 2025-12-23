"""
Plotly Dash Custom Dashboard
Real-time project management visualization.
"""
import os
import sys
from decimal import Decimal

import dash
from dash import dcc, html, dash_table, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# ===========================================
# Database Connection
# ===========================================

def get_db_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5432)),
        database=os.getenv('POSTGRES_DB', 'project_mgmt'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres123'),
    )


def fetch_projects():
    """Fetch all projects from database."""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    id_root, klaster_regional, entitas_terminal, 
                    project_definition, type_investasi, tahun_rkap,
                    status_investasi, status_issue, rkap, nilai_kontrak,
                    realisasi_januari + realisasi_februari + realisasi_maret +
                    realisasi_april + realisasi_mei + realisasi_juni +
                    realisasi_juli + realisasi_agustus + realisasi_september +
                    realisasi_oktober + realisasi_november + realisasi_desember as total_realisasi,
                    latitude, longitude, updated_at
                FROM project_investasi
                ORDER BY updated_at DESC
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def fetch_summary_by_regional():
    """Fetch summary statistics by regional."""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    klaster_regional,
                    COUNT(*) as project_count,
                    COALESCE(SUM(rkap), 0) as total_rkap,
                    COALESCE(SUM(nilai_kontrak), 0) as total_nilai_kontrak,
                    COALESCE(SUM(
                        realisasi_januari + realisasi_februari + realisasi_maret +
                        realisasi_april + realisasi_mei + realisasi_juni +
                        realisasi_juli + realisasi_agustus + realisasi_september +
                        realisasi_oktober + realisasi_november + realisasi_desember
                    ), 0) as total_realisasi,
                    COUNT(*) FILTER (WHERE status_issue = 'Open') as open_issues,
                    COUNT(*) FILTER (WHERE status_issue = 'Closed') as closed_issues
                FROM project_investasi
                GROUP BY klaster_regional
                ORDER BY klaster_regional
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def fetch_monthly_realization():
    """Fetch monthly realization data."""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COALESCE(SUM(realisasi_januari), 0) as januari,
                    COALESCE(SUM(realisasi_februari), 0) as februari,
                    COALESCE(SUM(realisasi_maret), 0) as maret,
                    COALESCE(SUM(realisasi_april), 0) as april,
                    COALESCE(SUM(realisasi_mei), 0) as mei,
                    COALESCE(SUM(realisasi_juni), 0) as juni,
                    COALESCE(SUM(realisasi_juli), 0) as juli,
                    COALESCE(SUM(realisasi_agustus), 0) as agustus,
                    COALESCE(SUM(realisasi_september), 0) as september,
                    COALESCE(SUM(realisasi_oktober), 0) as oktober,
                    COALESCE(SUM(realisasi_november), 0) as november,
                    COALESCE(SUM(realisasi_desember), 0) as desember
                FROM project_investasi
            """)
            return cur.fetchone()
    except Exception as e:
        print(f"Database error: {e}")
        return {}
    finally:
        if conn:
            conn.close()


# ===========================================
# Initialize Dash App
# ===========================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Project Management Dashboard",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)

server = app.server

# ===========================================
# Layout Components
# ===========================================

def create_kpi_card(title, value, subtitle="", color="primary"):
    """Create a KPI card component."""
    return dbc.Card([
        dbc.CardBody([
            html.H6(title, className="card-subtitle text-muted mb-2"),
            html.H3(value, className=f"card-title text-{color}"),
            html.P(subtitle, className="card-text small text-muted")
        ])
    ], className="shadow-sm h-100")


def create_header():
    """Create dashboard header."""
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand([
                html.I(className="fas fa-chart-line me-2"),
                "Project Management Dashboard"
            ], className="fs-4"),
            dbc.Nav([
                dbc.NavItem(dbc.Button(
                    [html.I(className="fas fa-sync-alt me-2"), "Refresh"],
                    id="refresh-btn",
                    color="light",
                    outline=True,
                    size="sm"
                ))
            ])
        ]),
        color="dark",
        dark=True,
        className="mb-4"
    )


# ===========================================
# Main Layout
# ===========================================

app.layout = html.Div([
    create_header(),
    
    dbc.Container([
        # KPI Row
        dbc.Row([
            dbc.Col([
                html.Div(id="kpi-total-projects")
            ], md=3),
            dbc.Col([
                html.Div(id="kpi-total-rkap")
            ], md=3),
            dbc.Col([
                html.Div(id="kpi-total-realisasi")
            ], md=3),
            dbc.Col([
                html.Div(id="kpi-open-issues")
            ], md=3),
        ], className="mb-4"),
        
        # Charts Row 1
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("RKAP vs Realisasi by Regional"),
                    dbc.CardBody([
                        dcc.Graph(id="chart-rkap-realisasi", config={"displayModeBar": False})
                    ])
                ], className="shadow-sm")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Monthly Realization Trend"),
                    dbc.CardBody([
                        dcc.Graph(id="chart-monthly-trend", config={"displayModeBar": False})
                    ])
                ], className="shadow-sm")
            ], md=6),
        ], className="mb-4"),
        
        # Charts Row 2
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Investment Type Distribution"),
                    dbc.CardBody([
                        dcc.Graph(id="chart-investment-type", config={"displayModeBar": False})
                    ])
                ], className="shadow-sm")
            ], md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Issue Status"),
                    dbc.CardBody([
                        dcc.Graph(id="chart-issue-status", config={"displayModeBar": False})
                    ])
                ], className="shadow-sm")
            ], md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Project Locations"),
                    dbc.CardBody([
                        dcc.Graph(id="chart-map", config={"displayModeBar": False})
                    ])
                ], className="shadow-sm")
            ], md=4),
        ], className="mb-4"),
        
        # Project Table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Project List"),
                    dbc.CardBody([
                        html.Div(id="project-table")
                    ])
                ], className="shadow-sm")
            ])
        ]),
        
        # Footer
        html.Footer([
            html.Hr(),
            html.P("Project Management Dashboard © 2025", className="text-center text-muted")
        ], className="mt-4")
    ], fluid=True),
    
    # Interval for auto-refresh
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # 60 seconds
        n_intervals=0
    )
])


# ===========================================
# Callbacks
# ===========================================

@callback(
    [
        Output("kpi-total-projects", "children"),
        Output("kpi-total-rkap", "children"),
        Output("kpi-total-realisasi", "children"),
        Output("kpi-open-issues", "children"),
        Output("chart-rkap-realisasi", "figure"),
        Output("chart-monthly-trend", "figure"),
        Output("chart-investment-type", "figure"),
        Output("chart-issue-status", "figure"),
        Output("chart-map", "figure"),
        Output("project-table", "children"),
    ],
    [
        Input("interval-component", "n_intervals"),
        Input("refresh-btn", "n_clicks")
    ]
)
def update_dashboard(n_intervals, n_clicks):
    """Update all dashboard components."""
    
    # Fetch data
    projects = fetch_projects()
    summary = fetch_summary_by_regional()
    monthly = fetch_monthly_realization()
    
    df_projects = pd.DataFrame(projects) if projects else pd.DataFrame()
    df_summary = pd.DataFrame(summary) if summary else pd.DataFrame()
    
    # Calculate KPIs
    total_projects = len(projects)
    total_rkap = sum(float(p.get('rkap') or 0) for p in projects)
    total_realisasi = sum(float(p.get('total_realisasi') or 0) for p in projects)
    open_issues = sum(1 for p in projects if p.get('status_issue') == 'Open')
    
    serapan_pct = (total_realisasi / total_rkap * 100) if total_rkap > 0 else 0
    
    # KPI Cards
    kpi_projects = create_kpi_card("Total Projects", f"{total_projects:,}", "Active projects")
    kpi_rkap = create_kpi_card("Total RKAP", f"Rp {total_rkap/1e9:.2f}B", "Budget allocation", "info")
    kpi_realisasi = create_kpi_card("Total Realisasi", f"Rp {total_realisasi/1e9:.2f}B", f"{serapan_pct:.1f}% absorption", "success")
    kpi_issues = create_kpi_card("Open Issues", f"{open_issues}", "Pending resolution", "warning")
    
    # Chart: RKAP vs Realisasi
    if not df_summary.empty:
        fig_rkap = go.Figure()
        fig_rkap.add_trace(go.Bar(
            name='RKAP',
            x=df_summary['klaster_regional'],
            y=df_summary['total_rkap'],
            marker_color='#3498db'
        ))
        fig_rkap.add_trace(go.Bar(
            name='Realisasi',
            x=df_summary['klaster_regional'],
            y=df_summary['total_realisasi'],
            marker_color='#2ecc71'
        ))
        fig_rkap.update_layout(
            barmode='group',
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
    else:
        fig_rkap = go.Figure()
        fig_rkap.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    # Chart: Monthly Trend
    if monthly:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
        values = [
            float(monthly.get('januari') or 0),
            float(monthly.get('februari') or 0),
            float(monthly.get('maret') or 0),
            float(monthly.get('april') or 0),
            float(monthly.get('mei') or 0),
            float(monthly.get('juni') or 0),
            float(monthly.get('juli') or 0),
            float(monthly.get('agustus') or 0),
            float(monthly.get('september') or 0),
            float(monthly.get('oktober') or 0),
            float(monthly.get('november') or 0),
            float(monthly.get('desember') or 0),
        ]
        
        fig_monthly = go.Figure()
        fig_monthly.add_trace(go.Scatter(
            x=months, y=values,
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#9b59b6'),
            marker=dict(size=8)
        ))
        fig_monthly.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20)
        )
    else:
        fig_monthly = go.Figure()
        fig_monthly.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    # Chart: Investment Type
    if not df_projects.empty and 'type_investasi' in df_projects.columns:
        type_counts = df_projects['type_investasi'].value_counts()
        fig_type = go.Figure(data=[go.Pie(
            labels=type_counts.index.tolist(),
            values=type_counts.values.tolist(),
            hole=0.4,
            marker_colors=['#3498db', '#e74c3c', '#f39c12']
        )])
        fig_type.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True
        )
    else:
        fig_type = go.Figure()
        fig_type.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    # Chart: Issue Status
    if not df_summary.empty:
        total_open = df_summary['open_issues'].sum()
        total_closed = df_summary['closed_issues'].sum()
        
        fig_issues = go.Figure(data=[go.Pie(
            labels=['Open', 'Closed'],
            values=[total_open, total_closed],
            hole=0.5,
            marker_colors=['#e74c3c', '#2ecc71']
        )])
        fig_issues.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20)
        )
    else:
        fig_issues = go.Figure()
        fig_issues.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    # Chart: Map
    if not df_projects.empty and 'latitude' in df_projects.columns:
        df_map = df_projects.dropna(subset=['latitude', 'longitude'])
        if not df_map.empty:
            fig_map = px.scatter_mapbox(
                df_map,
                lat='latitude',
                lon='longitude',
                hover_name='project_definition',
                hover_data=['klaster_regional', 'status_investasi'],
                color_discrete_sequence=['#3498db'],
                zoom=4
            )
            fig_map.update_layout(
                mapbox_style='carto-darkmatter',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=0, b=0)
            )
        else:
            fig_map = go.Figure()
            fig_map.add_annotation(text="No location data available", showarrow=False)
            fig_map.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    else:
        fig_map = go.Figure()
        fig_map.add_annotation(text="No location data available", showarrow=False)
        fig_map.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    # Project Table
    if not df_projects.empty:
        display_cols = ['id_root', 'klaster_regional', 'entitas_terminal', 
                       'type_investasi', 'tahun_rkap', 'status_issue']
        df_display = df_projects[display_cols].head(20)
        
        table = dash_table.DataTable(
            data=df_display.to_dict('records'),
            columns=[{"name": col, "id": col} for col in display_cols],
            style_cell={
                'backgroundColor': '#303030',
                'color': 'white',
                'textAlign': 'left',
                'padding': '10px'
            },
            style_header={
                'backgroundColor': '#404040',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{status_issue} = "Open"'},
                    'backgroundColor': 'rgba(231, 76, 60, 0.2)'
                }
            ],
            page_size=10
        )
    else:
        table = html.P("No projects found.", className="text-muted")
    
    return (
        kpi_projects, kpi_rkap, kpi_realisasi, kpi_issues,
        fig_rkap, fig_monthly, fig_type, fig_issues, fig_map,
        table
    )


# ===========================================
# Run Server
# ===========================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)
