from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_server, name='create_server'),
    path('<int:server_id>/', views.server_view, name='server_view'),
    path('<int:server_id>/channel/<int:channel_id>/', views.server_view, name='channel_view'),
    path('<int:server_id>/create_channel/', views.create_channel, name='create_channel'),
    path('join/<str:invite_code>/', views.join_server, name='join_server'),
    path('join-by-code/', views.join_server_by_code, name='join_server_by_code'),
]