from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('add_city/', views.add_city, name='add_city'),
    path('del_city/<int:id_city>/', views.del_city, name='del_city'),
    path('info/', views.info, name='info'),
]
