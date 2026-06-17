from django.urls import path
from apps.mail.views import (
    MailCreateView, MailDetailView, MailQRPrintView,
    MailScanView, MailListView
)

app_name = 'mail'

urlpatterns = [
    path('create/', MailCreateView.as_view(), name='create'),
    path('<int:pk>/detail/', MailDetailView.as_view(), name='detail'),
    path('<int:pk>/qr/', MailQRPrintView.as_view(), name='qr_print'),
    path('scan/', MailScanView.as_view(), name='scan'),
    path('list/', MailListView.as_view(), name='list'),
]
