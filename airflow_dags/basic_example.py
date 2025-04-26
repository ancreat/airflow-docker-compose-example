from airflow.sdk import dag, task
import json

@dag(schedule=None,tags=["example"])
def basic_pipeline():
    @task()
    def extract():
        transactions_data = '{"transactions":[{"amount":1},{"amount":2},{"amount":3}]}'
        return json.loads(transactions_data)

    @task(multiple_outputs=True)
    def transform(transactions: dict):
        amounts = [transaction["amount"] for transaction in transactions["transactions"]]
        return {
            "min": min(amounts),
            "max": max(amounts)
        }

    @task()
    def load(transformed_data: dict):
        print(f"Min transaction amount is: {transformed_data['min']}")
        print(f"Max transaction amount is: {transformed_data['max']}")

    extracted_data = extract()
    transformed_data = transform(extracted_data)
    load(transformed_data)
basic_pipeline()
