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
from django.urls import path
from gfem_app.views import simple_view
from .views import *
from django.views.decorators.csrf import csrf_exempt


urlpatterns = [
    path('id-generate/', simple_view, {'template': 'id_generate.html'}),
    path(r'ajax/generator-id/', csrf_exempt(id_generate_view), name='generator-ID'),
    path('service_CS/', simple_view, {'template': 'calculate_page.html', 'models': CONFIG['DATA_BASE']
                                      ['Section']['dynamic_fields']['type'].keys()}),
    path(r'ajax/CS-calculation/', csrf_exempt(cs_calculation_view), name='calculate_CS'),
]
