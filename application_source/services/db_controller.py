from datetime import datetime
from services.db_service import SQLiteDB
from services.singlton_arc import SingletonMeta

class DBController(metaclass=SingletonMeta):

    def __init__(self):
        self.db = SQLiteDB()

    def validate_seller(self, seller_id):
        query_dict = {
            "table": "salesrep",
            "columns": ["salesrep_id", "first_name", "last_name"],
            "where": {"salesrep_id": seller_id}
        }
        df = self.db.fetch_json(query_dict)
        df = df.drop_duplicates()

        if len(df) > 0 and df.iloc[0]['salesrep_id'] == seller_id:
            return True
        return False

    def get_customers_list(self, seller_id):
        customers_list = []
        query_dict = {
            "table": "customer",
            "columns": ["customer_id", "customer_name"],
            "where": {"associated_salesrep_id": seller_id}
        }

        associated_customers = self.db.fetch_json(query_dict)
        if len(associated_customers) > 0:
            customers_list = associated_customers["customer_name"].tolist()
            customers_list = [name.lower() for name in customers_list]

        return customers_list

    def get_products_table(self):
        query_dict = {
            "table": "product",
            "columns": ["product_name", "product_type"]
        }

        products_table = self.db.fetch_json(query_dict)
        return products_table.to_markdown()

    def insert_summary_kpi(self, seller_id, customer_name, transcript, summary, kpis):
        customer_name = customer_name.replace('_', ' ')
        customer_name = customer_name.title()
        query_dict = {
            "table": "customer",
            "columns": ["customer_id"],
            "where": {"associated_salesrep_id": seller_id, "customer_name": customer_name}
        }

        customer_data = self.db.fetch_json(query_dict)

        query_dict = {
            "table": "salesrep",
            "columns": ["salesrep_fullname"],
            "where": {"salesrep_id": seller_id}
        }

        seller_data = self.db.fetch_json(query_dict)
        seller_name = seller_data.iloc[0]['salesrep_fullname']

        if len(customer_data) > 0:

            now = datetime.now()
            formatted_time = now.strftime("%d-%m-%Y %H:%M")

            customer_id = customer_data.iloc[0]["customer_id"]
            record_dict = {"customer_id": customer_id,
                           "salesrep_id": seller_id,
                           "customer_name": customer_name,
                           "salesrep_fullname" : seller_name,
                           "timestamp": formatted_time,
                           "meet_type": "Video Call",
                           "transcript": transcript,
                           "summary" : summary
                           }

            for k, v in kpis.items():
                if isinstance(v, list):
                    kpis[k] = str(v)
            record_dict.update(kpis)

            self.db.insert(table="kpi", data_dict=record_dict)

    def get_optimization_requirements(self):

        query_dict = {
            "table": "customer",
        }
        customer_table = self.db.fetch_json(query_dict)

        query_dict = {
            "table": "kpi",
        }
        kpi_table = self.db.fetch_json(query_dict)

        return customer_table, kpi_table

