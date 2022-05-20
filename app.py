import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html , dash_table
import dash
import psycopg2
import json
import random as rd
from numpy import random
from dash import dcc
import plotly.graph_objs as go
import pandas as pd
####################### Connections ########################
host = "psql-eppopay-qa-001.postgres.database.azure.com"
dbname = "eppopay-test"
user = "dbadmin@psql-eppopay-qa-001"
password = "j7n$5^Euzx0CbK"
sslmode = "require"
conn_string = "host={0} user={1} dbname={2} password={3} sslmode={4}".format(host, user, dbname, password, sslmode)
engine = psycopg2.connect(conn_string) 
print("Connection established 🦄")
cursor = engine.cursor()
df = pd.read_sql("select ac.id as account_id , ac.account_code as account_code , ac.account_name as account_name , su.id as property_id , su.sub_entity_name as property_name , ac.created_at from accounts ac join sub_entities su on ac.id = su.account_id where account_code not like 'Z%' order by ac.id", con=engine)
df2 = pd.read_sql("SELECT acc.id AS unique_customer_id , concat(left(acc.first_name, 1), left(acc.last_name, 1)) AS customer_abbreviated_name , act.id AS account_id , unique_account_number AS lease_id , un.id AS unit_id , su.id AS property_id , un.unit_name AS unit_name , ct.start_date AS start_date , ct.end_date AS end_date , ct.rent_amount AS rent_amount , ct.status , ep.rule_json ->> 'plan' AS payment_plan_name , ept.plan_type_name AS eppopay_plan_type FROM contracts ct INNER JOIN contract_account_customers cacc ON cacc.contract_id = ct.id INNER JOIN account_customers acc ON acc.id = cacc.account_customer_id INNER JOIN units un ON ct.unit_id = un.id INNER JOIN sub_entities su ON su.id = un.sub_entity_id INNER JOIN accounts act ON su.account_id = act.id INNER JOIN addresses ad ON ad.id = un.address_id INNER JOIN states st ON st.id = ad.state_id LEFT JOIN eppopay_plans ep ON ct.customer_preferred_payment_plan_id = ep.id LEFT JOIN eppopay_plan_types ept ON ept.id = ep.eppopay_plan_type_id WHERE act.account_code NOT LIKE 'Z%' AND (ct.end_date is null OR ct.end_date > current_date) ORDER BY act.id", con=engine)
df2.sort_values(by='start_date',ascending = False,inplace=True)
df3 = pd.read_sql("select ac.id as customer_unique_identifier , cup.id as customer_payment_id , 0 as customer_payment_arrears_id , amount as amount , (smoothing_fee - eppopay_commission) as property_fee , eppopay_commission as circa_fees , 0 as late_fee , amount + smoothing_fee as total_amount , payment_date , ct.id as lease_id , ac.account_id as account_id , case when coalesce(cup.global_payment_id,0) = 1 then 'Cash' else 'ACH' end , cop.merchant_due_date as due_month , cop.id as lease_monthly_payment_id , 'False' as is_arrear_payment , '' as is_failed_payment , '' as is_late_payment , cup.status as paymentstatus , 0 as arrear_revenue , 0 as credit_card_margin from customer_payments cup inner join contract_payments cop on cup.contract_payment_id = cop.id inner join contracts ct on ct.id = cop.contract_id inner join customers cu on cu.id = ct.customer_id inner join units un on ct.unit_id = un.id inner join sub_entities su on su.id = un.sub_entity_id inner join addresses ad on ad.id = un.address_id left join bank_accounts ba on ba.id = cup.bank_account_id inner join contract_account_customers cac on cac.contract_id = ct.id inner join account_customers ac on ac.id = cac.account_customer_id inner join accounts act on act.id = ct.account_id where act.account_code not like 'Z%' and cup.status in (2,3,4) union all select ac.id as customer_unique_identifier , cup.id as customer_payment_id , arr.id as customer_payment_arrears_id , arr.amount as amount , (late_fee - arr.eppopay_commission) as property_fee , arr.eppopay_commission as circa_fees , late_fee as late_fee , late_fee as total_amount , arr.payment_date , ct.id as lease_id , ac.account_id as account_id , case when coalesce(arr.global_payment_id,0) = 1 then 'Cash' else 'ACH' end , cop.merchant_due_date as due_month , cop.id as lease_monthly_payment_id , 'True' as is_arrear_payment , case when cup.status = 4 then 'True' else 'False' end as is_failed_payment , case when cup.status = 5 then 'True' else 'False' end as is_late_payment , arr.status as paymentstatus , 0 as arrear_revenue , 0 as credit_card_margin from customer_payment_arrears arr inner join customer_payments cup on cup.id = arr.customer_payment_id inner join contract_payments cop on cup.contract_payment_id = cop.id inner join contracts ct on ct.id = cop.contract_id inner join customers cu on cu.id = ct.customer_id inner join units un on ct.unit_id = un.id inner join sub_entities su on su.id = un.sub_entity_id inner join addresses ad on ad.id = un.address_id left join bank_accounts ba on ba.id = cup.bank_account_id inner join contract_account_customers cac on cac.contract_id = ct.id inner join account_customers ac on ac.id = cac.account_customer_id inner join accounts act on act.id = ct.account_id where act.account_code not like 'Z%' and arr.status in (2,3,4) order by payment_date", con=engine)
df3.sort_values(by='payment_date',ascending = False,inplace=True)
#############################################################
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
        "family=Poppins:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(external_stylesheets=["https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",external_stylesheets])
