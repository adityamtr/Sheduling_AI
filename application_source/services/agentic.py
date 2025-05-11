import pandas as pd 

from pydantic import BaseModel
from typing import List, Literal, Optional


def strict_schema(schema):
    if not isinstance(schema, dict):
        return schema
    if "properties" in schema.keys():
        schema["additionalProperties"] = False
    for key, value in schema.items():
        value = strict_schema(value)
    return schema

class ContextMethods():

    def __init__(self):
        self.context = []

    def add_role(self, role = "user", content=None):
        self.context.append({"role": role, "content": content})

    def build_context(self):
        return self.context

class Agent_Generate_Interaction(ContextMethods):

    def __init__(self):
        self.context = []

    def prompt_response_schema(self):
        modelschema = ConversationAnalysis.model_json_schema()
        schema = strict_schema(modelschema)
        return False

    def prompt_func(self, user_input=None):

        self.add_role(role="system", content=self.role_defination())
        self.add_role(role="system", content=self.task_defination())
        self.add_role(role="user", content=self.user_input_defination(user_input))

        return self.build_context()


    def role_defination(self):

        prompt = f"""
        You are expert content generator. 
        You task is to generate a whole meeting transcript between a Sales Representative and Customer.
        """

        return prompt

    def task_defination(self):

        prompt = f"""
        
        You Task is:
        
        - Analyse details provides by user
        - Identify Customer Name, Sales Representative Name and other provided features
        - Generate a series of conversations between Customer and Sales Representative
        - Here Sales Representative is Trying to pitch/sell few products, product list will be provided
        - Generate transcript session of about 15 to 20 back and forth conversations with consideration of user provided instructions
        
        Important Notes:
        
        - Return proper format of conversation, refer following style
            ** Customer **: <Customer message here>
            ** Sales Rep **: <Sales Representative message here>
            
            ** Customer **: <Customer message here>
            ** Sales Rep **: <Sales Representative message here>
        - add provided product name and product at every mention of respective product in conversation
        - Return only generated conversations, nothing else is required
        - at least 10 conversation should be there in generated session transcript
            
        """

        return prompt

    def user_input_defination(self, data):

        prompt = f"""
        Here are product list, Customer profile details and Customer impressions,
        along with conversation flow to generate till end of session.
        conclusion of conversation is also provided, generate conversations accordingly.:
        
        {data}
        """

        return prompt


class Agent_Generate_Summary(ContextMethods):

    def __init__(self):
        self.context = []

    def prompt_response_schema(self):
        modelschema = ConversationAnalysis.model_json_schema()
        schema = strict_schema(modelschema)
        return False
    
    def prompt_func(self, user_input=None):
        self.add_role(role="system", content=self.role_defination())
        self.add_role(role="system", content=self.task_defination())
        self.add_role(role="user", content=self.user_input_defination(user_input))

        return self.build_context()

    def role_defination(self):
        prompt = f"""
        You are expert content analyser. 
        You task is to analyse a whole meeting transcript between a Sales Representative and Customer
        And provide summarization
        """

        return prompt

    def task_defination(self):
        prompt = f"""

        You Task is:

        - Analyse Conversations between Customer and Sales Representative
        - Identify useful business points and exchanges
        - Generate brief summary of conversations which includes
            1. Proper markdown format of headings and labels
            2. Primary points discussed
            3. Future scope discussed
            4. Insight which help advisor to be able to convince Customer

        Important Notes:

        - Return only generated summary, nothing else is required

        """

        return prompt

    def user_input_defination(self, data):
        prompt = f"""
        Here are transcript of meeting between Customer and Sales Representative:

        {data}
        """

        return prompt

class ConversationAnalysis(BaseModel):
        sentiment: Literal["Positive", "Negative", "Neutral"]
        products_marketed_list: List[str]
        products_marketed: int
        products_interested_list: List[str]
        products_interested: int

