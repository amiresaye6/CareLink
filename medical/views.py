from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import ConsultationRecordSerializer, PrescriptionItemSerializer, TestRequestSerializer
from .models import ConsultationRecord, PrescriptionItem, TestRequest
# Create your views here.
@api_view(['GET', 'POST'])
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