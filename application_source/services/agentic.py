from pydantic import BaseModel
from typing import List, Literal

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

    def prompt_func(self, user_input=None):

        self.add_role(role="system", content=self.role_defination())
        self.add_role(role="system", content=self.task_defination())
        self.add_role(role="user", content=self.user_input_defination(user_input))

        return self.build_context()


    def role_defination(self):

        prompt = f"""
        You are expert content generator. 
        You task is to generate a whole meeting transcript between a seller and Customer.
        """

        return prompt

    def task_defination(self):

        prompt = f"""
        
        You Task is:
        
        - Analyse details provides by user
        - Identify Customer Name, Seller Name and other provided features
        - Generate a series of conversations between Customer and Seller
        - Here Seller is Trying to pitch/sell few products, product list will be provided
        - Generate transcript session of about 20 to 25 back and forth conversations with consideration of user provided instructions
        
        Important Notes:
        
        - Return proper format of conversation, refer following style
            ** Customer **: <customer message here>
            ** Sales Rep **: <seller message here>
            
            ** Customer **: <customer message here>
            ** Sales Rep **: <seller message here>
        - add provided product name and product at every mention of respective product in conversation
        - Return only generated conversations, nothing else is required
        - at least 20 conversation should be there in generated session transcript
            
        """

        return prompt

    def user_input_defination(self, data):

        prompt = f"""
        Here are product list, customer profile details and customer impressions,
        along with conversation flow to generate till end of session.
        conclusion of conversation is also provided, generate conversations accordingly.:
        
        {data}
        """

        return prompt


class Agent_Generate_Summary(ContextMethods):

    def __init__(self):
        self.context = []

    def prompt_func(self, user_input=None):
        self.add_role(role="system", content=self.role_defination())
        self.add_role(role="system", content=self.task_defination())
        self.add_role(role="user", content=self.user_input_defination(user_input))

        return self.build_context()

    def role_defination(self):
        prompt = f"""
        You are expert content analyser. 
        You task is to analyse a whole meeting transcript between a Financial Advisor and Customer
        And provide summarization
        """

        return prompt

    def task_defination(self):
        prompt = f"""

        You Task is:

        - Analyse Conversations between Customer and Financial Advisor
        - Identify usefull business points and exchanges
        - Generate brief summary of conversations which includes
            1. Proper markdown format of headings and labels
            2. Primary points discussed
            3. Future scope discussed
            4. Insight which help advisor to be able to convince customer

        Important Notes:

        - Return only generated summary, nothing else is required

        """

        return prompt

    def user_input_defination(self, data):
        prompt = f"""
        Here are transcript of meeting between Customer and Financial Advisor:

        {data}
        """

        return prompt
    

class ConversationAnalysis(BaseModel):
        sentiment: Literal["Positive", "Negative", "Neutral"]
        products_marketed: int
        products_marketed_list: List[str]
        products_interested: int
        products_interested_list: List[str]

class AgentGenerateKPIs(ContextMethods):

    def __init__(self):
        self.context = []
        self.example = """{
                        "sentiment": "Positive",
                        "products_marketed": 3,
                        "products_marketed_list": ["Product A", "Product B", "Product C"],
                        "products_interested": 2,
                        "products_interested_list": ["Product A", "Product C"]
                    }"""

    def prompt_func(self, user_input=None):

        self.add_role(role="syste", content=self.role_defination())
        self.add_role(role="system", content=self.task_defination())
        self.add_role(role="system", content=self.add_role())
        self.add_role(role="user", content=self.user_input_defination(user_input))

        return self.build_context()
    
    def role_defination(self):
        prompt = f"""
        You are expert content generator. 
        You task is to generate a list of KPIS from a whole meeting transcript between a Financial Advisor and Customer.
        """
        return prompt
    
    def task_defination(self):
        prompt = f"""
        Your task is to analyse the conversations between a Sales Representative and Customer, and therby Extract the following pointers (KPIs):
        
        Below each pointer is provided along with their data type, values that it accepts and its definiton:

            1 - sentiment: string (Positive, Negative, Neutral) ->  Over all sentiment of the conversation.
            2 - products_marketed: int -> number of products marketed during the meeting.
            3 - products_marketed_list: list -> Names of the  products marketed in form of a Python list. 
            4 - products_interested: int -> Mumber of products the customer is interested in. 
            5 - products_interested_list: list ->  Names of products the customer is interested in in form of a Python list. 

        """
        return prompt
    
    def response_format(self):

        prompt = f"""Provide the output in form of a JSON only. 

        Here is a provided Schema for the output to follow: 
        {ConversationAnalysis.model_json_schema()}

        Follow the below example to get an idea (Do not reply on this for facts.):
        {self.example}

        Do not provide any other text or explaination. Only the JSON format is needed. 
        
        """
        return prompt
    
    def user_input_defination(self, data):
        prompt = f"""
        Here are transcript of meeting between Customer and Financial Advisor:

        {data}
        """

        return prompt



    
