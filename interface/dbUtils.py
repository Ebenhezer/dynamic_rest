import psycopg2
import os

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASS')

# Connect to the database
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

class DbUtils:  
    # General calls
    def getConfigDetails(self):
        cursor = conn.cursor() 
        cursor.execute("SELECT * FROM t_config") 
        key = cursor.fetchone()
        return key
    
    def updateConfig(self, config_password, config_email, smtp_server_address, sender_email_address, smtp_username, smtp_password, smtp_port, domain):
        cursor = conn.cursor() 
        cursor.execute("UPDATE t_config SET config_password = %s, config_email = %s, smtp_server_address = %s,\
                sender_email_address = %s, smtp_username = %s, smtp_password = %s, smtp_port = %s, domain = %s\
                WHERE config_username = %s"
                       ,(config_password, config_email, smtp_server_address, sender_email_address, smtp_username, smtp_password, smtp_port, domain, "master",)) 
        conn.commit()
    
    def getUserByEmail(self, email):  
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM t_user_info WHERE email = %s ",(email,))  
        user = cursor.fetchone()
        return user  
