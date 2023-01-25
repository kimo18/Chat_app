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
