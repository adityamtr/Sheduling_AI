import pandas as pd
import json
import ast
from services.dialog_service import Agent_Orchestrator
from services.agentic import AgentGenerateKPIs

## Loading client and meeting data
dummy_data = pd.read_csv('data/proc/clients_trascript_summary_v2.csv')
inventory_mapping = pd.read_csv('data/raw_2/inventory_mapping.csv')
products_markdown = inventory_mapping[['Product Name', 'Product Type']].to_markdown()

rows = []
final = pd.DataFrame()
## Loop to generate query for transcript agent and extract kpis
for index, row in dummy_data.iterrows():
    print(f"{index}/{len(dummy_data)}")
    query = f"""
    Products table:

    {products_markdown}

    """
    query += f"""Meeting Transcripts:\n\n{row["transcript"]}"""

    new_row = row.to_dict()

    ## Calling kpi agent
    orchestrator = Agent_Orchestrator(prompt_func=AgentGenerateKPIs().prompt_func,  is_json_response = AgentGenerateKPIs().prompt_response_schema())
    res = orchestrator.run(query)
    print(res)
    try:
        generated_kpis = json.loads(res)
    except:
        generated_kpis = ast.literal_eval(res)

    new_row.update(generated_kpis)
    rows.append(new_row)


    final = pd.DataFrame(rows)
    final.to_csv('data/proc/clients_trascript_summary_kpis.csv', index=False)

final.to_csv('data/proc/clients_trascript_summary_kpis.csv', index=False)

