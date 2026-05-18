from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_assignments, name='list-assignments'),
    path('create/', views.create_assignment, name='create-assignment'),
    path('<str:assignment_id>/', views.get_assignment, name='get-assignment'),
    path('<str:assignment_id>/update/', views.update_assignment, name='update-assignment'),
    path('<str:assignment_id>/delete/', views.delete_assignment, name='delete-assignment'),
    path('<str:assignment_id>/submissions/', views.list_submissions, name='list-submissions'),
    path('<str:assignment_id>/submissions/<str:student_id>/marks/', views.update_submission_marks, name='update-submission-marks'),
]
