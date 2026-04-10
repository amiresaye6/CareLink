from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status ,permissions
from medical.api.serializers import ConsultationRecordSerializer, PrescriptionItemSerializer, TestRequestSerializer
from medical.models import ConsultationRecord, PrescriptionItem, TestRequest
from appointments.models import Appointment
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser ,IsAuthenticatedOrReadOnly ,BasePermission
# from rest_framework.permissions import SAFE_METHODS
from accounts.apis  import IsDoctor, IsPatient, IsReceptionist, IsAdmin ,IsDoctorOrReadOnly, IsPatientOrReadOnly, IsReceptionistOrReadOnly, IsAdminOrReadOnly ,IsDoctorOrAdmin, IsPatientOrAdmin, IsReceptionistOrAdmin ,IsDoctorOrReceptionist, IsPatientOrReceptionist, IsAdminOrReceptionist ,IsDoctorOrPatient, IsDoctorOrReceptionistOrAdmin, IsPatientOrReceptionistOrAdmin , IsDoctorOrPatientOrAdmin ,IsDoctorOrPatientOrReceptionist ,IsDoctorOrReceptionistOrAdmin , IsPatientOrReceptionistOrAdmin

# Create your views here.
@api_view(['GET', 'POST'])
@permission_classes([IsDoctor])
def consultation_list(request):
    if request.method == 'POST':
        serializer = ConsultationRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    consultations = ConsultationRecord.objects.all()
    serializer = ConsultationRecordSerializer(consultations, many=True)
    return Response(serializer.data)
@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsDoctor])
def consultation_detail(request, id):
    consultation = get_object_or_404(ConsultationRecord, pk=id)

    if request.method == 'GET':
        return Response(ConsultationRecordSerializer(consultation).data)

    elif request.method == 'PUT':
        serializer = ConsultationRecordSerializer(consultation, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        consultation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsDoctor])
def prescription_list(request):
    if request.method == 'POST':
        serializer = PrescriptionItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    prescriptions = PrescriptionItem.objects.all()
    serializer = PrescriptionItemSerializer(prescriptions, many=True)
    return Response(serializer.data)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsDoctor])
def prescription_detail(request, id):
    prescription = get_object_or_404(PrescriptionItem, pk=id)

    if request.method == 'GET':
        return Response(PrescriptionItemSerializer(prescription).data)

    elif request.method == 'PUT':
        serializer = PrescriptionItemSerializer(prescription, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        prescription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET', 'POST'])
@permission_classes([IsDoctor])
def test_list(request):
    if request.method == 'POST':
        serializer = TestRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    tests = TestRequest.objects.all()
    serializer = TestRequestSerializer(tests, many=True)
    return Response(serializer.data)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsPatient])
def test_detail(request, id):
    test = get_object_or_404(TestRequest, pk=id)

    if request.method == 'GET':
        return Response(TestRequestSerializer(test).data)

    elif request.method == 'PUT':
        serializer = TestRequestSerializer(test, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)