class AgentGenerateKPIs(ContextMethods):

    def __init__(self):
        self.context = []
        self.example = """{
                        "sentiment": "<sentiment here>",
                        "products_marketed_list": ["<product name> (<product type>)", "<product name> (<product type>)", "<product name> (<product type>)"],
                        "products_marketed": <count of elements in products_marketed_list>,
                        "products_interested_list": ["<product name> (<product type>)", "<product name> (<product type>)"],
                        "products_interested": <count of elements in products_interested_list>
                    }"""


    def prompt_response_schema(self):
        modelschema = ConversationAnalysis.model_json_schema()
        schema = strict_schema(modelschema)
        return schema

    def prompt_func(self, user_input=None):

        self.add_role(role="system", content=self.role_defination())
        self.add_role(role="system", content=self.task_defination())
        self.add_role(role="system", content=self.response_format())
        self.add_role(role="user", content=self.user_input_defination(user_input))

        return self.build_context()
    
    def role_defination(self):
        prompt = f"""
        You are expert content generator. 
        You task is to generate a list of KPIS from a whole meeting transcript between a Sales Representative and Customer.
        """
        return prompt
    
    def task_defination(self):
        prompt = f"""
        Your task is:
         - Analyse the conversations between a Sales Representative and a Customer.
         - Identify mentions of product in conversation (identify products listed in product table only)
         - Identify who has mentioned which product
         - Extract the following pointers (KPIs):
        
        Below each pointer is provided along with their data type, values that it accepts and its definition:

            1 - sentiment: string (Positive, Negative, Neutral) ->  Over all sentiment of the conversation (based on Customer's willingness to make purchase)
            2 - products_marketed_list: list -> Names of the products marketed or discussed by Sales Representative during the meeting in Python list format. 
            3 - products_marketed: int -> Number of elements in above generated products_marketed_list.
            4 - products_interested_list: list ->  Names of products the Customer seems to be genuinely interested in Python list format. 
            5 - products_interested: int -> Number of elements in above generated products_interested_list.
            
        Important Notes:
        - Products table will be given by user, identify these products only from transcript while generating above KPIs
        - while adding any product in response add in this format <Product Name> (<Product Type>), identify product name and product type from given products table
        """
        return prompt

    def response_format(self):

        prompt = f"""Provide the output in form of a JSON only. 

        Here is a provided Schema for the output to follow: 
        {ConversationAnalysis.model_json_schema()}

        Do not provide any other text or explanation. Only the JSON format is needed. 
        
        """
        return prompt
    
    def user_input_defination(self, data):
        prompt = f"""
        Here is product table and transcript of meeting between Customer and Sales Representative:

        {data}
        """

        return prompt


class CustomerDetails(BaseModel):
    customer_name: str
    priority_reason: str
    highlights_last_meeting: Optional[str] = None
    next_meeting_agenda: Optional[str] = None
    suggestions_next_meeting: Optional[str] = None

class Agent_Generate_Priority_Reasoning(ContextMethods):

    def __init__(self):
        self.context = []
        self.kpis_table = pd.read_csv("./data/demo_data/output/transcript_extracted_kpi_table.csv")
        self.example  = [{
            "customer_name": "John Doe",
            "priority_reason": "High engagement and strong past sales performance",
            "highlights_last_meeting": "Discussed pricing and expansion strategy",
            "next_meeting_agenda": "Review latest KPIs and align on next-quarter strategy",
            "suggestions_next_meeting": "Offer new promotional discounts based on buying trends"
        }, 
        {
            "customer_name": "Jenny Fin",
            "priority_reason": "Moderate engagement and medium past sales performance",
            "highlights_last_meeting": "Discussed pricing and expansion strategy",
            "next_meeting_agenda": "Review latest KPIs and align on next-quarter strategy",
            "suggestions_next_meeting": "Offer new promotional discounts based on buying trends"
        }]

    def prompt_response_schema(self):
        modelschema = ConversationAnalysis.model_json_schema()
        schema = strict_schema(modelschema)
        return False
    
    def prompt_func(self, user_input):
        self.add_role(role="system", content=self.role_defination())
        self.add_role(role="system", content=self.task_defination())
        self.add_role(role="system", content=self.response_format())
        self.add_role(role="user", content=self.user_input_defination(user_input))

        return self.build_context()
    
    def role_defination(self):
        prompt = f"""
        
        You are an expert Content generator & analyser.
        
        Your task is to analyse the contents/ details provided to you regarding various Customers of a Sales representative.
        Once analysed, you need to generate a few content based on these details accordingly. 
        """

        return prompt
    
    def task_defination(self):
        prompt = f"""
        For the Sales representative, you will be provided with the details of a few Customers. 
    
        Following are the details (KPIs) that each customer will have:

            - Customer_name: Name of the Customer. 
            - priority: Priority of the Customer according to custom Model ,
            - priority_score : Priority Score of the Customer according to custom Model,
            - summary: The call summary of the conversation. 
            - sentiment: The sentiment of the conversation.
            - products_marketed_list: Names of the products marketed or discussed by Sales Representative during the meeting in Python list format. 
            - products_interested_list: Names of products the Customer seems to be genuinely interested in Python list format. 

        You will also be provided with the Customer priority list and their respective priority scores. 

        As per the priority list and the KPI details provided to you, You will generate the following pointers for each of the Customers and return them back in form of list of JSONs.
        Each JSON element of the list will have the following fields:

            -1. Priority_reason: The detailed explanation providing the reason for the priority level and score for this customer based on the provided KPIs.
            -2. Highlights_last_meeting: Highlighting the key pointers of the previous meeting.
            -3. Next_meeting_agenda: Discuss about the agenda of the next meeting in details. 
            -4. Suggestions_next_meeting: Suggestions for the next meeting based on the Customer KPIs.

        Provide these details in form of a Python list only. No other text, or explanation is needed.
        NOTE:
        
            - The KPIs are the main reference pointers
            - Utilize Summary at the fullest to generate results
            - Be very descriptive while generating above points
            - Maintain Proper headers and labels, i want a markdown format of results you are generating
            - These needs to be presented in a UI so maintain proper markdown formats

        """

        return prompt
    
    def response_format(self):
        prompt = f"""
        The response format should be in form of a Python list. 
        The python list should comprise of the JSONs for each Customer. 
        
        Here is a Schema for an individual Customer JSON: 
        {CustomerDetails.model_json_schema()}

        So if there are 3 customers for a Sales representative, the response schema would be like:
        [{CustomerDetails.model_json_schema()}, {CustomerDetails.model_json_schema()}, {CustomerDetails.model_json_schema()}]

        NOTE:
        1. The example is just for you to get an idea of the response format. 
        2. Do NOT reply on the example for the data and facts.  only the KPIs are the main source of data. 
        """

        return prompt
    
    def user_input_defination(self, user_input):


        prompt = f"""
        Here are the details of the KPIs for the customers and there conversations with sales representative:
        
        {user_input}

        """

        return prompt