app.title = "Crica KPI Dashboard"
header = html.Div(
            children=[

                html.Img(src='https://images.squarespace-cdn.com/content/v1/5ff43b0269011948ff5fb388/1611912749253-394JV07FTMTZNXMHP5TL/Circa+temporary+logo.png',className="header-image"),
                html.P(
                    children="Analyze the behavior of avocado prices"
                    " and the number of avocados sold in the US"
                    " between 2015 and 2018",
                    className="header-description",
                ),
            ],
            className="header",
        )
########## CIRCA - CAMPAIGN TRACKER ##########
pipeline = [
    dbc.CardHeader("In Pipeline", className="card-header"),
    dbc.CardBody(
        [
            html.H5("{0}".format(rd.randint(500,1000)), className="card-title"),
            html.P(
                "Properties In The Pipeline",
                className="card-text",
            ),
        ]
    ),
]
try_circa = [
    dbc.CardHeader("Crica", className="card-header"),
    dbc.CardBody(
        [
            html.H5("{0}".format(rd.randint(500,1000)), className="card-title"),
            html.P(
                "Properties That Have Asked To Try Circa",
                className="card-text",
            ),
        ]
    ),
]
signed_contracts = [
    dbc.CardHeader("Signed Contracts", className="card-header"),
    dbc.CardBody(
        [
            html.H5("{0}".format(rd.randint(500,1000)), className="card-title"),
            html.P(
                "Properties That Signed Contracts",
                className="card-text",
            ),
        ]
    ),
]
properties_signed = [
    dbc.CardHeader("Properties Signed", className="card-header"),
    dbc.CardBody(
        [
            html.H5("{0}".format(rd.randint(500,1000)), className="card-title"),
            html.P(
                "Units In The Properties Signed",
                className="card-text",
            ),
        ]
    ),
]
CAMPAIGN_TRACKER = dbc.Row(
    [
        dbc.Col(dbc.Card(pipeline, color="secondary", outline=True, className='card')),
        dbc.Col(dbc.Card(try_circa, color="secondary", outline=True)),
        dbc.Col(dbc.Card(signed_contracts, color="secondary", outline=True)),
        dbc.Col(dbc.Card(properties_signed, color="secondary", outline=True)),
    ],
    className="mb-4",
)
CAMPAIGN_TRACKER_KPI = html.Div([CAMPAIGN_TRACKER])

########## UNIT RELATED KPI ##########
under_management = [
    dbc.CardHeader("Under Management", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10000,1000000)), className="card-title"),
            html.P(
                "This is some card content that we'll reuse",
                className="card-text",
            ),
        ]
    ),
]
using_circa = [
    dbc.CardHeader("Using Circa", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10000,1000000)), className="card-title"),
            html.P(
                "This is some card content that we'll reuse",
                className="card-text",
            ),
        ]
    ),
]
using_fps = [
    dbc.CardHeader("Using Flexible Payment Schedules", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10000,1000000)), className="card-title"),
            html.P(
                "This is some card content that we'll reuse",
                className="card-text",
            ),
        ]
    ),
]
UNIT_KPI_ROW = dbc.Row(
    [
        dbc.Col(dbc.Card(under_management, color="secondary", outline=True, className='card')),
        dbc.Col(dbc.Card(using_circa, color="secondary", outline=True)),
        dbc.Col(dbc.Card(using_fps, color="secondary", outline=True)),
    ],
    className="mb-4",
)
UNIT_KPI = html.Div([UNIT_KPI_ROW])
UNIT_KPI_GRAPH = dcc.Graph(
    figure={
        'data': [
            {'x': random.rand(5), 'y': random.rand(5), 'type': 'line', 'name': 'Under Management'},
            {'x': random.rand(5), 'y': random.rand(5), 'type': 'line', 'name': 'Using Circa'},
            {'x': random.rand(5), 'y': random.rand(5), 'type': 'line', 'name': 'Using Fps'},
        ],
        'layout': {
            'title': 'Unit Kpi Graph'
        },
    }
)
###########################################################################################
##################################### RENT RELATED KPI ####################################
total_rent_processed = [
    dbc.CardHeader("Total Rent Processed", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10000,1000000)), className="card-title"),
            html.P(
                "Total Rent Processed Using Circa",
                className="card-text",
            ),
        ]
    ),
]
rent_processed = [
    dbc.CardHeader("Rent Processed", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10000,1000000)), className="card-title"),
            html.P(
                "Rent Processed For Date",
                className="card-text",
            ),
        ]
    ),
]
saas_fees_collected = [
    dbc.CardHeader("Saas Fees Collected", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10000,1000000)), className="card-title"),
            html.P(
                "Saas Fees Collected For Date",
                className="card-text",
            ),
        ]
    ),
]

