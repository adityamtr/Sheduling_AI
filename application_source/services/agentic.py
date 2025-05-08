

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