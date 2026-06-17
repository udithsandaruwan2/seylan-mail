from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to restrict access based on user role"""
    allowed_roles = []

    def test_func(self):
        if not hasattr(self.request.user, 'profile'):
            return False
        user_role = self.request.user.profile.role
        return user_role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("You do not have permission to access this page.")


class BranchOfficerMixin(RoleRequiredMixin):
    allowed_roles = ['branch_officer', 'mailroom_staff', 'mailroom_admin', 'system_admin']


class MailroomStaffMixin(RoleRequiredMixin):
    allowed_roles = ['mailroom_staff', 'mailroom_admin', 'system_admin']


class DepartmentOfficerMixin(RoleRequiredMixin):
    allowed_roles = ['department_officer', 'mailroom_staff', 'mailroom_admin', 'system_admin']


class CAUOfficerMixin(RoleRequiredMixin):
    allowed_roles = ['cau_officer', 'cau_admin', 'system_admin']


class CAUAdminMixin(RoleRequiredMixin):
    allowed_roles = ['cau_admin', 'system_admin']


class MailroomAdminMixin(RoleRequiredMixin):
    allowed_roles = ['mailroom_admin', 'system_admin']


class SystemAdminMixin(RoleRequiredMixin):
    allowed_roles = ['system_admin']
