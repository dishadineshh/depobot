import pandas as pd

def load_public_sheet(sheet_id):
    # Public Google Sheet CSV URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    df = pd.read_csv(csv_url)
    return df
