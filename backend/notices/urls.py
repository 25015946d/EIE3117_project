from django.urls import path
from . import views

urlpatterns = [
    path('', views.notice_list_create, name='notice-list-create'),
    path('my-notices/', views.my_notices, name='my-notices'),
    path('<int:pk>/', views.notice_detail, name='notice-detail'),
    path('<int:pk>/respond/', views.respond_to_notice, name='respond-to-notice'),
    path('<int:pk>/complete/', views.complete_notice, name='complete-notice'),
]
