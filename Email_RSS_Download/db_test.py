import mysql.connector

CON = {
	"host" : "192.168.50.230",  # MySQL host
	"port" : 3307,
	"user" : "test",  # MySQL user
	"password" : "jimuchen",  # MySQL password
	"database" : "test"   # MySQL database
}

SQL = {
    "dbs" : "test",   # MySQL database
    "tab" : "mail_rss",   # MySQL table
    "sql" : """
            INSERT INTO `{dbs}`.`{tab}` (`mail_mid`, `mail_time`, `sender_name`, `sender_addr`, `subject`, `content`) VALUES
            ('{mail_id}', '{time}', '{from}', '{addr}', '{subject}', '{body}');
    """
}

MAIL = {
    "mail_id": 'mail_id',
    "time": 'timetest',
    "from": 'mail_from',
    "addr": 'mail_addr',
    "subject": 'mail_subject',
    "body": 'mail_body',
}

mydb = mysql.connector.connect(**CON)
mycursor = mydb.cursor()

try:
    mycursor.execute(SQL["sql"].format(**SQL, **MAIL))
    mydb.commit()
except mysql.connector.Error as e:
    print('insert data error! {}'.format(e))
finally:
    mycursor.close()
    mydb.close()
