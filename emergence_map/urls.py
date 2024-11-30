



from django.conf.urls import url, include

from emergence_map import views
urlpatterns = [
    url(r'^analysis/$',views.analysis ),
    url(r'^demo/$', views.demo),
    url('register/',views.register,name = 'register'),
    url('login/',views.login,name = 'login'),
]