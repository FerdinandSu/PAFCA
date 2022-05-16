#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
from requests.utils import dict_from_cookiejar
from lxml import etree
from hit.ids.login import idslogin
from hit.exceptions import LoginFailed
import json
import re
import random
import datetime
import argparse
import sys
import urllib
from _datetime import date
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from email.header import Header

parser = argparse.ArgumentParser(description='HIT出校申请')
parser.add_argument('username', help='统一身份认证登录用户名（学号）')
parser.add_argument('password', help='统一身份认证登录密码')
parser.add_argument('-k', '--api_key', help='Server酱的SCKEY，或是电邮密码/Key')
parser.add_argument('-m', '--mail_to', help='电邮信息，格式"服务器[:端口[U]]:用户名"')


def print_log(msg: str) -> None:
    print(f'[{datetime.datetime.now()}] {msg}')


def get_application_info(session: requests.Session, module_id: str) -> dict:
    with open('post_data.jsonc', 'r', encoding='utf-8') as jsonfile:
        jsondata = ''.join(
            line for line in jsonfile if not line.startswith('//'))
    model = json.loads(re.sub("//.*", "", jsondata, flags=re.MULTILINE))

    with open('reasons.json', 'r', encoding='utf-8') as reasons_file:
        reasons = json.load(reasons_file)
    # 顺序出校理由
    model['cxly'] = reasons[datetime.date.today().day % len(reasons)]
    model['id'] = module_id
    # 日期为第二天
    model['rq'] = (datetime.date.today() +
                   datetime.timedelta(days=1)).isoformat()
    application_info = {
        'info': json.dumps({'model': model})
    }
    print_log('生成申请信息成功')
    return application_info


def main(args):
    print_log('尝试登录...')
    lose_count = 0
    session = None
    while lose_count < 10 and session == None:
        try:
            session = idslogin(args.username, args.password)
            break
        except LoginFailed as e:
            print_log(f'登录失败:{e}')
            lose_count += 1
    if lose_count == 10:
        return False, '登录失败'

    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Redmi K30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.110 Mobile Safari/537.36'
    })
    r = session.get('https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/shsj/common')
    r = session.post(
        'https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xsCxsq/getCxsq',
        data={'info': '{"id": "id"}'})

    response_txt = json.loads(r.text)

    if not r.ok or not response_txt['isSuccess']:
        print_log(
            f'无法获取出校申请信息, 响应原文: {response_txt}')
        return False, '无法获取出校申请信息'
    module = response_txt['module']['id']
    if not module:
        print_log('未获取申请信息!')
        return False, '未找到申请出校入口'

    application_info = get_application_info(session, module)
    save_url = 'https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xsCxsq/saveCxsq'
    response = session.post(save_url, data=application_info)
    print_log(f'POST {save_url} {response.status_code}')
    # print_log(response.text)
    response = response.json()
    msg = response['msg']
    res_msg = '提交成功' if response['isSuccess'] else f'提交失败;{msg}'
    return response['isSuccess'], res_msg


if __name__ == '__main__':
    args = parser.parse_args()
    is_successful, msg = main(args)
    print_log(msg)
    if args.api_key:
        report_msg = ""  # 生成上报报告
        if is_successful:
            report_msg = f"明天的出校申请成功！{datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            report_msg = f"明天的出校申请失败，原因：{msg}{datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"

        if args.mail_to:
            mail_info = args.mail_to.split(':')
            mail_addr = mail_info[-1]

            msg = MIMEText(report_msg, 'plain', 'utf-8')
            msg['Subject'] = Header(report_msg, 'utf-8')
            msg['From'] = 'AUTO_REPORT_BOT'
            msg['To'] = mail_addr
            print_log('尝试发送邮件...')

            host = mail_info[0]
            unsafe = False
            if len(mail_info) == 3 and mail_info[1][-1] == 'U':
                unsafe = True
                mail_info[1] = mail_info[1][:-1]
            try:
                if unsafe:
                    s = smtplib.SMTP(host=host) if len(mail_info) == 2 else smtplib.SMTP(
                        host=host, port=int(mail_info[1]))
                    s.login(mail_addr, args.api_key)
                    print_log('邮件服务器连接成功')
                    s.ehlo_or_helo_if_needed()
                    s.sendmail(mail_addr, mail_addr, msg.as_string())
                    s.quit()
                    print_log('邮件发送成功！')
                else:
                    s = smtplib.SMTP_SSL(host=host) if len(mail_info) == 2 else smtplib.SMTP_SSL(
                        host=host, port=int(mail_info[1]))
                    s.ehlo(host)
                    s.starttls()
                    s.login(mail_addr, args.api_key)
                    print_log('邮件服务器连接成功')
                    s.sendmail(mail_addr, mail_addr, msg.as_string())
                    s.quit()
                    print_log('邮件发送成功！')
            except Exception as e:
                print_log('邮件发送失败。')
                print_log(e)

        else:
            print_log('发送微信提醒...')
            requests.get(
                f"https://sc.ftqq.com/{args.api_key}.send?text={report_msg}")
