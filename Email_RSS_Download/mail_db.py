# !/usr/bin/python3
# -*- coding: utf-8 -*-
 
"""
create_author : 
create_time   : 2019-01-21
program       : *_* mail handler *_*
"""
 
import os
import re
import sys
import socks
import poplib
import datetime
import mysql.connector
from email import parser, policy
from email.utils import parseaddr, parsedate_tz, mktime_tz
 
 
CON = {
	"host" : "localhost",  # MySQL host
	"port" : 3306,
	"user" : "root",  # MySQL user
	"password" : "root",  # MySQL password
	"database" : "test",   # MySQL database
    "charset": 'utf8'
}
 
SET = {
	"charset": "utf8",  # character charset
	"use_unicode": True,    # use unicode
	"autocommit" : False    # transaction autocommit
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
    "host" : "pop.sina.com",  # mail host
    "port" : 110,   # pop3 port
    "user" : "your_email@sina.com",   # mail user
    "pass" : "your_password"   # mail password
}
 
# File write to local args
# 群晖定时任务时, os.getcwd() 未能生成文件, 或者文件被清除, 需使用绝对路径
# mail_dig_tag_path = "/root/tmp"
mail_dig_tag_path = os.getcwd()
mail_dig_tag_file = "mail_dig.tag"
 
# 邮件标题用的名字
mail_dig_filter_list = ["DownloadCommandFromMail"]
 
