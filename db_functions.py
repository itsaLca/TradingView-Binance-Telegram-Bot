import sqlite3

''' Table name: user_info
    Columns:
    1. chat_id: integer
    2. user: text'''


class Database(object):
    def __init__(self):
        self.conn = sqlite3.connect('db.sqlite')
        self.c = self.conn.cursor()
        self.initialize_db()

    def initialize_db(self):
        '''Creates necessary tables if they do not exist'''
        with self.conn:
            self.c.execute("CREATE TABLE IF NOT EXISTS user_info(chat_id INTEGER, user TEXT, allow INTEGER)")

#    def chat_id_check(self,chat_id,user):
#        ''' Only one chat can be initialized at a time by the owner of the bot '''
#        with self.conn:
#            chat_id_tuple = self.c.execute("SELECT chat_id FROM user_info WHERE user=?",(user,))
#        for id in chat_id_tuple:
#            chat_id = id[0]
#        return chat_id

    def chat_ids(self):
        ''' Only one chat can be initialized at a time by the owner of the bot '''
        chat_ids=list()
        with self.conn:
            found_users = self.c.execute("SELECT chat_id FROM user_info WHERE allow=1")
            for id in found_users:
                chat_id = id[0]
                chat_ids.append(chat_id)
        return chat_ids

    def user_check(self,chat_id, user):
        ''' This is for security reasons. Only one specified user can use this bot '''
        with self.conn:
            found_users = self.c.execute("SELECT allow FROM user_info where allow=1 and chat_id=? and user=?",(chat_id,user))
        allow=False
        for user in found_users:
            allow = user[0]==1
        return allow

    def username_check(self,chat_id):
        ''' This is for security reasons. Only one specified user can use this bot '''
        with self.conn:
            found_users = self.c.execute("SELECT user FROM user_info where allow=1 and chat_id=?",(chat_id))
        username=None
        for user in found_users:
            username = user[0]
        return username

    def save_chat(self,chat_id, user, allow):
        with self.conn:
            found_users = self.c.execute("SELECT 1 FROM user_info where chat_id=? and user=?",(chat_id,user))
            if found_users.rowcount==0:
                self.c.execute("INSERT INTO user_info (chat_id, user, allow) VALUES (?,?,?)",(chat_id,user,allow))


    def list_chat(self):
        userstext="found users:"
        with self.conn:
            found_users = self.c.execute("SELECT chat_id, user, allow FROM user_info")
            for user in found_users:
                userstext = userstext + "\n" + str(user[0]) + " "+  user[1] + " " +  str(user[2])
        return userstext

    def allow_chat(self,chat_id, allow):
        with self.conn:
            username = self.username_check(chat_id)
            if username is None:
                return "None"
            else:
                self.c.execute("UPDATE user_info SET allow=? where chat_id=?",(allow, chat_id))