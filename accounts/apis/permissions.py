from rest_framework.permissions import BasePermission

class IsPatient(BasePermission):
    def has_permission(self, request, view):
        #return bool(request.user and request.user.is_authenticated and request.user.role=="PATIENT")
        return bool(request.user and request.user.groups.filter(name='Patients').exists())
    

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        #return bool(request.user and request.user.is_authenticated and request.user.role=="DOCTOR")
        return bool(request.user and request.user.groups.filter(name='Doctors').exists())
    

class IsReceptionist(BasePermission):
    def has_permission(self, request, view):
        #return bool(request.user and request.user.is_authenticated and request.user.role=="RECEPTIONIST")
        return bool(request.user and request.user.groups.filter(name='Receptionists').exists())
    

class IsDoctorOrReceptionist(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, 'is_authenticated', False):
            return False
        return bool(
            request.user.groups.filter(name='Doctors').exists()
            or request.user.groups.filter(name='Receptionists').exists()
        )

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        #return bool(request.user and request.user.is_authenticated and request.user.role=="ADMIN")
        return bool(request.user and request.user.groups.filter(name='Admins').exists())
    
