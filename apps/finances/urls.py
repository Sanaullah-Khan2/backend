from django.urls import path
from . import views

urlpatterns = [
    path('fees/', views.get_all_fees, name='get_all_fees'),
    path('fees/create/', views.create_fee, name='create_fee'),
    path('fees/mark-paid/<str:fee_id>/', views.mark_fee_paid, name='mark_fee_paid'),
    path('defaulters/', views.get_defaulters, name='get_defaulters'),
    path('salaries/', views.get_all_salaries, name='get_all_salaries'),
    path('salaries/create/', views.create_salary, name='create_salary'),
    path('salaries/<str:salary_id>/', views.update_salary, name='update_salary'),
    path('salaries/pay/<str:salary_id>/', views.pay_salary, name='pay_salary'),
]
