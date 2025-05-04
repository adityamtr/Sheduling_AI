

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
        You task is to generate a whole meeting transcript between a Financial Advisor and Customer.
        """

        return prompt

    def task_defination(self):

        prompt = f"""
        
        You Task is:
        
        - Analyse profile details provides by user
        - Identify Customer Name, and other provided features
        - Generate a series of conversations between Customer and Financial Advisor
            Here Financial Advisor is Trying to pitch/sell three products
            1. A Mutual Fund Named 'AF cap' with annual returns of 9%
            2. A ETF named 'QAR' with annual returns of 13%
            3. A PPS Named 'AOX' with annual returns of 20%
        - Generate transcript session of about 20 to 25 back and forth conversations
        
        Important Notes:
        
        - Return proper format of conversation, refer following style
            ** Customer **: <customer message here>
            ** Advisor **: <advisor message here>
            
            ** Customer **: <customer message here>
            ** Advisor **: <advisor message here>
        - Return only generated conversations, nothing else is required
        - at least 20 conversation should be there in generated session transcript
            
        """

        return prompt

    def user_input_defination(self, data):

        prompt = f"""
        Here are customer profile details and customer impressions to generate till end of session:
        
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