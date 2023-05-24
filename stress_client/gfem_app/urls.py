"""stress_client URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, re_path
from .views import *
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path('', simple_view, {'template': 'first_page.html'}),
    path('gfem/get_data', csrf_exempt(simple_view), {'template': 'get_page.html', 'models': CONFIG['DATA_BASE']}),
    path(r'ajax/get_response/', csrf_exempt(BaseInteract.as_view()), name='get_response'),
    path(r'ajax/get_table_fields/', AjaxFields.as_view(), name='get_table_fields'),
    path('gfem/post_data', simple_view, {'template': 'post_page.html', 'models': CONFIG['DATA_BASE'].keys()}),
    path('gfem/update_data', simple_view, {'template': 'change_page.html', 'models': CONFIG['DATA_BASE'].keys()}),
    path('gfem/delete_data', simple_view, {'template': 'delete_page.html', 'models': CONFIG['DATA_BASE'].keys()}),
    re_path(r'file_save', csrf_exempt(file_save_view), {'template': 'file_save.html'},
            name='save_form'),
]
