import pickle
class ChatRoom:
    def __init__(self, name,server_on):
        self.name = name
        self.server_on=server_on
        self.users = []
        self.Leader=""
        self.messages = []
        self.sequencer=0
        
    def add_user(self, user):
        self.users.append(user)

    def remove_user(self, user):
        self.users.remove(user)

    def set_leader(self, user):
        self.Leader=user

    def post_message(self, message):
        #ToDo
        s=1

    def get_messages(self):
        #ToDo
        s=1
    def serialize(self):
        self.name=pickle.dumps(self.name) 
        self.server_on=pickle.dumps(self.name)  
        self.users = pickle.dumps(self.users)
        self.Leader= pickle.dumps(self.Leader)
        self.messages = pickle.dumps(self.messages)
        self.sequencer=pickle.dumps(self.sequencer)
    def deserialize(self):    
        self.name=pickle.loads(self.name) 
        self.server_on=pickle.loads(self.name)  
        self.users = pickle.loads(self.users)
        self.Leader= pickle.loads(self.Leader)
        self.messages = pickle.loads(self.messages)
        self.sequencer=pickle.loads(self.sequencer)