class Agent_Formatter(ContextMethods):

    def __init__(self):
        self.context = []

    def prompt_response_schema(self):
        return False

    def prompt_func(self, user_input=None):
        self.add_role(role="system", content=self.role_defination())
        self.add_role(role="system", content=self.task_defination())
        self.add_role(role="user", content=self.user_input_defination(user_input))

        return self.build_context()

    def role_defination(self):
        prompt = f"""
        You are expert content formatter. 
        You task is to analyse a whole given pointers and generated formatted output
        """

        return prompt

    def task_defination(self):
        prompt = f"""

        You Task is:

        - Analyse given pointers and generated formatted output
        - Generate proper explanations of points given, like complete sentences.
        - Generate response like a proper guided conversation, which sounds like human is talking.
        - Identify headings and labels and sections from given user input
        - Generate brief explanation that includes
            1. Proper markdown format of headings and labels
            2. Primary points discussed

        Important Notes:

        - Return only generated summary, nothing else is required

        """

        return prompt

    def user_input_defination(self, data):
        prompt = f"""
        Here is input content:

        {data}
        """

        return prompt


class Agent_Scheduler(ContextMethods):

    def __init__(self):
        self.context = []

    def prompt_response_schema(self):
        return False

    def prompt_func(self, user_input=None):
        self.add_role(role="system", content=self.role_defination())
        self.add_role(role="system", content=self.task_defination())
        self.add_role(role="user", content=self.user_input_defination(user_input))

        return self.build_context()

    def role_defination(self):
        prompt = f"""
        You are expert calender scheduler. 
        You task is to analyse a whole given priority information of customers.
        And generate meeting schedules for given date range.
        """

        return prompt

    def task_defination(self):
        prompt = f"""

        You Task is:

        - Analyse given priority data.
        - Analyse given free slots available from sellers calender.
        - Identify max Date Range.
        - Determine Optimal time slots to meet with each customer and generate schedule list.
        - The format for each element in schedule list should look like:
            **<client name here>** (Score: <client score here>): Suggest on **<meeting date here>** at Slot -> <start time here> to <end time here>
            like this generate list of elements where each elements is string of meeting slots details in above format.
        - While generating slot details, consider following default instructions:
            1. Schedule max 2 meeting in a day, one can be in morning and one can be in afternoon.
            2. Do note that seller might need to travel or need time to eat from one place to another so dont schedule consecutive meetings. keep at least one hour gaps.
            3. Avoid weekends (saturday and sunday) and holidays while scheduling.
            4. One meeting should be 1 hour long
        - User can provide his own custom instructions, so follow those as well.

        Important Notes:

        - Return only generated python list of slot details, nothing else is required
        - Also, if user has provided his instructions then give priority to those instructions over default instructions if there any conflicts between default and user provided instructions.
        - One Customer will be given only one meeting slot
        """

        return prompt

    def user_input_defination(self, data):
        prompt = f"""
        Here is input from user:

        {data}
        """

        return prompt


        



         

    
