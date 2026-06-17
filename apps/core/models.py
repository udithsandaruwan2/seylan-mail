from django.db import models
from django.contrib.auth.models import User
from apps.branches.models import Branch
from apps.departments.models import Department


class Profile(models.Model):
    ROLE_CHOICES = [
        ('branch_officer', 'Branch Officer'),
        ('mailroom_staff', 'Mailroom Staff'),
        ('department_officer', 'Department Officer'),
        ('cau_officer', 'CAU Officer'),
        ('cau_admin', 'CAU Admin'),
        ('mailroom_admin', 'Mailroom Admin'),
        ('system_admin', 'System Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='officers'
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='officers'
    )
    assigned_branches = models.ManyToManyField(
        Branch, blank=True, related_name='assigned_cau_officers'
    )

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"

    class Meta:
        ordering = ['-created_at']
