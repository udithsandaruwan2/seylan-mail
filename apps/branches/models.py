from django.db import models
from django.contrib.auth.models import User


class Branch(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    assigned_cau_officer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_branches_as_officer'
    )

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ['name']
