from dash import Dash, dash_table, dcc, html, Input, Output
import requests
from bs4 import BeautifulSoup
import pandas as pd


# Function to scrape NCAA team stats
def fetch_ncaa_team_stats():
    url = "https://www.ncaa.com/stats/basketball-men/d1/current/team/148"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Locate the stats table
        table = soup.find("table")
        if not table:
            raise ValueError("No stats table found on the page.")

        # Extract headers and rows
        headers = [header.text.strip() for header in table.find_all("th")]
        rows = table.find_all("tr")[1:]  # Skip the header row

        data = []
        for row in rows:
            cells = row.find_all("td")
            if cells:
                # Extract team name from <a> with class="school"
                team_cell = cells[1].find("a", class_="school")
                team_name = team_cell.text.strip() if team_cell else "Unknown Team"

                # Extract the remaining columns
                columns = [cell.text.strip() for cell in cells]
                columns[1] = team_name  # Replace the second column with the team name
                data.append(columns)

        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)

        # Ensure numeric columns are properly converted
        for col in headers[2:]:  # Assuming the first two columns are "Rank" and "Team"
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    except Exception as e:
        print(f"Error while fetching data: {e}")
        return pd.DataFrame()  # Return empty DataFrame on failure


# Initialize the Dash app
app = Dash(__name__)

# Fetch the data
team_stats_df = fetch_ncaa_team_stats()

# If data is empty, create a placeholder DataFrame
if team_stats_df.empty:
    print("No data was retrieved. Please check the NCAA stats page.")
    team_stats_df = pd.DataFrame({"Team": [], "Stats": []})  # Placeholder with key columns

# Layout for the Dash app
app.layout = html.Div(
    children=[
        html.H1("NCAA Men's Basketball Stats Dashboard", style={"textAlign": "center"}),

        # Filters
        html.Div(
            [
                dcc.Dropdown(
                    id="team-filter",
                    options=[
                        {"label": team, "value": team} for team in sorted(team_stats_df["Team"].unique())
                    ],
                    multi=True,
                    placeholder="Select Teams",
                    style={"width": "45%", "display": "inline-block", "margin-right": "10px"},
                ),
                dcc.Dropdown(
                    id="stat-filter",
                    options=[
                        {"label": col, "value": col} for col in team_stats_df.columns if col not in ["Rank", "Team"]
                    ],
                    multi=True,
                    placeholder="Select Stats to Compare",
                    style={"width": "45%", "display": "inline-block"},
                )
            ],
            style={"padding": "10px"},
        ),

        # Graph
        dcc.Graph(id="team-stats-graph"),

        # Table
        dash_table.DataTable(
            id="stats-table",
            columns=[{"name": col, "id": col} for col in team_stats_df.columns],
            data=team_stats_df.to_dict("records"),
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


# Callbacks for filtering and graphing
@app.callback(
    [Output("team-stats-graph", "figure"), Output("stats-table", "data")],
    [Input("team-filter", "value"), Input("stat-filter", "value")]
)
def update_dashboard(selected_teams, selected_stats):
    filtered_df = team_stats_df

    # Filter by team
    if selected_teams:
        filtered_df = filtered_df[filtered_df["Team"].isin(selected_teams)]

    # Update the graph
    if selected_stats:
        figure = {
            "data": [
                {
                    "x": filtered_df["Team"],
                    "y": filtered_df[stat],
                    "type": "bar",
                    "name": stat,
                }
                for stat in selected_stats
            ],
            "layout": {
                "title": "Comparison of Selected Stats",
                "xaxis": {"title": "Team"},
                "yaxis": {"title": "Value"},
                "barmode": "group",
            },
        }
    else:
        figure = {
            "data": [],
            "layout": {
                "title": "Select Stats to Display",
                "xaxis": {"title": "Team"},
                "yaxis": {"title": "Value"},
            },
        }

    return figure, filtered_df.to_dict("records")


# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
