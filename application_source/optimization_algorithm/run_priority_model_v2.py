import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from datetime import date
from pathlib import Path
import logging
import argparse
import os

from config.config import config
from services.db_controller import DBController
from services.singlton_arc import SingletonMeta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
root_path = os.getcwd().split('application_source')[0] + 'application_source'


class PriorityModel(metaclass=SingletonMeta):

    def __init__(self):
        self.db = DBController()
        self.visits_threshold = int(config.get('optimization', 'visits_threshold'))

    def prepare_customer_score_data(
            self,
            cust_table,
            today: pd.Timestamp,
            customer_score_cols: list = None
    ) -> pd.DataFrame:

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
        cust_df = cust_table
        cust_df = self.add_days_since_last_col(cust_df, today, 'last_purchase_date', 'days_since_last_purchase')
        cust_df = self.add_days_since_last_col(cust_df, today, 'last_meeting_date', 'days_since_last_meeting')

        return cust_df[customer_score_cols]


    def add_days_since_last_col(self, cust_df: pd.DataFrame, today: pd.Timestamp, last_date_col: str, days_since_col: str):
        if days_since_col in list(cust_df.columns):
            cust_df = cust_df.drop([days_since_col], axis=1)
        cust_df[last_date_col] = pd.to_datetime(cust_df[last_date_col], format="%d-%m-%Y")
        cust_df[days_since_col] = (today - cust_df[last_date_col]).dt.days
        return cust_df


    def process_transcript_kpis(self, kpi_table) -> pd.DataFrame:

        logging.info("Loading transcript KPI data...")
        df = kpi_table
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
            self,
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


    def compute_priority_score(self, df: pd.DataFrame, weights: dict = None):
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


    def get_top_customers_df(self, df: pd.DataFrame, top_n=2):
        logging.info("Getting top priority customers per sales rep...")
        top_priority = (
            df.sort_values(["associated_salesrep_id", "priority_score"], ascending=[True, False])
            .groupby("associated_salesrep_id")
            .head(top_n)[["associated_salesrep_id", "customer_id", "customer_name", "priority_score"]]
        )
        return top_priority


    def get_priority_order(self, df, salesrep_id):
        filtered = df[df["associated_salesrep_id"] == salesrep_id]
        sorted_customers = filtered.sort_values(by="priority_score", ascending=False)
        sorted_customers = sorted_customers.head(self.visits_threshold)
        return sorted_customers, sorted_customers["customer_name"].tolist()


    def run(self, seller_id):

        salesrep_id_param = seller_id

        today = date.today()
        today = pd.to_datetime(str(today))

        customer_table, kpi_table = self.db.get_optimization_requirements()

        print(f"Loading and processing data for Salesrep ID: {salesrep_id_param}")

        customer_df = self.prepare_customer_score_data(customer_table, today)
        latest_new_kpi_df = self.process_transcript_kpis(kpi_table)
        kpi_df = self.combine_customer_kpis(customer_df, latest_new_kpi_df)
        priority_df = self.compute_priority_score(kpi_df)

        assert not priority_df.empty, "Priority dataframe is empty."

        priority_df = self.get_top_customers_df(priority_df)
        priority_df, ls = self.get_priority_order(priority_df, salesrep_id_param)

        analysis = {}
        for i, row in priority_df.iterrows():
            analysis[row['customer_name']] = {'summary':"", 'score':round(row['priority_score']*100, 2)}

        analysis['priority_order'] = ls
        return analysis
