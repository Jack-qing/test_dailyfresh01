from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from apps.user.models import User
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.conf import settings
from django.http import HttpResponse
from celery_tasks.tasks import send_register_active_email
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
import re


# Create your views here.

def register(request):
    '''用户注册'''

    return render(request, 'register.html')


def register_handel(request):
    # 1 接收数据
    username = request.POST.get('username')
    password = request.POST.get('pwd')
    email = request.POST.get('email')
    allow = request.POST.get('allow')

    # 2 进行数据校验
    # 判断数据完整性
    if not all([username, password, email]):
        return render(request, 'register.html', {'errmsg': '数据不完整'})

    # 判断邮箱
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        return render(request, 'register.html', {'errmsg': '邮箱不合法重新输入'})

    # 判断用户协议
    if allow != 'on':
        return render(request, 'register.html', {'errmsg': '请用户同意协议'})

    # 进行校验用户名是否重复
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        # 用户名为空
        user = None

    if user:
        # 用户已存在
        return render(request, 'register.html', {'errmsg': '用户已存在，请重新输入:'})

    # 3 进行业务处理：进行用户注册    # 注册：用户保存到数据库中
    user = User.objects.create_user(username, password, email)
    # 默认is_active 是True，需要修改为False
    user.is_active = 0
    user.save()

    # 4 返回应答
    return redirect(reverse('goods:index'))


class RegisterView(View):
    '''注册'''

    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        '''进行注册处理'''
        # 1 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 2 进行数据校验
        # 判断数据完整性
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        # 判断邮箱
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱不合法重新输入'})

        # 判断用户协议
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请用户同意协议'})

        # 进行校验用户名是否重复
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名为空
            user = None

        if user:
            # 用户已存在
            return render(request, 'register.html', {'errmsg': '用户已存在，请重新输入:'})

        # 3 进行业务处理：进行用户注册    # 注册：用户保存到数据库中
        user = User.objects.create_user(username, email, password)
        # 默认is_active 是True，需要修改为False
        user.is_active = 0
        user.save()

        # 发送激活邮件，包含激活链接：http://127.0.0.1:8000/user/activer/3
        # 使用settings.py中的密钥(创建项目的时候随机生成) ， 和过期时间

        # 创建一个TimedJSONWeb SignatureSerializer对象
        serializer = Serializer(settings.SECRET_KEY, 3600)
        # 待加密码信息
        info = {'confirm': user.id}
        # 获取加密内容，注意类型：bytes
        token = serializer.dumps(info)  # bytes
        # 因为发送过来的是bytes类型需要转换成字符串
        # 还原成字符串
        token = token.decode()

        # 发送邮件
        send_register_active_email.delay(email, username, token)

        return redirect(reverse('goods:index'))


class ActiveView(View):
    '''用活激活'''

    def get(self, request, token):
        '''进行用户激活'''
        # 进行解密，获取用户激活的信息
        serializer = Serializer(settings.SECRET_KEY, 3600)

        try:
            info = serializer.loads(token)
            # 解密成功可获取原信息
            user_id = info['confirm']

            # 获取待激活的用户id
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()

            # 跳转到登录面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # token已过期
            return HttpResponse('激活信息已过期')


# /user/login
class LoginView(View):
    '''登录信息'''
    def get(self, request):
        # 显示用户登录信息
        # 判断是否记住有用户名
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checkbox = 'checkbox'
        else:
            username = ''
            checkbox = ''
        return render(request, 'login.html', {'username':username, 'checkbox': checkbox})

    def post(self, request):
        #  1 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')

        # 2 校验数据
        # 判断数据完整型
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        # 3 业务处理：登录名校验
        user = authenticate(username=username, password=password)
        if user is not None:
            # 用户密码正确
            if user.is_active:
                # print("用户已激活")
                login(request, user)
                # 跳转首页
                response = redirect(reverse('goods:index')) # 等价 HttpResponse

                # session记住用户名
                remember = request.POST.get('remember')
                if remember == 'on':
                    # 记住用户名
                    response.set_cookie('username', username, max_age=7*24*3600)
                else:
                    response.delete_cookie('username')

                    return response

            else:
                return render(request, 'login.html', {'errmsg': '未激活'})
        else:
            return render(request, 'login.html', {'errmsg': '用户名或密码错误'})
