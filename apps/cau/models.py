from django.db import models
from django.conf import settings
from apps.mail.models import MailRecord


class CAUMailDetail(models.Model):
    mail = models.OneToOneField(
        MailRecord, on_delete=models.CASCADE, related_name='cau_detail'
    )
    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='assigned_cau_mails'
    )
    document_types = models.ManyToManyField(
        'departments.DocumentType', blank=True,
        related_name='cau_mails'
    )
    additional_notes = models.TextField(blank=True)
    discrepancy_count = models.IntegerField(default=0)
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    stored_in_wallet = models.BooleanField(default=False)
    wallet_stored_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"CAU Detail for {self.mail.reference_number}"


class DiscrepancyLog(models.Model):
    cau_detail = models.ForeignKey(
        CAUMailDetail, on_delete=models.CASCADE, related_name='discrepancies'
    )
    logged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='logged_discrepancies'
    )
    description = models.TextField()
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='resolved_discrepancies'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Resolved" if self.resolved else "Open"
        return f"Discrepancy #{self.id} ({status}) for {self.cau_detail.mail.reference_number}"

    class Meta:
        ordering = ['-created_at']


class WalletDocument(models.Model):
    cau_detail = models.ForeignKey(
        CAUMailDetail, on_delete=models.CASCADE, related_name='wallet_documents'
    )
    retrieved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='retrieved_wallet_docs'
    )
    retrieved_at = models.DateTimeField(null=True, blank=True)
    return_reason = models.TextField(blank=True)
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='returned_wallet_docs'
    )
    returned_at = models.DateTimeField(null=True, blank=True)
    retrieval_note = models.TextField(blank=True)

    def __str__(self):
        status = "Retrieved" if self.retrieved_by and not self.returned_by else "In Wallet"
        return f"Wallet Doc for {self.cau_detail.mail.reference_number} ({status})"


class WalletRetrievalLog(models.Model):
    wallet_document = models.ForeignKey(
        WalletDocument, on_delete=models.CASCADE, related_name='retrieval_logs'
    )
    retrieved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='wallet_retrievals'
    )
    retrieved_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='wallet_returns'
    )
    returned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Retrieval log for {self.wallet_document.cau_detail.mail.reference_number}"

    class Meta:
        ordering = ['-retrieved_at']
