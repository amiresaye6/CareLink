from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from django.shortcuts import get_object_or_404

from accounts.models import DoctorProfile
from dashboard.api.doctor.serializers import (
    DoctorProfileModelSerializer
)


def _get_logged_in_doctor(request):
    try:
        return request.user.doctor_profile
    except Exception:
        return None


@api_view(['GET'])
def get_doctor_by_id(request, id):
    doctor = get_object_or_404(DoctorProfile, pk=id)
    doctor = DoctorProfileModelSerializer(doctor)
    return Response(doctor.data)


@api_view(['PUT'])
def update_doctor_by_id(request, id):
    doctor = get_object_or_404(DoctorProfile, pk=id)
    doctor = DoctorProfileModelSerializer(doctor, data=request.data, partial=True)
    if doctor.is_valid():
        doctor.save()
        return Response({'message': 'object updated!', 'doctor': doctor.data}, status=status.HTTP_200_OK)
    return Response({'message': 'not valid', 'errors': doctor.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_logged_in_doctor(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)
    doctor = DoctorProfileModelSerializer(doctor)
    return Response(doctor.data)


@api_view(['PUT'])
def update_logged_in_doctor(request):
    doctor = _get_logged_in_doctor(request)
    if not doctor:
        return Response({'message': 'not allowed'}, status=status.HTTP_403_FORBIDDEN)

    doctor = DoctorProfileModelSerializer(doctor, data=request.data, partial=True)
    if doctor.is_valid():
        doctor.save()
        return Response({'message': 'object updated!', 'doctor': doctor.data}, status=status.HTTP_200_OK)
    return Response({'message': 'not valid', 'errors': doctor.errors}, status=status.HTTP_400_BAD_REQUEST)




