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

parser = argparse.ArgumentParser(description='HIT疫情上报')
parser.add_argument('username', help='统一身份认证登录用户名（学号）')
parser.add_argument('password', help='统一身份认证登录密码')
parser.add_argument('-k', '--api_key', help='Server酱的SCKEY，或是电邮密码/Key')
parser.add_argument('-m', '--mail_to', help='电邮信息，格式"服务器[:端口[U]]:用户名"')


def print_log(msg: str) -> None:
    print(f'[{datetime.datetime.now()}] {msg}')


def get_report_info(session: requests.Session, module_id: str) -> dict:
    with open('post_data.jsonc', 'r', encoding='utf-8') as jsonfile:
        jsondata = ''.join(
            line for line in jsonfile if not line.startswith('//'))
    model = json.loads(re.sub("//.*", "", jsondata, flags=re.MULTILINE))

    model['id'] = module_id

    report_info = {
        'info': json.dumps({'model': model})
    }
    print_log('生成上报信息成功')
    # print_log(report_info)
    return report_info


def main(args):
    print_log('尝试登录...')
    lose_count = 0
    s = None
    while lose_count < 10 and s == None:
        try:
            s = idslogin(args.username, args.password)
            break
        except LoginFailed as e:
            print_log(f'登录失败:{e}')
            lose_count += 1
    if lose_count == 10:
        return False, '登录失败'

    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; Redmi K30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.110 Mobile Safari/537.36'
    })
    r = s.get('https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/shsj/common')
    _ = urllib.parse.urlparse(r.url)
    if _.hostname != 'xg.hit.edu.cn':
        print_log('登录失败')
        return False, '登录失败'
    print_log('登录成功')
    r = s.post('https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xs/csh')
    _ = json.loads(r.text)
    if _['isSuccess']:
        module = _['module']
        print_log("获取上报信息成功")
    else:
        module = ''
        r = s.post('https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xs/getYqxxList')
        yqxxlist = json.loads(r.text)
        if not yqxxlist['isSuccess']:
            print_log(
                '无法获取上报信息列表, 原因: %s', yqxxlist['msg'])
            return False, '无法获取上报信息列表'
        yqxxlist = yqxxlist['module']['data']
        for i in yqxxlist:
            if i['rq'] == date.today().isoformat():
                if i['zt'] == '00':  # 未提交
                    module = i['id']
                    print_log("使用从前的项目进行疫情上报...")
                elif i['zt'] == '01':  # 待辅导员审核
                    # 总是强制重新提交
                    print_log("你已经提交过每日上报。")
                    module = i['id']
                    print_log("使用从前的项目进行疫情上报...")

                else:  # 辅导员审核成功 当前状态不可提交！
                    print_log("当前状态不可提交!")
                    return False, '辅导员审核成功 当前状态不可提交'
                break
    if not module:
        print_log('未找到疫情信息!')
        return False, '未找到上报信息入口'

    report_info = get_report_info(s, module)
    save_url = 'https://xg.hit.edu.cn/zhxy-xgzs/xg_mobile/xsMrsb/saveYqxx'
    response = s.post(save_url, params=report_info)
    print_log(f'POST {save_url} {response.status_code}')

    res_msg = '提交成功' if response.json()['isSuccess'] else '提交失败'
    return response.json()['isSuccess'], res_msg


if __name__ == '__main__':
    args = parser.parse_args()
    is_successful, msg = main(args)
    print_log(msg)
    if args.api_key:
        report_msg = ""  # 生成上报报告
        if is_successful:
            report_msg = f"疫情上报成功！{datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            report_msg = f"疫情上报失败，原因：{msg}{datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')}"

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
                s = smtplib.SMTP(host=host) if len(mail_info) == 2 else smtplib.SMTP(
                    host=host, port=int(mail_info[1]))
                if not unsafe:
                    s.starttls()
                s.login(mail_addr, args.api_key)
                print_log('邮件服务器连接成功')
                s.ehlo_or_helo_if_needed()
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
