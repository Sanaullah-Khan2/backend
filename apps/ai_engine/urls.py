from django.urls import path
from . import views

urlpatterns = [
    path('risk-scores/',              views.all_risk_scores,       name='all-risk-scores'),
    path('risk-scores/<str:student_id>/', views.student_risk_score, name='student-risk-score'),
    path('recalculate/',              views.recalculate_all,       name='recalculate'),
    path('interventions/',            views.list_interventions,    name='list-interventions'),
    path('interventions/create/',     views.create_intervention,   name='create-intervention'),
]