from django.urls import path
from . import views

urlpatterns = [
    path('', views.notice_list_create, name='notice-list-create'),
    path('my-notices/', views.my_notices, name='my-notices'),
    path('<str:pk>/', views.notice_detail, name='notice-detail'),
    path('<str:pk>/respond/', views.respond_to_notice, name='respond-to-notice'),
    path('<str:pk>/complete/', views.complete_notice, name='complete-notice'),
    path('<str:pk>/delete/', views.delete_notice, name='delete-notice'),
    path('image/<str:grid_id>/', views.serve_image, name='serve-image'),
]
