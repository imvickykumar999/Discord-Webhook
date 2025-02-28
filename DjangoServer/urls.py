from django.urls import path
from .views import send_reply

urlpatterns = [
    path('send-dm/', send_reply, name='send_dm'),
]
