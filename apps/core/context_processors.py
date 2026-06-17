from django.contrib.auth.models import User


def role_context_processor(request):
    """Add user role and sidebar links to template context"""
    if hasattr(request.user, 'profile'):
        return {
            'user_role': request.user.profile.role,
            'user_branch': request.user.profile.branch,
            'user_department': request.user.profile.department,
        }
    return {}
