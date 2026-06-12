import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# Set path
os.chdir(r"C:\Users\srira\OneDrive\Desktop\bluestock_project")

# Load data
nav_df = pd.read_csv("data/processed/nav_history_clean.csv")
aum_df = pd.read_csv("data/processed/aum_by_fund_house_clean.csv")
sip_df = pd.read_csv("data/processed/monthly_sip_inflows_clean.csv")
category_df = pd.read_csv("data/processed/category_inflows_clean.csv")
transactions_df = pd.read_csv("data/processed/investor_transactions_clean.csv")
folio_df = pd.read_csv("data/processed/industry_folio_count_clean.csv")
portfolio_df = pd.read_csv("data/processed/portfolio_holdings_clean.csv")
fund_master_df = pd.read_csv("data/processed/fund_master_clean.csv")
scorecard_df = pd.read_csv("reports/fund_scorecard.csv")
alpha_beta_df = pd.read_csv("reports/alpha_beta.csv")
benchmark_df = pd.read_csv("data/processed/benchmark_indices_clean.csv")

# Convert dates
nav_df['date'] = pd.to_datetime(nav_df['date'])
aum_df['date'] = pd.to_datetime(aum_df['date'])
sip_df['month'] = pd.to_datetime(sip_df['month'])
folio_df['month'] = pd.to_datetime(folio_df['month'])
benchmark_df['date'] = pd.to_datetime(benchmark_df['date'])
aum_df['year'] = aum_df['date'].dt.year

# ── Charts ──────────────────────────────────────────────────────────────────

# Page 1
total_aum = aum_df.groupby('date')['aum_crore'].sum()
aum_trend_fig = px.line(aum_df.groupby('date')['aum_crore'].sum().reset_index(),
                         x='date', y='aum_crore', title='Industry AUM Trend (2022–2025)')

aum_amc_fig = px.bar(aum_df.groupby('fund_house')['aum_crore'].mean().reset_index(),
                      x='fund_house', y='aum_crore', title='AUM by AMC')

folio_fig = px.line(folio_df, x='month', y='total_folios_crore', title='Folio Count Growth')

# Page 2
sip_benchmark = sip_df.copy()
nifty50 = benchmark_df[benchmark_df['index_name'] == 'NIFTY50'].copy()
dual_fig = go.Figure()
dual_fig.add_trace(go.Bar(x=sip_df['month'], y=sip_df['sip_inflow_crore'], name='SIP Inflow'))
dual_fig.add_trace(go.Scatter(x=nifty50['date'], y=nifty50['close_value'], name='Nifty 50', yaxis='y2'))
dual_fig.update_layout(title='SIP Inflow vs Nifty 50',
                        yaxis2=dict(overlaying='y', side='right'))

category_df['month'] = pd.to_datetime(category_df['month'])
cat_pivot = category_df.pivot_table(index='category', columns=category_df['month'].dt.strftime('%b %Y'), values='net_inflow_crore', aggfunc='sum')
heatmap_fig = px.imshow(cat_pivot, title='Category Inflow Heatmap', aspect='auto', color_continuous_scale='YlGn')

top5_cat = category_df.groupby('category')['net_inflow_crore'].sum().nlargest(5).reset_index()
top5_fig = px.bar(top5_cat, x='category', y='net_inflow_crore', title='Top 5 Categories by Net Inflow')

# Page 3
state_fig = px.bar(transactions_df.groupby('state')['amount_inr'].sum().reset_index().sort_values('amount_inr'),
                    x='amount_inr', y='state', orientation='h', title='Transaction Amount by State')

donut_fig = px.pie(transactions_df, names='transaction_type', title='SIP/Lumpsum/Redemption Split', hole=0.4)

age_fig = px.bar(transactions_df[transactions_df['transaction_type']=='SIP'].groupby('age_group')['amount_inr'].mean().reset_index(),
                  x='age_group', y='amount_inr', title='Avg SIP Amount by Age Group')

# Page 4
scatter_df = scorecard_df.copy()
scatter_fig = px.scatter(alpha_beta_df, x='alpha', y='beta',
                          hover_name='scheme_name',
                          title='Alpha vs Beta — All Funds',
                          size_max=20)

# ── App Layout ───────────────────────────────────────────────────────────────

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([

    html.H1("🏦 Bluestock Mutual Fund Dashboard", className="text-center my-3",
            style={'color': '#1a3c6e', 'fontWeight': 'bold'}),

    dbc.Tabs([

        # PAGE 1 - Industry Overview
        dbc.Tab(label='📊 Industry Overview', children=[
            dbc.Row([
                dbc.Col(dbc.Card([dbc.CardBody([html.H4("Total AUM"), html.H2("₹81L Cr")])], color="primary", inverse=True)),
                dbc.Col(dbc.Card([dbc.CardBody([html.H4("SIP Inflows"), html.H2("₹31K Cr")])], color="success", inverse=True)),
                dbc.Col(dbc.Card([dbc.CardBody([html.H4("Folios"), html.H2("26.12 Cr")])], color="warning", inverse=True)),
                dbc.Col(dbc.Card([dbc.CardBody([html.H4("Schemes"), html.H2("1,908")])], color="danger", inverse=True)),
            ], className="my-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=aum_trend_fig), width=8),
                dbc.Col(dcc.Graph(figure=folio_fig), width=4),
            ]),
            dcc.Graph(figure=aum_amc_fig),
        ]),

        # PAGE 2 - SIP & Market Trends
        dbc.Tab(label='📈 SIP & Market Trends', children=[
            dcc.Graph(figure=dual_fig),
            dcc.Graph(figure=heatmap_fig),
            dcc.Graph(figure=top5_fig),
        ]),

        # PAGE 3 - Investor Analytics
        dbc.Tab(label='👥 Investor Analytics', children=[
            dbc.Row([
                dbc.Col(dcc.Graph(figure=state_fig), width=8),
                dbc.Col(dcc.Graph(figure=donut_fig), width=4),
            ]),
            dcc.Graph(figure=age_fig),
        ]),

        # PAGE 4 - Fund Performance
        dbc.Tab(label='🏆 Fund Performance', children=[
            dcc.Graph(figure=scatter_fig),
            dash_table.DataTable(
                data=scorecard_df[['scheme_name', 'score', 'CAGR_3yr']].round(2).to_dict('records'),
                columns=[{'name': i, 'id': i} for i in ['scheme_name', 'score', 'CAGR_3yr']],
                sort_action='native',
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'backgroundColor': '#1a3c6e', 'color': 'white', 'fontWeight': 'bold'},
            ),
        ]),

    ]),

], fluid=True)

if __name__ == '__main__':
    app.run(debug=True)