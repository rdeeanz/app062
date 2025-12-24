"""
Plotly Dash Multi-Page Dashboard
Project management visualization with navigation menu.
"""
import os
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
                    kebutuhan_dana, asset_categories,
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


def fetch_investment_by_category():
    """Fetch investment summary by asset category."""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    asset_categories,
                    COUNT(*) as item_count,
                    COALESCE(SUM(kebutuhan_dana), 0) as total_kebutuhan,
                    COALESCE(SUM(rkap), 0) as total_rkap,
                    COALESCE(SUM(
                        realisasi_januari + realisasi_februari + realisasi_maret +
                        realisasi_april + realisasi_mei + realisasi_juni +
                        realisasi_juli + realisasi_agustus + realisasi_september +
                        realisasi_oktober + realisasi_november + realisasi_desember
                    ), 0) as total_realisasi
                FROM project_investasi
                GROUP BY asset_categories
                ORDER BY asset_categories
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def fetch_investment_by_status():
    """Fetch investment summary by status."""
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    COALESCE(NULLIF(status_investasi, ''), 'Belum Ditentukan') as status,
                    COUNT(*) as count
                FROM project_investasi
                GROUP BY status_investasi
                ORDER BY count DESC
            """)
            return cur.fetchall()
    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


# ===========================================
# Initialize Dash App
# ===========================================

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.DARKLY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    title="Project Management Dashboard",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True
)

server = app.server

# ===========================================
# Sidebar Navigation
# ===========================================

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "220px",
    "padding": "20px 15px",
    "backgroundColor": "#1a1a2e",
}

CONTENT_STYLE = {
    "marginLeft": "240px",
    "padding": "20px",
}

sidebar = html.Div([
    html.Div([
        html.I(className="fas fa-chart-pie fa-2x text-info"),
        html.Span(" Dashboard", className="text-white fs-5 ms-2"),
    ], className="mb-4 text-center"),
    
    html.Hr(style={"borderColor": "#444"}),
    
    dbc.Nav([
        dbc.NavLink([html.I(className="fas fa-home me-2"), "Overview"], href="/", active="exact"),
        dbc.NavLink([html.I(className="fas fa-chart-bar me-2"), "Investment"], href="/investment", active="exact"),
        dbc.NavLink([html.I(className="fas fa-list me-2"), "Project List"], href="/projects", active="exact"),
        dbc.NavLink([html.I(className="fas fa-chart-line me-2"), "Trends"], href="/trends", active="exact"),
        dbc.NavLink([html.I(className="fas fa-map me-2"), "Map"], href="/map", active="exact"),
    ], vertical=True, pills=True),
    
    html.Hr(style={"borderColor": "#444"}),
    html.Small("© 2025 Project Management", className="text-muted"),
], style=SIDEBAR_STYLE)


# ===========================================
# Helper Components
# ===========================================

def create_kpi_card(title, value, subtitle="", color="primary", icon=""):
    return dbc.Card([
        dbc.CardBody([
            html.Div([html.I(className=f"fas {icon} fa-2x text-{color} opacity-50")], className="float-end") if icon else None,
            html.H6(title, className="card-subtitle text-muted mb-2"),
            html.H3(value, className=f"card-title text-{color}"),
            html.P(subtitle, className="card-text small text-muted mb-0")
        ])
    ], className="shadow-sm h-100")


# ===========================================
# Page Layouts
# ===========================================

def page_overview():
    return html.Div([
        html.H2("Dashboard Overview", className="mb-4"),
        dbc.Row([
            dbc.Col([html.Div(id="kpi-projects")], md=3),
            dbc.Col([html.Div(id="kpi-rkap")], md=3),
            dbc.Col([html.Div(id="kpi-realisasi")], md=3),
            dbc.Col([html.Div(id="kpi-issues")], md=3),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("RKAP vs Realisasi by Regional"),
                    dbc.CardBody([dcc.Graph(id="chart-regional", config={"displayModeBar": False})])
                ], className="shadow-sm")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Monthly Realization Trend"),
                    dbc.CardBody([dcc.Graph(id="chart-monthly", config={"displayModeBar": False})])
                ], className="shadow-sm")
            ], md=6),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Investment Type"),
                    dbc.CardBody([dcc.Graph(id="chart-type", config={"displayModeBar": False})])
                ], className="shadow-sm")
            ], md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Issue Status"),
                    dbc.CardBody([dcc.Graph(id="chart-issues", config={"displayModeBar": False})])
                ], className="shadow-sm")
            ], md=4),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Project Locations"),
                    dbc.CardBody([dcc.Graph(id="chart-overview-map", config={"displayModeBar": False})])
                ], className="shadow-sm")
            ], md=4),
        ]),
    ])


def page_investment():
    return html.Div([
        html.H2("Investment Dashboard", className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Capaian RKAP", className="text-center text-muted"),
                        html.Div(id="gauge-capaian")
                    ])
                ], className="shadow-sm", style={"minHeight": "250px"})
            ], md=3),
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([dbc.CardBody([
                            html.H6("Total Item", className="text-muted"),
                            html.H2(id="stat-total-item", className="text-info"),
                        ])], className="shadow-sm mb-3")
                    ], md=6),
                    dbc.Col([
                        dbc.Card([dbc.CardBody([
                            html.H6("Total RKAP", className="text-muted"),
                            html.H4(id="stat-total-rkap", className="text-success"),
                        ])], className="shadow-sm mb-3")
                    ], md=6),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Card([dbc.CardBody([
                            html.H6("Kebutuhan Dana", className="text-muted"),
                            html.H4(id="stat-kebutuhan", className="text-warning"),
                        ])], className="shadow-sm")
                    ], md=6),
                    dbc.Col([
                        dbc.Card([dbc.CardBody([
                            html.H6("Total Realisasi", className="text-muted"),
                            html.H4(id="stat-realisasi", className="text-primary"),
                        ])], className="shadow-sm")
                    ], md=6),
                ]),
            ], md=5),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Status Program"),
                    dbc.CardBody([dcc.Graph(id="chart-status", config={"displayModeBar": False}, style={"height": "200px"})])
                ], className="shadow-sm h-100")
            ], md=4),
        ], className="mb-4"),
        dbc.Card([
            dbc.CardHeader("Investasi per Kategori"),
            dbc.CardBody([html.Div(id="table-category")])
        ], className="shadow-sm"),
    ])


def page_projects():
    return html.Div([
        html.H2("Project List", className="mb-4"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([dcc.Dropdown(id="f-regional", placeholder="Regional", clearable=True)], md=2),
                    dbc.Col([dcc.Dropdown(id="f-terminal", placeholder="Terminal", clearable=True)], md=3),
                    dbc.Col([dcc.Dropdown(id="f-type", placeholder="Type", clearable=True)], md=2),
                    dbc.Col([dcc.Dropdown(id="f-tahun", placeholder="Tahun", clearable=True)], md=2),
                    dbc.Col([dcc.Dropdown(id="f-status", placeholder="Status", clearable=True)], md=2),
                    dbc.Col([dbc.Button("Reset", id="btn-reset", size="sm", className="w-100")], md=1),
                ])
            ])
        ], className="shadow-sm mb-4"),
        dbc.Card([
            dbc.CardBody([html.Div(id="project-table")])
        ], className="shadow-sm"),
        dcc.Store(id="projects-store"),
    ])


def page_trends():
    return html.Div([
        html.H2("Trend Analysis", className="mb-4"),
        dbc.Card([
            dbc.CardHeader("Realisasi Bulanan"),
            dbc.CardBody([dcc.Graph(id="chart-trend-monthly", config={"displayModeBar": False}, style={"height": "400px"})])
        ], className="shadow-sm mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("RKAP vs Realisasi per Kategori"),
                    dbc.CardBody([dcc.Graph(id="chart-cat-compare", config={"displayModeBar": False})])
                ], className="shadow-sm")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Capaian per Kategori (%)"),
                    dbc.CardBody([dcc.Graph(id="chart-cat-pct", config={"displayModeBar": False})])
                ], className="shadow-sm")
            ], md=6),
        ]),
    ])


def page_map():
    return html.Div([
        html.H2("Peta Lokasi Project", className="mb-4"),
        dbc.Card([
            dbc.CardBody([dcc.Graph(id="full-map", config={"displayModeBar": True}, style={"height": "600px"})])
        ], className="shadow-sm"),
    ])


def page_404():
    return html.Div([
        html.H1("404", className="display-1 text-muted text-center"),
        html.P("Halaman tidak ditemukan", className="text-center"),
        dbc.Button("Kembali", href="/", className="d-block mx-auto"),
    ], className="py-5")


# ===========================================
# Main Layout
# ===========================================

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    sidebar,
    html.Div(id='page-content', style=CONTENT_STYLE),
    dcc.Interval(id='interval', interval=60*1000, n_intervals=0),
])


# ===========================================
# Routing Callback
# ===========================================

@callback(Output('page-content', 'children'), Input('url', 'pathname'))
def route_page(pathname):
    if pathname == '/': return page_overview()
    elif pathname == '/investment': return page_investment()
    elif pathname == '/projects': return page_projects()
    elif pathname == '/trends': return page_trends()
    elif pathname == '/map': return page_map()
    return page_404()


# ===========================================
# Overview Page Callbacks
# ===========================================

@callback(
    [Output("kpi-projects", "children"), Output("kpi-rkap", "children"), Output("kpi-realisasi", "children"), Output("kpi-issues", "children"),
     Output("chart-regional", "figure"), Output("chart-monthly", "figure"), Output("chart-type", "figure"), Output("chart-issues", "figure"), Output("chart-overview-map", "figure")],
    [Input("interval", "n_intervals")]
)
def update_overview(n):
    projects = fetch_projects()
    summary = fetch_summary_by_regional()
    monthly = fetch_monthly_realization()
    df = pd.DataFrame(projects) if projects else pd.DataFrame()
    df_sum = pd.DataFrame(summary) if summary else pd.DataFrame()
    
    total = len(projects)
    rkap = sum(float(p.get('rkap') or 0) for p in projects)
    real = sum(float(p.get('total_realisasi') or 0) for p in projects)
    issues = sum(1 for p in projects if p.get('status_issue') == 'Open')
    pct = (real / rkap * 100) if rkap > 0 else 0
    
    kpi1 = create_kpi_card("Total Projects", f"{total:,}", "Active", "info", "fa-folder")
    kpi2 = create_kpi_card("Total RKAP", f"Rp {rkap/1e9:.2f}B", "Budget", "success", "fa-money-bill")
    kpi3 = create_kpi_card("Total Realisasi", f"Rp {real/1e9:.2f}B", f"{pct:.1f}%", "primary", "fa-chart-line")
    kpi4 = create_kpi_card("Open Issues", f"{issues}", "Pending", "warning", "fa-exclamation")
    
    # Charts
    if not df_sum.empty:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(name='RKAP', x=df_sum['klaster_regional'], y=df_sum['total_rkap'], marker_color='#3498db'))
        fig1.add_trace(go.Bar(name='Realisasi', x=df_sum['klaster_regional'], y=df_sum['total_realisasi'], marker_color='#2ecc71'))
        fig1.update_layout(barmode='group', template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20,r=20,t=20,b=20))
    else:
        fig1 = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    if monthly:
        months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
        vals = [float(monthly.get(m) or 0) for m in ['januari','februari','maret','april','mei','juni','juli','agustus','september','oktober','november','desember']]
        fig2 = go.Figure(go.Scatter(x=months, y=vals, mode='lines+markers', fill='tozeroy', line=dict(color='#9b59b6')))
        fig2.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=20,r=20,t=20,b=20))
    else:
        fig2 = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    if not df.empty and 'type_investasi' in df.columns:
        tc = df['type_investasi'].value_counts()
        fig3 = go.Figure(go.Pie(labels=tc.index.tolist(), values=tc.values.tolist(), hole=0.4))
        fig3.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20,r=20,t=20,b=20))
    else:
        fig3 = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    if not df_sum.empty:
        fig4 = go.Figure(go.Pie(labels=['Open','Closed'], values=[df_sum['open_issues'].sum(), df_sum['closed_issues'].sum()], hole=0.5, marker_colors=['#e74c3c','#2ecc71']))
        fig4.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=20,r=20,t=20,b=20))
    else:
        fig4 = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    if not df.empty and 'latitude' in df.columns:
        dm = df.dropna(subset=['latitude','longitude'])
        if not dm.empty:
            fig5 = px.scatter_mapbox(dm, lat='latitude', lon='longitude', hover_name='project_definition', zoom=4)
            fig5.update_layout(mapbox_style='carto-darkmatter', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=0,b=0))
        else:
            fig5 = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    else:
        fig5 = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    return kpi1, kpi2, kpi3, kpi4, fig1, fig2, fig3, fig4, fig5


# ===========================================
# Investment Page Callbacks
# ===========================================

@callback(
    [Output("gauge-capaian", "children"), Output("stat-total-item", "children"), Output("stat-total-rkap", "children"),
     Output("stat-kebutuhan", "children"), Output("stat-realisasi", "children"), Output("chart-status", "figure"), Output("table-category", "children")],
    [Input("interval", "n_intervals")]
)
def update_investment(n):
    projects = fetch_projects()
    cats = fetch_investment_by_category()
    status = fetch_investment_by_status()
    
    total = len(projects)
    rkap = sum(float(p.get('rkap') or 0) for p in projects)
    keb = sum(float(p.get('kebutuhan_dana') or 0) for p in projects)
    real = sum(float(p.get('total_realisasi') or 0) for p in projects)
    cap = (real / rkap * 100) if rkap > 0 else 0
    
    gf = go.Figure(go.Indicator(mode="gauge+number", value=cap, gauge={'axis':{'range':[0,100]}, 'bar':{'color':'#2ecc71'}}))
    gf.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', height=180, margin=dict(l=20,r=20,t=20,b=20))
    gauge = dcc.Graph(figure=gf, config={"displayModeBar": False})
    
    if status:
        ds = pd.DataFrame(status)
        fs = go.Figure(go.Bar(x=ds['count'], y=ds['status'], orientation='h', marker_color='#3498db'))
        fs.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=10,r=10,t=10,b=10), yaxis={'categoryorder':'total ascending'})
    else:
        fs = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    if cats:
        dc = pd.DataFrame(cats)
        dc['capaian'] = dc.apply(lambda r: round((r['total_realisasi']/r['total_rkap']*100),2) if r['total_rkap']>0 else 0, axis=1)
        tbl = dash_table.DataTable(
            data=dc.to_dict('records'),
            columns=[{"name":"Kategori","id":"asset_categories"},{"name":"Item","id":"item_count"},{"name":"Kebutuhan","id":"total_kebutuhan","type":"numeric","format":{"specifier":",.0f"}},{"name":"RKAP","id":"total_rkap","type":"numeric","format":{"specifier":",.0f"}},{"name":"Realisasi","id":"total_realisasi","type":"numeric","format":{"specifier":",.0f"}},{"name":"Capaian(%)","id":"capaian"}],
            style_cell={'backgroundColor':'#303030','color':'white','textAlign':'left','padding':'10px'},
            style_header={'backgroundColor':'#404040','fontWeight':'bold'},
            page_size=10,
        )
    else:
        tbl = html.P("No data", className="text-muted")
    
    return gauge, f"{total:,}", f"Rp {rkap/1e6:,.0f}Jt", f"Rp {keb/1e6:,.0f}Jt", f"Rp {real/1e6:,.0f}Jt", fs, tbl


# ===========================================
# Projects Page Callbacks
# ===========================================

@callback(
    [Output("projects-store", "data"), Output("f-regional", "options"), Output("f-terminal", "options"), Output("f-type", "options"), Output("f-tahun", "options"), Output("f-status", "options")],
    [Input("interval", "n_intervals")]
)
def load_projects(n):
    projects = fetch_projects()
    df = pd.DataFrame(projects) if projects else pd.DataFrame()
    if not df.empty:
        cols = ['id_root','klaster_regional','entitas_terminal','type_investasi','tahun_rkap','status_issue']
        return df[cols].to_dict('records'), [{"label":v,"value":v} for v in sorted(df['klaster_regional'].dropna().unique())], [{"label":v,"value":v} for v in sorted(df['entitas_terminal'].dropna().unique())], [{"label":v,"value":v} for v in sorted(df['type_investasi'].dropna().unique())], [{"label":str(v),"value":v} for v in sorted(df['tahun_rkap'].dropna().unique())], [{"label":v if v else "N/A","value":v if v else ""} for v in df['status_issue'].dropna().unique()]
    return [], [], [], [], [], []

@callback(Output("project-table", "children"), [Input("projects-store", "data"), Input("f-regional", "value"), Input("f-terminal", "value"), Input("f-type", "value"), Input("f-tahun", "value"), Input("f-status", "value")])
def filter_projects(data, fr, ft, fty, fy, fs):
    if not data: return html.P("No data", className="text-muted")
    df = pd.DataFrame(data)
    if fr: df = df[df['klaster_regional']==fr]
    if ft: df = df[df['entitas_terminal']==ft]
    if fty: df = df[df['type_investasi']==fty]
    if fy: df = df[df['tahun_rkap']==fy]
    if fs: df = df[df['status_issue']==fs]
    if df.empty: return html.P("No matching data", className="text-muted")
    return dash_table.DataTable(data=df.to_dict('records'), columns=[{"name":c.replace('_',' ').title(),"id":c} for c in df.columns], style_cell={'backgroundColor':'#303030','color':'white','textAlign':'left','padding':'10px'}, style_header={'backgroundColor':'#404040','fontWeight':'bold'}, page_size=20, sort_action='native')

@callback([Output("f-regional", "value"), Output("f-terminal", "value"), Output("f-type", "value"), Output("f-tahun", "value"), Output("f-status", "value")], Input("btn-reset", "n_clicks"), prevent_initial_call=True)
def reset_filters(n): return None, None, None, None, None


# ===========================================
# Trends Page Callbacks
# ===========================================

@callback([Output("chart-trend-monthly", "figure"), Output("chart-cat-compare", "figure"), Output("chart-cat-pct", "figure")], [Input("interval", "n_intervals")])
def update_trends(n):
    monthly = fetch_monthly_realization()
    cats = fetch_investment_by_category()
    
    if monthly:
        months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']
        vals = [float(monthly.get(m.lower()) or 0) for m in ['januari','februari','maret','april','mei','juni','juli','agustus','september','oktober','november','desember']]
        f1 = go.Figure(go.Scatter(x=months, y=vals, mode='lines+markers', fill='tozeroy', line=dict(color='#3498db', width=3)))
        f1.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40,r=40,t=20,b=40))
    else:
        f1 = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    if cats:
        dc = pd.DataFrame(cats)
        f2 = go.Figure()
        f2.add_trace(go.Bar(name='RKAP', x=dc['asset_categories'], y=dc['total_rkap'], marker_color='#3498db'))
        f2.add_trace(go.Bar(name='Realisasi', x=dc['asset_categories'], y=dc['total_realisasi'], marker_color='#2ecc71'))
        f2.update_layout(barmode='group', template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40,r=20,t=20,b=80))
        
        dc['cap'] = dc.apply(lambda r: (r['total_realisasi']/r['total_rkap']*100) if r['total_rkap']>0 else 0, axis=1)
        f3 = go.Figure(go.Bar(x=dc['asset_categories'], y=dc['cap'], marker_color=['#2ecc71' if c>=50 else '#e74c3c' for c in dc['cap']], text=[f'{c:.1f}%' for c in dc['cap']], textposition='outside'))
        f3.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40,r=20,t=40,b=80))
    else:
        f2 = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
        f3 = go.Figure().update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    
    return f1, f2, f3


# ===========================================
# Map Page Callback
# ===========================================

@callback(Output("full-map", "figure"), [Input("interval", "n_intervals")])
def update_map(n):
    projects = fetch_projects()
    df = pd.DataFrame(projects) if projects else pd.DataFrame()
    if not df.empty and 'latitude' in df.columns:
        dm = df.dropna(subset=['latitude','longitude'])
        if not dm.empty:
            fig = px.scatter_mapbox(dm, lat='latitude', lon='longitude', hover_name='project_definition', hover_data=['klaster_regional','status_investasi','rkap'], color='status_investasi', zoom=5, height=600)
            fig.update_layout(mapbox_style='carto-darkmatter', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=0,b=0))
            return fig
    fig = go.Figure()
    fig.add_annotation(text="No location data", showarrow=False, font=dict(size=20))
    fig.update_layout(template='plotly_dark', paper_bgcolor='rgba(0,0,0,0)')
    return fig


# ===========================================
# Run Server
# ===========================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)
