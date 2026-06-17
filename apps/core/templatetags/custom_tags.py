from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def get_user_role(context):
    request = context.get('request')
    if request and hasattr(request.user, 'profile'):
        return request.user.profile.role
    return None


@register.simple_tag(takes_context=True)
def get_sidebar_links(context):
    """Return sidebar links based on user role"""
    request = context.get('request')
    if not request or not hasattr(request.user, 'profile'):
        return []
    
    role = request.user.profile.role
    
    links = [
        {'name': 'Dashboard', 'url': '/', 'icon': '📊'},
    ]
    
    if role in ['branch_officer', 'mailroom_staff', 'mailroom_admin', 'system_admin']:
        links.extend([
            {'name': 'Create Mail', 'url': '/mail/create/', 'icon': '✉️'},
            {'name': 'Mail List', 'url': '/mail/list/', 'icon': '📋'},
            {'name': 'Scan QR', 'url': '/mail/scan/', 'icon': '📷'},
        ])
    
    if role in ['mailroom_staff', 'mailroom_admin', 'system_admin']:
        links.append({'name': 'Mailroom Dashboard', 'url': '/mailroom/dashboard/', 'icon': '🏢'})
    
    if role in ['cau_officer', 'cau_admin', 'system_admin']:
        links.append({'name': 'CAU Inbox', 'url': '/cau/inbox/', 'icon': '📥'})
        links.append({'name': 'Wallet', 'url': '/cau/wallet/', 'icon': '🗄️'})
    
    if role in ['cau_admin', 'system_admin']:
        links.append({'name': 'CAU Admin', 'url': '/cau/admin/dashboard/', 'icon': '⚙️'})
    
    if role in ['department_officer', 'system_admin']:
        links.append({'name': 'Department Inbox', 'url': '/dept/inbox/', 'icon': '📬'})
    
    if role in ['mailroom_admin', 'system_admin']:
        links.append({'name': 'Admin Dashboard', 'url': '/admin-dashboard/mail/', 'icon': '🔧'})
    
    return links


@register.filter
def get_status_badge_class(status):
    """Return Tailwind classes for status badges"""
    classes = {
        'created': 'bg-gray-100 text-gray-800',
        'dispatched': 'bg-blue-100 text-blue-800',
        'received_mailroom': 'bg-purple-100 text-purple-800',
        'sorted': 'bg-indigo-100 text-indigo-800',
        'approved': 'bg-green-100 text-green-800',
        'routed': 'bg-cyan-100 text-cyan-800',
        'in_progress': 'bg-yellow-100 text-yellow-800',
        'completed': 'bg-emerald-100 text-emerald-800',
        'returned': 'bg-red-100 text-red-800',
    }
    return classes.get(status, 'bg-gray-100 text-gray-800')


@register.filter
def can_transition(current_status, new_status):
    """Check if status transition is valid (one-directional)"""
    order = [
        'created', 'dispatched', 'received_mailroom', 'sorted',
        'approved', 'routed', 'in_progress', 'completed', 'returned'
    ]
    
    try:
        current_idx = order.index(current_status)
        new_idx = order.index(new_status)
        return new_idx > current_idx
    except ValueError:
        return False
