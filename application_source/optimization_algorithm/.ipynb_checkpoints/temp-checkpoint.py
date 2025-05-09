import os
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime

def set_working_directory(path: str):
    os.chdir(path)
    print(f"Working directory set to: {os.getcwd()}")
    return os.listdir(path)

def load_data(file_path: str):
    loaded_df = pd.read_csv(file_path)
    return loaded_df

def process_meeting_dates(meeting_df: pd.DataFrame):
    meeting_df["Meeting Timestamp"] = pd.to_datetime(
        meeting_df["Meeting Timestamp"], format="%Y-%m-%d %I:%M %p"
    )
    latest_meetings = (
        meeting_df.groupby("Customer ID")["Meeting Timestamp"]
        .max()
        .reset_index()
        .rename(columns={"Meeting Timestamp": "Last Meeting Date"})
    )
    return latest_meetings

def enrich_customer_data(customer_df: pd.DataFrame, latest_meetings: pd.DataFrame, today: pd.Timestamp):
    customer_df = customer_df.drop(['Last Meeting Date'], axis=1)
    customer_df["Last Purchase Date"] = pd.to_datetime(customer_df["Last Purchase Date"], format="%Y-%m-%d")
    df = customer_df.merge(latest_meetings, on="Customer ID", how="left")
    df["Days Since Last Meeting"] = (today - df["Last Meeting Date"]).dt.days
    df["Days Since Last Purchase"] = (today - df["Last Purchase Date"]).dt.days
    return df

def add_meeting_outcomes(df: pd.DataFrame, meeting_df: pd.DataFrame):
    latest_outcomes = (
        meeting_df.sort_values("Meeting Timestamp")
        .groupby("Customer ID")
        .tail(1)[["Customer ID", "Meeting Outcome"]]
    )
    df = df.merge(latest_outcomes, on="Customer ID", how="left")
    df["Needs Follow-up"] = df["Meeting Outcome"].apply(
        lambda x: 1 if "follow-up" in str(x).lower() or "approval" in str(x).lower() else 0
    )
    return df

def compute_priority_score(df: pd.DataFrame, weights: dict = None):
    if weights is None:
        weights = {
            "Days Since Last Meeting": 0.3,
            "Days Since Last Purchase": 0.3,
            "Purchase Freq/Q": 0.1,
            "Last 12M Revenue ($)": 0.2,
            "Needs Follow-up": 0.1
        }

    scaler = MinMaxScaler()
    columns = list(weights.keys())

    # Invert specified columns
    if "Purchase Freq/Q" in df.columns:
        df["Purchase Freq/Q"] = 1 / (df["Purchase Freq/Q"] + 1e-5)
    if "Last 12M Revenue ($)" in df.columns:
        df["Last 12M Revenue ($)"] = 1 / (df["Last 12M Revenue ($)"] + 1e-5)

    normalized = pd.DataFrame(scaler.fit_transform(df[columns]), columns=columns)

    df["Priority Score"] = sum(normalized[col] * weight for col, weight in weights.items())
    return df


def get_top_customers(df: pd.DataFrame, top_n=2):
    top_priority = (
        df.sort_values(["Sales Rep ID", "Priority Score"], ascending=[True, False])
        .groupby("Sales Rep ID")
        .head(top_n)[["Sales Rep ID", "Customer ID", "Customer Name", "Priority Score"]]
    )
    return top_priority

def main():
    folder_path = '/Users/'  # Update as needed
    today = pd.to_datetime("2025-05-08")

    files = set_working_directory(folder_path)
    print("Files in directory:", files)

    customer_df, meeting_df = load_data("customer_data.csv", "enhanced_sales_meeting_history.csv")
    latest_meetings = process_meeting_dates(meeting_df)
    enriched_df = enrich_customer_data(customer_df, latest_meetings, today)
    enriched_df = add_meeting_outcomes(enriched_df, meeting_df)
    scored_df = compute_priority_score(enriched_df)
    top_customers = get_top_customers(scored_df)

    top_customers.to_csv("priority_df.csv", index=False)
    print("Top customer priorities exported to priority_df.csv")

# if __name__ == "__main__":
#     main()