flexible_payment_fees = [
    dbc.CardHeader("Using Flexible Payment Schedules", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10000,1000000)), className="card-title"),
            html.P(
                "Flexible Payment Fees Collected For Date",
                className="card-text",
            ),
        ]
    ),
]
rentassist = [
    dbc.CardHeader("RentAssist/Arrears Fees", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10000,1000000)), className="card-title"),
            html.P(
                "Rentassist/Arrears Fees Collected For Date",
                className="card-text",
            ),
        ]
    ),
]
credit_reporting_fee = [
    dbc.CardHeader("RentAssist/Arrears Fees", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10000,1000000)), className="card-title"),
            html.P(
                "Credit Reporting Fee Collected For Date",
                className="card-text",
            ),
        ]
    ),
]
revenue_shared = [
    dbc.CardHeader("Revenue Shared With Properties", className="card-header"),
    dbc.CardBody(
        [
            html.H5("${:,.2f}".format(rd.randint(10057,1000032)), className="card-title"),
            html.P(
                "Credit Reporting Fee Collected For Date",
                className="card-text",
            ),
        ]
    ),
]
RENT_KPI_ROW_1 = dbc.Row(
    [
        dbc.Col(dbc.Card(total_rent_processed, color="secondary", outline=True, className='card')),
        dbc.Col(dbc.Card(rent_processed, color="secondary", outline=True)),
        dbc.Col(dbc.Card(saas_fees_collected, color="secondary", outline=True)),
        dbc.Col(dbc.Card(flexible_payment_fees, color="secondary", outline=True, className='card')),
    ],
    className="mb-4",
)
RENT_KPI_ROW_2 = dbc.Row(
    [
        dbc.Col(dbc.Card(rentassist, color="secondary", outline=True)),
        dbc.Col(dbc.Card(credit_reporting_fee, color="secondary", outline=True)),
        dbc.Col(dbc.Card(revenue_shared, color="secondary", outline=True)),
    ],
    className="mb-3",
)
RENT_KPI = html.Div([RENT_KPI_ROW_1 , RENT_KPI_ROW_2])
RENT_KPI_GRAPH = dcc.Graph(
    figure={
        'data': [
            {'x': random.rand(5), 'y': random.rand(5), 'type': 'line', 'name': 'Rent Processed'},
            {'x': random.rand(5), 'y': random.rand(5), 'type': 'line', 'name': 'SaaS Fees Collected'},
            {'x': random.rand(5), 'y': random.rand(5), 'type': 'line', 'name': 'Flexible Payment Fees'},
            {'x': random.rand(5), 'y': random.rand(5), 'type': 'line', 'name': 'RentAssist/arrears Fees'},
            {'x': random.rand(5), 'y': random.rand(5), 'type': 'line', 'name': 'Credit Reporting Fee'},
            {'x': random.rand(5), 'y': random.rand(5), 'type': 'line', 'name': 'Revenue Shared'},
        ],
        'layout': {
            'title': 'Rent Kpi Graph'
        }
    }
)
######################################################################################

app.layout = html.Div(
    children=[
        html.Div(
            children=[

                html.Img(src='https://images.squarespace-cdn.com/content/v1/5ff43b0269011948ff5fb388/1611912749253-394JV07FTMTZNXMHP5TL/Circa+temporary+logo.png',className="header-image"),
                html.P(
                    children="Analyze the behavior of avocado prices"
                    " and the number of avocados sold in the US"
                    " between 2015 and 2018",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                     children=[
                        html.H2("Campaign Tracker KPI", className="csection"),
                        html.P(
                            children="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
                            className="section-description",
                        ),
                        CAMPAIGN_TRACKER_KPI
                               ]
            ),
            html.Div(
                     children=[
                        html.H2("Unit Related KPI", className="csection"),
                        html.P(
                            children="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
                            className="section-description",
                        ),
                        UNIT_KPI,UNIT_KPI_GRAPH
                               ]
            ),
            html.Div(
                    children=[
                        html.H2("Rent Related KPI", className="csection"),
                        html.P(
                            children="Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
                            className="section-description",
                        ),
                        RENT_KPI,RENT_KPI_GRAPH
                               ]
            )
            ],
            className="wrapper",
        )
    ]
)
        

if __name__ == "__main__":
    app.run_server(port=8080, debug=True)