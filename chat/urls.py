# chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dm/', views.direct_messages, name='direct_messages'),
    path('dm/<int:user_id>/', views.direct_messages, name='direct_message'),
    path('load-messages/<int:channel_id>/', views.load_messages, name='load_messages'),
    path('delete-message/<int:message_id>/', views.delete_message, name='delete_message'),
    path('edit-message/<int:message_id>/', views.edit_message, name='edit_message'),
]