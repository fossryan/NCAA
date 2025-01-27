from dash import Dash, dash_table, dcc, html
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Function to scrape NCAA NET Rankings
def fetch_ncaa_net_rankings():
    url = "https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Locate the rankings table
        table = soup.find("table")
        if not table:
            raise ValueError("No rankings table found on the page.")

        # Extract headers and rows
        headers = [header.text.strip() for header in table.find_all("th")]
        rows = table.find_all("tr")[1:]  # Skip the header row

        data = []
        for row in rows:
            cells = row.find_all("td")
            if cells:
                columns = [cell.text.strip() for cell in cells]
                data.append(columns)

        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)
        return df
    except Exception as e:
        print(f"Error while fetching data: {e}")
        return pd.DataFrame()


# Initialize the Dash app
app = Dash(__name__)

# Fetch the data
rankings_df = fetch_ncaa_net_rankings()

# If data is empty, create a placeholder DataFrame
if rankings_df.empty:
    print("No data was retrieved. Please check the NCAA rankings page.")
    rankings_df = pd.DataFrame({"Rank": [], "Team": [], "Conference": [], "Overall": []})  # Placeholder with key columns

# Layout for the Dash app
app.layout = html.Div(
    children=[
        html.H1("NCAA Men's Basketball NET Rankings", style={"textAlign": "center"}),

        # Table
        dash_table.DataTable(
            id="rankings-table",
            columns=[{"name": col, "id": col} for col in rankings_df.columns],
            data=rankings_df.to_dict("records"),
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


# Run the Dash app
if __name__ == "__main__":
    app.run_server(debug=True)
