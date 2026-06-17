from django.urls import path
from apps.mailroom.views import (
    MailroomDashboardView, MailroomReceiveView,
    MailroomApproveView, MailroomRouteView
)

app_name = 'mailroom'

urlpatterns = [
    path('dashboard/', MailroomDashboardView.as_view(), name='dashboard'),
    path('receive/<int:pk>/', MailroomReceiveView.as_view(), name='receive'),
    path('approve/<int:pk>/', MailroomApproveView.as_view(), name='approve'),
    path('route/<int:pk>/', MailroomRouteView.as_view(), name='route'),
]
