import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from datetime import date
from pathlib import Path
import logging
import argparse
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
root_path = os.getcwd().split('application_source')[0] + 'application_source'

def set_working_directory(path: str):
    os.chdir(path)
    logging.info(f"Working directory set to: {os.getcwd()}")
    return os.listdir(path)

def prepare_customer_score_data(
    cust_table_path: str,
    today: pd.Timestamp,
    customer_score_cols: list = None
) -> pd.DataFrame:
    if not os.path.exists(cust_table_path):
        raise FileNotFoundError(f"{cust_table_path} not found.")

    if customer_score_cols is None:
        customer_score_cols = [
            'customer_id',
            'customer_name',
            'associated_salesrep_id',
            'avg_annual_sales',
            'purchase_freq_per_qtr',
            'days_since_last_purchase',
            'days_since_last_meeting'
        ]

    logging.info("Loading customer data...")
    cust_df = pd.read_csv(cust_table_path)
    cust_df = add_days_since_last_col(cust_df, today, 'last_purchase_date', 'days_since_last_purchase')
    cust_df = add_days_since_last_col(cust_df, today, 'last_meeting_date', 'days_since_last_meeting')

    return cust_df[customer_score_cols]

def add_days_since_last_col(cust_df: pd.DataFrame, today: pd.Timestamp, last_date_col:str ,days_since_col: str):
    if days_since_col in list(cust_df.columns):
        cust_df = cust_df.drop([days_since_col], axis=1)
    cust_df[last_date_col] = pd.to_datetime(cust_df[last_date_col], format="%d-%m-%Y")
    cust_df[days_since_col] = (today - cust_df[last_date_col]).dt.days
    return cust_df

def process_transcript_kpis(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")

    logging.info("Loading transcript KPI data...")
    df = pd.read_csv(file_path)
    df['timestamp'] = pd.to_datetime(df['timestamp'], dayfirst=True)
    df = df.sort_values('timestamp')
    latest_df = df.groupby(['salesrep_id', 'customer_id'], as_index=False).last()

    latest_df.loc[:, "interested_in_product_a_or_e"] = latest_df["products_interested_list"].apply(
        lambda x: 1 if "producta" in str(x).lower() or "producte" in str(x).lower() else 0
    )

    sentiment_map = {
        "positive": 1.0,
        "neutral": 0.5,
        "negative": 0.0
    }
    latest_df["sentiment_score"] = latest_df["sentiment"].str.lower().map(sentiment_map)

    return latest_df[[
        'customer_id',
        'sentiment_score',
        'products_interested',
        'interested_in_product_a_or_e'
    ]]

def combine_customer_kpis(
    cust_df: pd.DataFrame,
    latest_kpi_df: pd.DataFrame,
    fill_values: dict = None
) -> pd.DataFrame:
    if fill_values is None:
        fill_values = {
            "sentiment_score": 0.5,
            "products_interested": 0,
            "interested_in_product_a_or_e": 0
        }

    logging.info("Combining customer and KPI data...")
    kpi_df = pd.merge(cust_df, latest_kpi_df, on='customer_id', how='left')

    for col, value in fill_values.items():
        if col in kpi_df.columns:
            kpi_df[col] = kpi_df[col].fillna(value)

    return kpi_df

def compute_priority_score(df: pd.DataFrame, weights: dict = None):
    if weights is None:
        weights = {
            "days_since_last_meeting": 0.2,
            "days_since_last_purchase": 0.2,
            "avg_annual_sales": 0.1,
            "purchase_freq_per_qtr": 0.1,
            "sentiment_score": 0.1,
            "products_interested": 0.2,
            "interested_in_product_a_or_e": 0.1
        }

    logging.info("Computing priority scores...")
    scaler = MinMaxScaler()
    columns = list(weights.keys())

    if "purchase_freq_per_qtr" in df.columns:
        df["purchase_freq_per_qtr"] = 1 / (df["purchase_freq_per_qtr"] + 1e-5)

    normalized = pd.DataFrame(scaler.fit_transform(df[columns]), columns=columns)

    df["priority_score"] = sum(normalized[col] * weight for col, weight in weights.items())
    return df

def get_top_customers_df(df: pd.DataFrame, top_n=2):
    logging.info("Getting top priority customers per sales rep...")
    top_priority = (
        df.sort_values(["associated_salesrep_id", "priority_score"], ascending=[True, False])
        .groupby("associated_salesrep_id")
        .head(top_n)[["associated_salesrep_id", "customer_id", "customer_name" ,"priority_score"]]
    )
    return top_priority

def get_priority_order(df, salesrep_id):
    filtered = df[df["associated_salesrep_id"] == salesrep_id]
    sorted_customers = filtered.sort_values(by="priority_score", ascending=False)
    return sorted_customers["customer_name"].tolist()

def main():
    import os
    parser = argparse.ArgumentParser(description="Compute and export customer priority scores.")
    parser.add_argument("--salesrep_id", type=str, required=True, help="Sales Representative ID")
    args = parser.parse_args()
    
    salesrep_id_param = args.salesrep_id

    folder_path = f'{root_path}/data/demo_data'#change
    today = date.today()
    today = pd.to_datetime(str(today))

    salesrep_table_path = folder_path + '/input/salesrep_table.csv'
    customer_table_path = folder_path + '/input/customer_table.csv'
    product_table_path = folder_path + '/input/product_table.csv'
    transcript_kpi_table_path = folder_path + '/output/transcript_extracted_kpi_table.csv'
    priority_table_path = folder_path + '/output/priority_table.csv'

    if not os.path.exists(customer_table_path):
        raise FileNotFoundError(f"{customer_table_path} not found.")

    print(f"Loading and processing data for Salesrep ID: {salesrep_id_param}")
    
    customer_df = prepare_customer_score_data(customer_table_path, today)
    latest_new_kpi_df = process_transcript_kpis(transcript_kpi_table_path)
    kpi_df = combine_customer_kpis(customer_df, latest_new_kpi_df)
    priority_df = compute_priority_score(kpi_df)

    assert not priority_df.empty, "Priority dataframe is empty."

    priority_df = get_top_customers_df(priority_df)
    ls = get_priority_order(priority_df, salesrep_id_param)

    priority_df.to_csv(priority_table_path, index=False)
    print("Top customer priorities exported to priority_table.csv")
    print("Order of priority customer names: ", ls)


if __name__ == "__main__":
    main()
