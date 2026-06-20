from rest_framework.permissions import BasePermission, IsAuthenticated


def get_role_code(user):
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'admin'
    profile = getattr(user, 'profile', None)
    if profile and profile.role:
        return profile.role.code
    return None


def is_admin(user):
    return get_role_code(user) == 'admin'


def is_inspector(user):
    return get_role_code(user) == 'inspector'


def is_technician(user):
    return get_role_code(user) == 'technician'


def is_farmer(user):
    return get_role_code(user) == 'farmer'


def get_user_farmer(user):
    if not user or not user.is_authenticated:
        return None
    farmer = getattr(user, 'farmer_profile', None)
    if farmer:
        return farmer
    from core.models import Farmer
    try:
        return Farmer.objects.get(user=user)
    except Farmer.DoesNotExist:
        return None


def get_farmer_cage_ids(user):
    farmer = get_user_farmer(user)
    if not farmer:
        return []
    from core.models import Cage
    return list(Cage.objects.filter(cage_farmers__farmer=farmer).values_list('id', flat=True))


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return is_admin(request.user)


class IsInspectorOrAbove(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        code = get_role_code(request.user)
        return code in ('admin', 'inspector')


class IsTechnicianOrAbove(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        code = get_role_code(request.user)
        return code in ('admin', 'technician')


class IsFarmerOrAbove(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return get_role_code(request.user) is not None


class IsRoleAllowed(BasePermission):
    allowed_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if is_admin(request.user):
            return True
        code = get_role_code(request.user)
        return code in self.allowed_roles


def role_permission(*roles):
    class DynamicRolePermission(IsRoleAllowed):
        allowed_roles = list(roles)
    return DynamicRolePermission
