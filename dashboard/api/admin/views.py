from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.db.models import Q

from accounts.models import User
from .serializer import (
    UserListSerializer,
    UserDetailsSerializer,
    UserUpdateSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    """
    API viewSet for gettign users
    
     Endpoints:
        - GET /api/users/                   -> List all users (paginated, filterable)
        - GET /api/users/{id}/              -> Get single user with all details
        - PATCH /api/users/{id}/            -> Update user (activate/deactivate)
    
    Query Parameters:
        - ?role=DOCTOR                      -> Filter by role
        - ?is_active=true                   -> Filter by active status
        - ?search=ahmed                     -> Search by username/email/name
        - ?page=2                           -> Pagination
        - Combine: ?role=DOCTOR&is_active=true&search=ahmed&page=1
    """
    
    queryset = User.objects.all()

    #  to=do return it when azzazy finishs his part :__:
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        """
        chose which serializer for each actoin: 
            UserListSerializer,
            UserDetailsSerializer
        """
        if self.action == 'list':
            return UserListSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        else:
            return UserDetailsSerializer


    def get_queryset(self):
        """
        Filter the queryset based on query params
            - by role               >> role
            - by active state       >> is_active
            - by search statment    >> search
        """
        
        queryset = User.objects.all()
        
        role = self.request.query_params.get('role')
        if role:
            valid_roles = dict(User.ROLE_CHOICES)
            if role in valid_roles:
                queryset = queryset.filter(role = role)
                
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active = is_active_bool)
            

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter (
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
            
        return queryset