from rest_framework.permissions import BasePermission

from .models import Employee


def employee_of(user):
    return getattr(user, "employee", None)


class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        employee = employee_of(request.user)
        return bool(employee and employee.role == Employee.ADMIN)


class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        employee = employee_of(request.user)
        return bool(employee and employee.role in [Employee.ADMIN, Employee.MANAGER])
