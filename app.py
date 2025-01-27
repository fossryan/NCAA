from flask import Flask, render_template_string
from dash import Dash, html, dash_table, dcc
from dash.dependencies import Input, Output
import requests
from bs4 import BeautifulSoup
import pandas as pd


# Initialize Flask app
flask_app = Flask(__name__)

# Function to create a Dash app
def create_dash_app(flask_server, route, fetch_function, title):
    app = Dash(__name__, server=flask_server, url_base_pathname=route)
    
    # Fetch data using the provided function
    df = fetch_function()

    # Layout for the Dash app
    app.layout = html.Div(
        children=[
            html.H1(title, style={"textAlign": "center"}),

            # Filters
            html.Div(
                [
                    dcc.Dropdown(
                        id=f"{route}-stat-filter",
                        options=[
                            {"label": col, "value": col} for col in df.columns if col not in ["Rank", "Team"]
                        ],
                        multi=True,
                        placeholder="Select Stats to Compare",
                        style={"width": "60%", "margin": "auto", "padding": "10px"},
                    )
                ]
            ),

            # Graph
            dcc.Graph(id=f"{route}-graph"),

            # Table
            dash_table.DataTable(
                id=f"{route}-table",
                columns=[{"name": col, "id": col} for col in df.columns],
                data=df.to_dict("records"),
                page_size=50,
                sort_action="native",
                filter_action="native",
                style_table={"margin": "20px auto", "width": "90%"},
                style_header={"backgroundColor": "#333", "color": "white", "fontWeight": "bold"},
                style_cell={"textAlign": "center", "padding": "10px"},
            ),
        ],
        style={"fontFamily": "Arial, sans-serif", "backgroundColor": "#f9f9f9", "padding": "20px"},
    )

    # Callbacks for graph update
    @app.callback(
        Output(f"{route}-graph", "figure"),
        [Input(f"{route}-stat-filter", "value")]
    )
    def update_graph(selected_stats):
        if not selected_stats:
            return {
                "data": [],
                "layout": {"title": "Select Stats to Display", "xaxis": {"title": "Team"}, "yaxis": {"title": "Value"}}
            }

        figure = {
            "data": [
                {"x": df["Team"], "y": df[stat], "type": "bar", "name": stat}
                for stat in selected_stats if stat in df.columns
            ],
            "layout": {
                "title": "Comparison of Selected Stats",
                "xaxis": {"title": "Team"},
                "yaxis": {"title": "Value"},
                "barmode": "group",
            },
        }
        return figure

    return app

# Fetch functions for each dashboard
def fetch_ncaa_net_rankings():
    url = "https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    headers = [header.text.strip() for header in table.find_all("th")]
    rows = table.find_all("tr")[1:]
    data = [[cell.text.strip() for cell in row.find_all("td")] for row in rows]
    return pd.DataFrame(data, columns=headers)

def fetch_ncaa_team_stats():
    url = "https://www.ncaa.com/stats/basketball-men/d1/current/team/148"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    headers = [header.text.strip() for header in table.find_all("th")]
    rows = table.find_all("tr")[1:]
    data = [[cell.text.strip() for cell in row.find_all("td")] for row in rows]
    return pd.DataFrame(data, columns=headers)

def fetch_shooting_percentage():
    url = "https://www.teamrankings.com/ncaa-basketball/stat/shooting-pct"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    headers = [header.text.strip() for header in table.find_all("th")]
    rows = table.find_all("tr")[1:]
    data = [[cell.text.strip() for cell in row.find_all("td")] for row in rows]
    return pd.DataFrame(data, columns=headers)

def fetch_avg_points_per_game():
    url = "https://www.teamrankings.com/ncaa-basketball/stat/points-per-game"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    headers = [header.text.strip() for header in table.find_all("th")]
    rows = table.find_all("tr")[1:]
    data = [[cell.text.strip() for cell in row.find_all("td")] for row in rows]
    return pd.DataFrame(data, columns=headers)

def fetch_three_point_percentage():
    url = "https://www.teamrankings.com/ncaa-basketball/stat/three-point-pct"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    headers = [header.text.strip() for header in table.find_all("th")]
    rows = table.find_all("tr")[1:]
    data = [[cell.text.strip() for cell in row.find_all("td")] for row in rows]
    return pd.DataFrame(data, columns=headers)

# Create Dash apps for each route
create_dash_app(flask_app, "/net-rankings/", fetch_ncaa_net_rankings, "NCAA NET Rankings")
create_dash_app(flask_app, "/team-stats/", fetch_ncaa_team_stats, "NCAA Team Stats")
create_dash_app(flask_app, "/shooting-pct/", fetch_shooting_percentage, "Shooting Percentage")
create_dash_app(flask_app, "/avg-points-per-game/", fetch_avg_points_per_game, "Average Points Per Game")
create_dash_app(flask_app, "/three-point-pct/", fetch_three_point_percentage, "3-Point Percentage")

# Main Flask route
@flask_app.route("/")
def index():
    return render_template_string("""
    <h1>Welcome to the NCAA Basketball Dashboard</h1>
    <p>Select a dashboard to view and compare statistics:</p>
    <ul>
        <li><a href="/net-rankings/">NCAA NET Rankings</a></li>
        <li><a href="/team-stats/">Team Stats</a></li>
        <li><a href="/shooting-pct/">Shooting Percentage</a></li>
        <li><a href="/avg-points-per-game/">Average Points Per Game</a></li>
        <li><a href="/three-point-pct/">3-Point Percentage</a></li>
    </ul>
    """)

if __name__ == "__main__":
    flask_app.run(debug=True)
