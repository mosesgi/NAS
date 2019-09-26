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
import poplib
import socks
import chardet
import datetime
import _mysql_connector
from email import parser, policy
from email.utils import parseaddr, parsedate_tz, mktime_tz
 
 
CON = {
	"host" : "localhost",  # MySQL host
	"port" : 3306,
	"user" : "root",  # MySQL user
	"password" : "root",  # MySQL password
	"database" : "test"   # MySQL database
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
    "user" : "youremailname@sina.com",   # mail user
    "pass" : "youremailpass"   # mail password
}
 
# File write to local args
mail_dig_tag_path = os.getcwd()
mail_dig_tag_file = "mail_dig.tag"
 
# Mail filter define args
mail_dig_filter_list = ["DownloadCommandFromMail"]
 
# Codec
codec = ["gb2312", "gb18030", "gbk", "hz", "big5", "big5hkscs", "cp950", "cp932", "euc_jp", "euc_jis_2004", "euc_jisx0213",
     "iso2022_jp", "iso2022_jp_1", "iso2022_jp_2", "iso2022_jp_2004", "iso2022_jp_3", "iso2022_jp_ext",
     "shift_jis", "shift_jis_2004", "shift_jisx0213"]
 
 
class MailProc(object):
    def __init__(self):
        self.mysql_con = self._mysqlcon()
        #socks.setdefaultproxy(TYPE, ADDR, PORT)
        socks.setdefaultproxy(socks.HTTP, 'cn-proxy.sg.oracle.com', 80)
        socks.wrapmodule(poplib)
        self.mail_con = self._mailcon()
        self.char_col = set()
 
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
        con = _mysql_connector.MySQL()
        con.connect(**CON)
        con.set_character_set(SET["charset"])
        con.use_unicode(SET["use_unicode"])
        con.autocommit(SET["autocommit"])
        con.query("SET NAMES utf8mb4;")
        con.query("SET CHARACTER SET utf8mb4;")
        con.query("SET character_set_connection=utf8mb4;")
        con.commit()
        return con
 
    def _mailcon(self):
        mail_con = poplib.POP3(host=MAIL["host"], port=MAIL["port"])
        mail_con.user(MAIL["user"])
        mail_con.pass_(MAIL["pass"])
        return mail_con
 
    def _get_mail_source(self, ino):
        mail_src = ''
        for mail_row in self.mail_con.retr(ino)[1]:
            if mail_row:
                char = chardet.detect(mail_row)["encoding"]
                self.char_col.add(char)
                try:
                    mail_dec = mail_row.decode("utf-8")
                except UnicodeDecodeError:
                    mail_dec = mail_row.decode(char)
                mail_src = mail_src + mail_dec + "\n"
        mail_par = parser.Parser(policy=policy.default).parsestr(mail_src)
        return mail_par
 
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
        def __body_man(is_decode=False, char=None):
            body = ''
            if not mail_par.is_multipart():
                if not is_decode:
                    body = mail_par.get_payload()
                elif is_decode:
                    mail_par.set_charset(char)
                    body = mail_par.get_payload(decode=True).decode(char)
            elif mail_par.is_multipart():
                for part in mail_par.get_payload():
                    if part.get_content_type() == part.get_default_type():
                        if not is_decode:
                            body += part.get_payload()
                        elif is_decode:
                            part.set_charset(char)
                            body += part.get_payload(decode=True).decode(char)
            return body
 
        char = mail_par.get_charsets()[-1]
        if char == "utf-8":
            return __body_man()
        elif char != "utf-8":
            codec_copy = codec.copy()
            for char_detect in self.char_col:
                codec_copy.append(char_detect)
            for char_decode in codec_copy:
                try:
                    return __body_man(is_decode=True, char=char_decode)
                except UnicodeDecodeError:
                    continue
                finally:
                    self.char_col = set()
 
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
                        for column in MAIL:
                            if column != "time" and column != 'mail_id':
                                MAIL[column] = self.mysql_con.escape_string(MAIL[column]).decode("utf-8")
                        try:
                            self.mysql_con.query(SQL["sql"].format(**SQL, **MAIL))
                        except _mysql_connector.MySQLInterfaceError as E:
                            self.mysql_con.rollback()
                            if mail_ino:
                                mail_par = self._get_mail_source(ino=mail_ino)
                                mail_time = self._get_mail_time(mail_par=mail_par)
                                mail_id = self._get_mail_mid(mail_par=mail_par)
                                tags = "{id}\n{ts}".format(id=mail_id, ts=mail_time)
                                self._fileproc(path=file_tags, text=tags)
                            self.mysql_con.close()
                            self.mail_con.quit()
                            sys.exit(E)
                        else:
                            self.mysql_con.commit()
 
            self.mysql_con.close()
            self._fileproc(path=file_tags, text=tags)
        self.mail_con.quit()
 
 
if __name__ == "__main__":
    MP = MailProc()
    MP.mail_caseinfo_dig()
    