from django.db import models
from django.conf import settings
import qrcode
import hashlib
import hmac
import os
from datetime import datetime
from io import BytesIO


class MailRecord(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('dispatched', 'Dispatched'),
        ('received_mailroom', 'Received at Mailroom'),
        ('sorted', 'Sorted'),
        ('approved', 'Approved'),
        ('routed', 'Routed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('returned', 'Returned'),
    ]

    ORIGIN_TYPE_CHOICES = [
        ('branch_to_hq', 'Branch to HQ'),
        ('hq_to_branch', 'HQ to Branch'),
        ('hq_internal', 'HQ Internal'),
    ]

    reference_number = models.CharField(max_length=50, unique=True)
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    origin_type = models.CharField(max_length=20, choices=ORIGIN_TYPE_CHOICES)
    sender_branch = models.ForeignKey(
        'branches.Branch', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_mails'
    )
    sender_department = models.ForeignKey(
        'departments.Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_mails'
    )
    recipient_branch = models.ForeignKey(
        'branches.Branch', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='received_mails'
    )
    recipient_department = models.ForeignKey(
        'departments.Department', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='received_mails'
    )
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='created')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='created_mails'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    physical_received = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.reference_number} - {self.subject}"

    class Meta:
        ordering = ['-created_at']

    def generate_reference_number(self):
        today = datetime.now().strftime('%Y%m%d')
        last_mail = MailRecord.objects.filter(
            reference_number__startswith=f'MAIL-{today}-'
        ).order_by('-reference_number').first()
        
        if last_mail:
            last_num = int(last_mail.reference_number.split('-')[-1])
            next_num = last_num + 1
        else:
            next_num = 1
        
        return f'MAIL-{today}-{next_num:04d}'

    def generate_qr_hash(self):
        """Generate HMAC hash for QR code tamper detection"""
        message = self.reference_number.encode('utf-8')
        secret = settings.SECRET_KEY.encode('utf-8')
        return hmac.new(secret, message, hashlib.sha256).hexdigest()

    def generate_qr_code(self):
        """Generate QR code with reference number and HMAC hash"""
        qr_data = f"{self.reference_number}|{self.generate_qr_hash()}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO first
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Save to file
        filename = f"qr_{self.reference_number}.png"
        filepath = os.path.join(settings.MEDIA_ROOT, 'qrcodes', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(buffer.getvalue())
        
        return f'qrcodes/{filename}'

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if is_new and not self.reference_number:
            self.reference_number = self.generate_reference_number()
        
        super().save(*args, **kwargs)
        
        if is_new and not self.qr_code:
            self.qr_code = self.generate_qr_code()
            MailRecord.objects.filter(pk=self.pk).update(qr_code=self.qr_code)

    @classmethod
    def validate_qr(cls, reference_number, provided_hash):
        """Validate QR code HMAC hash"""
        try:
            mail = cls.objects.get(reference_number=reference_number)
            expected_hash = mail.generate_qr_hash()
            return hmac.compare_digest(expected_hash, provided_hash)
        except cls.DoesNotExist:
            return False


class MailStatusLog(models.Model):
    mail = models.ForeignKey(
        MailRecord, on_delete=models.CASCADE, related_name='status_logs'
    )
    status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='mail_status_changes'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.mail.reference_number} - {self.status} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


def create_mail_status_log(sender, instance, created, **kwargs):
    """Signal handler to create MailStatusLog on MailRecord creation or status change"""
    if created:
        MailStatusLog.objects.create(
            mail=instance,
            status=instance.status,
            changed_by=instance.created_by,
            note='Mail record created'
        )
    else:
        # Check if status changed
        try:
            old_instance = MailRecord.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                MailStatusLog.objects.create(
                    mail=instance,
                    status=instance.status,
                    changed_by=None,  # Will be set by view
                    note=f'Status changed from {old_instance.status} to {instance.status}'
                )
        except MailRecord.DoesNotExist:
            pass


from django.db.models.signals import post_save
post_save.connect(create_mail_status_log, sender=MailRecord)
