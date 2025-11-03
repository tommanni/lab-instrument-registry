"""
URL configuration for Backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path, include
from rest_framework import routers
from instrument_registry import views as api_views
from knox import views as knox_views

urlpatterns = [
    # instrument
    path('api/instruments/', api_views.InstrumentList.as_view()),
    path('api/instruments/search/', api_views.InstrumentSearch.as_view()),
    path('api/instruments/valueset/<field_name>/', api_views.InstrumentValueSet.as_view()),
    path('api/instruments/csv/export/', api_views.InstrumentCSVExport.as_view()),
    path('api/instruments/csv/preview/', api_views.InstrumentCSVPreview.as_view()),
    path('api/instruments/csv/import/', api_views.InstrumentCSVImport.as_view()),
    path('api/instruments/<pk>/', api_views.InstrumentDetail.as_view()),
    path('api/instruments/<pk>/history/', api_views.InstrumentHistory.as_view()),
    # user
    path('api/users/', api_views.UserList.as_view()),
    path('api/users/<pk>/', api_views.UserDetail.as_view()),
    # auth
    path('api/login/', api_views.Login.as_view()),
    path('api/logout/', api_views.Logout.as_view()),
    path('api/logoutall/', api_views.LogoutAll.as_view()),
    path('api/register/', api_views.Register.as_view()),
    path('api/invite/', api_views.GenerateInviteCode.as_view()),
    path('api/change-password/', api_views.ChangePasswordView.as_view()),
    path('api/change-admin-status/', api_views.ChangeAdminStatus.as_view()),
    path('api/change-superadmin-status/', api_views.ChangeSuperadminStatus.as_view()),
    path('api/delete-user/', api_views.DeleteUser.as_view()),
    # services
    path('api/service/', api_views.ServiceValueSet.as_view()),
]
