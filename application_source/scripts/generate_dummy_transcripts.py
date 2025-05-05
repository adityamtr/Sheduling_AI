import pandas as pd
from services.dialog_service import Agent_Orchestrator
from services.agentic import Agent_Generate_Interaction, Agent_Generate_Summary

## Loading client and meeting data
clients = pd.read_csv('data/raw/clients.csv')
meeting_notes = pd.read_csv('data/raw/meeting_notes.csv')

df = pd.merge(clients, meeting_notes, on='client_id', how='left')

final = pd.DataFrame()
## Loop to generate query for transcript agent and generate transcript + summarization
for user in df['client_id'].unique().tolist():
    temp = df[df['client_id'] == user].reset_index()
    query = ""
    name = ""
    for index, row in temp.iterrows():
        if index == 0:
            name = row['name']
            client_type = row['client_type']
            print(f"ID: {user}, Name: {name}")
            query += f"""Customer Profile:\nName: {name}\nClient Type: {client_type}\n\nConversation Flow:\n"""
        meeting_text = row['meeting_text']
        sentiment = row['sentiment']

        query += f"""step {index+1}: {meeting_text} - customer sentiment :{sentiment}\n"""

    ## Calling transcript agent
    orchestrator = Agent_Orchestrator(prompt_func=Agent_Generate_Interaction().prompt_func)
    generated_transcript = orchestrator.run(query)

    ## Calling summarization agent
    orchestrator = Agent_Orchestrator(prompt_func=Agent_Generate_Summary().prompt_func)
    summary = orchestrator.run(query)

    final = pd.concat([final,
                       pd.DataFrame({"client_id":[user],
                                     "name":[name],
                                     "transcript":[generated_transcript],
                                     "summary":[summary]})],
                      ignore_index=True)
    final.to_csv('data/proc/clients_trascript_summary.csv', index=False)

final.to_csv('data/proc/clients_trascript_summary.csv', index=False)

