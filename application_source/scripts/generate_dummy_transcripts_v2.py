import pandas as pd
from services.dialog_service import Agent_Orchestrator
from services.agentic import Agent_Generate_Interaction, Agent_Generate_Summary

## Loading client and meeting data
clients = pd.read_csv('data/raw_2/customer_data.csv')
customer_to_sales_rep = pd.read_csv('data/raw_2/customer_to_sales_rep.csv')
meeting_notes = pd.read_csv('data/raw_2/enhanced_sales_meeting_history.csv')
inventory_mapping = pd.read_csv('data/raw_2/inventory_mapping.csv')

meeting_notes = meeting_notes[['Sales Rep ID', 'Customer ID', 'Meeting Timestamp', 'Meeting Notes', 'Meeting Outcome', 'Meeting Mode']]
inventory_mapping = inventory_mapping[['Product Name', 'Product Type']]

df = pd.merge(customer_to_sales_rep, meeting_notes, on=['Customer ID', 'Sales Rep ID'], how='outer')

final = pd.DataFrame()
## Loop to generate query for transcript agent and generate transcript + summarization
for index, row in df.iterrows():
    # print(row)
    query = ""
    client_id = row['Customer ID']
    sales_rep_id = row['Sales Rep ID']
    client_name = row['Customer Name']
    advisor_name = row['Sales Rep Name']
    timestamp = row['Meeting Timestamp']
    meet_type = row['Meeting Mode']
    query += f"Following is products list:\n\n{inventory_mapping[['Product Name', 'Product Type']].to_markdown()}"
    query += f"""\n\nCustomer Name: {client_name}\nSales Representative Name: {advisor_name}\n\nMeeting Type: {meet_type}\n\nConversation Flow:\n"""
    meeting_text = row['Meeting Notes']
    conclusion = row['Meeting Outcome']

    query += f"""{meeting_text}\n\nColnclusion : {conclusion}\n"""

    ## Calling transcript agent
    orchestrator = Agent_Orchestrator(prompt_func=Agent_Generate_Interaction().prompt_func)
    generated_transcript = orchestrator.run(query)

    ## Calling summarization agent
    orchestrator = Agent_Orchestrator(prompt_func=Agent_Generate_Summary().prompt_func)
    summary = orchestrator.run(query)

    final = pd.concat([final,
                       pd.DataFrame({"client_id":[client_id],
                                     "sales_rep_id": [sales_rep_id],
                                     "client_name": [client_name],
                                     "advisor_name": [advisor_name],
                                     "timestamp":[timestamp],
                                     "meet_type": [meet_type],
                                     "transcript":[generated_transcript],
                                     "summary":[summary]})],
                      ignore_index=True)
    final.to_csv('data/proc/clients_trascript_summary_v2.csv', index=False)

final.to_csv('data/proc/clients_trascript_summary_v2.csv', index=False)