class MailProc(object):
    def __init__(self):
        self.mysql_con = self._mysqlcon()
        socks.setdefaultproxy(socks.HTTP, 'any.proxy.you.use', 80)
        socks.wrapmodule(poplib)
        self.mail_con = self._mailcon()
 
    def _fileproc(self, path, text):
        """
        Handler of writing file out to local.
        :param path: string
            full path of the file to write out.
        :param text: string
            content to write out.
        :return: Python built-in exit code.
        """
        with open(path, 'w') as f:
            f.write(text)
 
    def _mysqlcon(self):
        """
        Get MySQL connection.
        :return: MySQL connection object.
        """
        con = mysql.connector.connect(**CON)
        return con
 
    def _mailcon(self):
        mail_con = poplib.POP3(host=MAIL["host"], port=MAIL["port"])
        mail_con.user(MAIL["user"])
        mail_con.pass_(MAIL["pass"])
        return mail_con
 
    def _get_mail_source(self, ino):
        resp, lines, octets = self.mail_con.retr(ino)
        msg_src = b'\r\n'.join(lines).decode("utf-8")
        mail_par = parser.Parser().parsestr(msg_src)
        return mail_par
    
    # check email content string encoding charset.
    def _guess_charset(self, mar_par):
        # get charset from message object.
        charset = mar_par.get_charsets()[-1]
        # if can not get charset
        if charset is None:
            # get message header content-type value and retrieve the charset from the value.
            content_type = mar_par.get('Content-Type', '').lower()
            pos = content_type.find('charset=')
            if pos >= 0:
                charset = content_type[pos + 8:].strip()
            else:
                charset = "utf-8"
        return charset
 
    def _get_mail_mid(self, mail_par):
        return mail_par.get("X-SMAIL-MID")
 
    def _get_mail_time(self, mail_par):
        return datetime.datetime.fromtimestamp(mktime_tz(parsedate_tz(mail_par.get("Date"))))
 
    def _get_mail_from(self, mail_par):
        return parseaddr(mail_par.get("From"))[0]
 
    def _get_mail_addr(self, mail_par):
        return parseaddr(mail_par.get("From"))[1]
 
    def _get_mail_subject(self, mail_par):
        return mail_par.get("Subject")
 
    def _get_mail_body(self, mail_par):
        def __body_man(part):
            body = part.get_payload(decode=True)
            charset = self._guess_charset(part)
            if charset:
                body = body.decode(charset)
            return body.strip()
 
        if (mail_par.is_multipart()):
            # get multiple parts from message body.
            parts = mail_par.get_payload()
            # loop for each part
            for n, part in enumerate(parts):
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    return __body_man(part)
        # if not multiple part. 
        else:
            return __body_man(mail_par)
 
    def mail_caseinfo_dig(self):
        tag_id = ''
        tag_ts = datetime.datetime.strptime("1970-01-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        file_tags = mail_dig_tag_path + '/' + mail_dig_tag_file
        if os.path.exists(file_tags):
            with open(file_tags, 'r') as f:
                tags_info = f.readlines()
                tag_id = tags_info[0].replace("\n", '')
                tag_ts = datetime.datetime.strptime(tags_info[1], "%Y-%m-%d %H:%M:%S")
 
        mail_cnt = self.mail_con.stat()[0]
        mail_par_ck = self._get_mail_source(ino=mail_cnt)
        mail_tag_id = self._get_mail_mid(mail_par=mail_par_ck)
        mail_tag_ts = self._get_mail_time(mail_par=mail_par_ck)
        tags = "{id}\n{ts}".format(id=mail_tag_id, ts=mail_tag_ts)
        if mail_tag_id == tag_id:
            if not os.path.exists(file_tags):
                self._fileproc(path=file_tags, text=tags)
            self.mail_con.quit()
            sys.exit()
 
        elif mail_tag_id != tag_id:
            for mail_ino in range(mail_cnt):
                mail_par = self._get_mail_source(ino=mail_ino + 1)
                mail_time = self._get_mail_time(mail_par=mail_par)
                mail_id = self._get_mail_mid(mail_par=mail_par)
                if mail_time >= tag_ts and mail_id != tag_id:
                    mail_body = self._get_mail_body(mail_par=mail_par)
                    if re.search("(\\\\u\d+\w?)+", mail_body):
                        continue
                    qualified_mail = False
                    mail_subject = self._get_mail_subject(mail_par=mail_par)
                    for filter_loop in mail_dig_filter_list:
                        if re.search(filter_loop, mail_subject):
                            qualified_mail = True
                            break
                    # if not qualified_mail:
                    #     for filter_loop in mail_dig_filter_list:
                    #         if re.search(filter_loop, mail_body):
                    #             qualified_mail = True
                    #             break
                    if not qualified_mail:
                        continue
                    elif qualified_mail:
                        mail_from = self._get_mail_from(mail_par=mail_par)
                        mail_addr = self._get_mail_addr(mail_par=mail_par)
                        MAIL = {
                            "mail_id": mail_id,
                            "time": mail_time.__str__(),
                            "from": mail_from,
                            "addr": mail_addr,
                            "subject": mail_subject,
                            "body": mail_body,
                        }
                        print(MAIL)
                        # for column in MAIL:
                        #     if column != "time" and column != 'mail_id':
                        #         MAIL[column] = self.mysql_con.converter(MAIL[column]).decode("utf-8")
                        
                        mycursor = self.mysql_con.cursor()
                        try:
                            mycursor.execute(SQL["sql"].format(**SQL, **MAIL))
                            self.mysql_con.commit()
                        except mysql.connector.Error as e:
                            self.mysql_con.rollback()
                            print('insert data error! {}'.format(e))
                            if mail_ino:
                                mail_par = self._get_mail_source(ino=mail_ino)
                                mail_time = self._get_mail_time(mail_par=mail_par)
                                mail_id = self._get_mail_mid(mail_par=mail_par)
                                tags = "{id}\n{ts}".format(id=mail_id, ts=mail_time)
                                self._fileproc(path=file_tags, text=tags)
                            self.mail_con.quit()
                            sys.exit(e)
                        finally:
                            mycursor.close()
            self.mysql_con.close()
            self._fileproc(path=file_tags, text=tags)
        self.mail_con.quit()
 
 
if __name__ == "__main__":
    MP = MailProc()
    MP.mail_caseinfo_dig()
    