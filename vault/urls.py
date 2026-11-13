from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('documents/', views.documents_list, name='documents_list'),
    path('documents/add/', views.document_add, name='document_add'),
    path('documents/file/<str:file_id>/', views.document_file_view, name='document_file_view'),
    path('documents/<str:doc_id>/', views.document_detail, name='document_detail'),
    path('documents/<str:doc_id>/edit/', views.document_edit, name='document_edit'),
    path('documents/<str:doc_id>/delete/', views.document_delete, name='document_delete'),
    path('documents/<str:doc_id>/renew/', views.document_renew, name='document_renew'),
    path('vault/export/', views.export_vault, name='export_vault'),
    path('login/', views.auth_login, name='login'),
    path('register/', views.auth_register, name='register'),
    path('logout/', views.auth_logout, name='logout'),
    path('demo/', views.demo_login, name='demo_login'),
]

