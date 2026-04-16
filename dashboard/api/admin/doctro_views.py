from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db.models import Q
from accounts.models import DoctorProfile
from .doctro_serializer import DoctorPublicSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

class DoctorListViewSet(viewsets.ModelViewSet):
    """
    Public/Receptionist view to get the list of doctors
    with search and category filtering.
    """
    queryset = DoctorProfile.objects.select_related('user').all()
    serializer_class = DoctorPublicSerializer
    permission_classes = [IsAuthenticated, AllowAny] 

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 1. Category (Specialty) Filtering
        specialty = self.request.query_params.get('specialty')
        if specialty:
            queryset = queryset.filter(specialty=specialty)

        # 2. Search (Name, Username, or Specialty)
        search_query = self.request.query_params.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__username__icontains=search_query) |
                Q(specialty__icontains=search_query)
            )

        return queryset