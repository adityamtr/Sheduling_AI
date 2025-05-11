import pandas as pd
import sqlite3
import os


class SQLiteDB:
    def __init__(self, db_path="data/database/poc.db"):
        self.db_path = db_path
        self.conn = self._connect()
        self.csvs = {"customer": "data/demo_data/input/customer_table.csv",
                     "product": "data/demo_data/input/product_table.csv",
                     "salesrep": "data/demo_data/input/salesrep_table.csv",
                     "kpi": "data/demo_data/output/transcript_extracted_kpi_table.csv"}
        self.load_multiple_csvs()

    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def close(self):
        if self.conn:
            self.conn.close()

    def load_csv(self, table_name, csv_path, if_exists='replace'):
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, self.conn, if_exists=if_exists, index=False)
            print(f"Loaded '{csv_path}' into table '{table_name}'")
        else:
            print(f"File not found: {csv_path}")

    def load_multiple_csvs(self, csv_mapping=None):
        if not csv_mapping:
            csv_mapping = self.csvs
        for table, path in csv_mapping.items():
            self.load_csv(table, path)

    def fetch(self, query, params=None):
        try:
            df = pd.read_sql_query(query, self.conn, params=params or {})
            return df
        except Exception as e:
            print(f"Fetch error: {e}")
            return None

    def fetch_json(self, query_dict):
        table = query_dict["table"]
        columns = ", ".join(query_dict.get("columns", ["*"]))
        where_clause = ""
        params = []

        if "where" in query_dict and query_dict["where"]:
            conditions = []
            for key, value in query_dict["where"].items():
                conditions.append(f"{key} = ?")
                params.append(value)
            where_clause = "WHERE " + " AND ".join(conditions)

        order_clause = ""
        if "order_by" in query_dict:
            order_clause = "ORDER BY " + ", ".join(query_dict["order_by"])

        limit_clause = f"LIMIT {query_dict['limit']}" if "limit" in query_dict else ""

        sql = f"SELECT {columns} FROM {table} {where_clause} {order_clause} {limit_clause}".strip()
        try:
            df = pd.read_sql_query(sql, self.conn, params=params)
            return df
        except Exception as e:
            print(f"Error in fetch_json: {e}")
            return None

    def execute(self, query, params=None):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            self.conn.commit()
            print("Executed successfully.")
        except Exception as e:
            print(f"Execution error: {e}")

    def insert(self, table, data_dict):
        columns = ', '.join(data_dict.keys())
        placeholders = ', '.join(['?'] * len(data_dict))
        values = tuple(data_dict.values())
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        self.execute(query, values)

    def update(self, table, update_dict, where_clause, where_params):
        set_clause = ', '.join([f"{k}=?" for k in update_dict.keys()])
        values = list(update_dict.values()) + list(where_params)
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        self.execute(query, values)

    def delete(self, table, where_clause, where_params):
        query = f"DELETE FROM {table} WHERE {where_clause}"
        self.execute(query, where_params)


# Example usage
if __name__ == "__main__":
    csvs = {
        'users': 'users.csv',
        'orders': 'orders.csv'
    }

    db = SQLiteDB()
    db.load_multiple_csvs(csvs)

    print("\nPreview of 'users' table:")
    print(db.fetch("SELECT * FROM users LIMIT 5"))

    query = {
        "table": "users",
        "columns": ["id", "name"],
        "where": {"name": "Alice"},
        "order_by": ["id DESC"],
        "limit": 5
    }

    result = db.fetch_json(query)
    print(result)

    db.insert('users', {'name': 'Dave', 'email': 'dave@example.com'})
    query = {
        "table": "users",
        "columns": ["id", "name"],
        "where": {"name": "Alice"},
        "order_by": ["id DESC"],
        "limit": 5
    }

    result = db.fetch_json(query)
    db.update('users', {'email': 'new_dave@example.com'}, 'name = ?', ['Dave'])
    db.delete('users', 'name = ?', ['Dave'])

    db.close()
