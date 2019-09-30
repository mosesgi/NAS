import os
import re
import sys
import poplib
import chardet
import datetime
import socks
from email import parser, policy
from email.header import decode_header
from email.utils import parseaddr

MAIL = {
    "host" : "pop.sina.com",  # mail host
    "port" : 110,   # pop3 port
    "user" : "your_email@sina.com",   # mail user
    "pass" : "your_password"   # mail password
}

# 邮件标题必须用这个名字
mail_dig_filter_list = ["DownloadCommandFromMail"]
 
# Codec
codec = ["gb2312", "gb18030", "gbk", "hz", "big5", "big5hkscs", "cp950", "cp932", "euc_jp", "euc_jis_2004", "euc_jisx0213",
     "iso2022_jp", "iso2022_jp_1", "iso2022_jp_2", "iso2022_jp_2004", "iso2022_jp_3", "iso2022_jp_ext",
     "shift_jis", "shift_jis_2004", "shift_jisx0213"]

char_col = set()

def _get_mail_body(mail_par, char_col):
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
        for char_detect in char_col:
            codec_copy.append(char_detect)
        for char_decode in codec_copy:
            try:
                return __body_man(is_decode=True, char=char_decode)
            except UnicodeDecodeError:
                continue
            finally:
                char_col = set()

# The Subject of the message or the name contained in the Email is encoded string
# , which must decode for it to display properly, this function just provide the feature.
def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
       value = value.decode(charset)
    return value

# check email content string encoding charset.
def guess_charset(msg):
    # get charset from message object.
    charset = msg.get_charsets()[-1]
    # if can not get charset
    if charset is None:
        # get message header content-type value and retrieve the charset from the value.
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
        else:
            charset = "utf-8"
    return charset

def print_info(msg, indent_number=0):
    if indent_number == 0:
       # loop to retrieve from, to, subject from email header.
       for header in ['From', 'To', 'Subject']:
           # get header value
           value = msg.get(header, '')
           if value:
              # for subject header.
              if header=='Subject':
                 # decode the subject value
                 value = decode_str(value)
              # for from and to header. 
              else:
                 # parse email address
                 hdr, addr = parseaddr(value)
                 # decode the name value.
                 name = decode_str(hdr)
                 value = u'%s <%s>' % (name, addr)
           print('%s%s: %s' % (' ' * indent_number, header, value))
    # if message has multiple part. 
    if (msg.is_multipart()):
       # get multiple parts from message body.
       parts = msg.get_payload()
       # loop for each part
       for n, part in enumerate(parts):
           print('%spart %s' % (' ' * indent_number, n))
           print('%s--------------------' % (' ' * indent_number))
           # print multiple part information by invoke print_info function recursively.
           print_info(part, indent_number + 1)
    # if not multiple part. 
    else:
        # get message content mime type
        content_type = msg.get_content_type() 
        # if plain text or html content type.
        if content_type=='text/plain' or content_type=='text/html':
           # get email content
           content = msg.get_payload(decode=True)
           # get content string charset
           charset = guess_charset(msg)
           # decode the content with charset if provided.
           if charset:
              content = content.decode(charset)
           print('%sText: %s' % (' ' * indent_number, content + '...'))
        else:
           print('%sAttachment: %s' % (' ' * indent_number, content_type))

def _get_mail_source(mail_con, ino, char_col):
    # mail_src = ''
    # for mail_row in mail_con.retr(ino)[1]:
    #     if mail_row:
    #         char = chardet.detect(mail_row)["encoding"]
    #         char_col.add(char)
    #         try:
    #             mail_dec = mail_row.decode("utf-8")
    #         except UnicodeDecodeError:
    #             mail_dec = mail_row.decode(char)
    #         mail_src = mail_src + mail_dec + "\n"
    resp, lines, octets = mail_con.retr(ino)
    msg_src = b'\r\n'.join(lines).decode("utf-8")
    # print(msg_src)
    print('=======================end of get_mail_source=====================')
    mail_par = parser.Parser().parsestr(msg_src)
    return mail_par

socks.setdefaultproxy(socks.HTTP, 'any.proxy.you.use', 80)
socks.wrapmodule(poplib)
mail_con = poplib.POP3(host=MAIL["host"], port=MAIL["port"])
mail_con.user(MAIL["user"])
mail_con.pass_(MAIL["pass"])
mail_cnt = mail_con.stat()[0]
for mail_ino in range(mail_cnt):
    mail_par = _get_mail_source(mail_con=mail_con, ino=mail_ino + 1, char_col=char_col)
    # print(mail_par)
    # mail_body = _get_mail_body(mail_par=mail_par, char_col=char_col)
    # print(mail_body)

    print_info(mail_par)
    print("=========================================================")