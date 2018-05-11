
from django.conf.urls import url
from apps.user.views import RegisterView, ActiveView, LoginView

urlpatterns = [
    # url(r'^register$', views.register, name='register'), # 注册界面
    # url(r'^register_handel$', views.register_handel, name='register_handel'), # 注册

    url(r'^register$', RegisterView.as_view(), name='RegisterView'), # 注册界面
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'), # 注册
    url(r'^login$', LoginView.as_view(), name='login'), # 登录

]

