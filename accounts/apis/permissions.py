from rest_framework.permissions import BasePermission

class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role=="PATIENT")
    

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role=="DOCTOR")
    

class IsReceptionist(BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and request.user.role=="RECEPTIONIST")
    
    
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and request.user.role=="ADMIN")
    
