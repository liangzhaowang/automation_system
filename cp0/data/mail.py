import smtplib
import base64
import os
from email.mime.text import MIMEText


class MailSender(object):
    def __init__(self, template, subtitle, title, content, link, from_addr, recipients, cc_addr=''):
        self.server = 'smtp.intel.com'
        self.template = template
        self.subtitle = subtitle
        self.title = title
        self.content = content
        self.link = link
        self.from_addr = from_addr
        self.recipients = recipients
        self.cc_addr = cc_addr

    def success(self):
        cc_addr = ['chenx.chen@intel.com', self.cc_addr] if self.cc_addr else ['chenx.chen@intel.com']

        smtp = smtplib.SMTP(self.server)
        link = self.link
        content = open(os.path.join(os.path.join(os.path.dirname(__file__), 'templates', self.template)), 'r').read()
        content = content.replace('var_title', self.title)
        content = content.replace('var_content', self.content)
        content = content.replace('var_link', link)
        smtp.ehlo(self.server)
        msg = MIMEText(content, _subtype='html', _charset='utf-8')
        msg['Subject'] = '<CP0> ' + self.subtitle
        msg['From'] = self.from_addr
        msg['To'] = ";".join(self.recipients)
        msg['CC'] = ";".join(cc_addr)
        smtp.sendmail(self.from_addr, self.recipients + cc_addr, msg.as_string())
        smtp.close()
