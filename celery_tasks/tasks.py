#!/usr/bin/python3 
# -*-coding:utf-8-*- 
# @Author: zhu shiqing
# @Time: 2018年04月19日22时20分 
# 说明: 
# 总结:

from celery import Celery
from django.conf import settings
# 创建一个celery类的实例对象
from django.core.mail import send_mail

app = Celery('celery_tasks', broker='redis://127.0.0.1:6379/5')

import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_dailyfresh01.settings")
django.setup()


@app.task
def send_register_active_email(to_email, username, token):
    # 发送激活邮件
    subject = '天天生鲜欢迎信息'
    message = ''
    sender = settings.EMAIL_FROM
    receiver = [to_email]
    html_message = '<h1>%s,欢迎成为天天生鲜超级会员</h1>请点击链接进行激活<br/><a href="http://127.0.0.1:8000/user/active/%s">http://127.0.0.1:8000/user/active/%s</a>' % (
        username, token, token)

    send_mail(subject, message, sender, receiver, html_message=html_message)

