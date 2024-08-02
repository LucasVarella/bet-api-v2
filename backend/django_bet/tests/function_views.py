#from django.shortcuts import render

from api.models import Aeroporto, Voo
from api.serializers import AeroportoSerializer

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response



@api_view(['GET', 'POST'])
def aeroportos(request):
    if request.method == 'GET':
        aeroportos = Aeroporto.objects.all()
        serializer = AeroportoSerializer(aeroportos, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = AeroportoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def aeroporto_change_delete(request, pk):
    try:
        aeroporto = Aeroporto.objects.get(pk=pk)
    except Aeroporto.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AeroportoSerializer(aeroporto)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = AeroportoSerializer(aeroporto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        aeroporto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class AeroportoChangeAndDelete(APIView):
    def get_object(self, pk):
        try:
            return Aeroporto.objects.get(pk=pk)
        except Aeroporto.DoesNotExist:
            raise NotFound()
    
    @swagger_auto_schema(
        operation_description="Este endpoint lhe fornece os dados referentes ao aeroporto especificado pelo ID",
    )
    def get(self, request, pk):
        aeroporto = self.get_object(pk)
        serializer = AeroportoSerializer(aeroporto)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Este endpoint permite que você realize alterações em um aeroporto especificado pelo ID",
    )
    def put(self, request, pk):
        aeroporto = self.get_object(pk)
        serializer = AeroportoSerializer(aeroporto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Este endpoint permite a exclusão de um aeroporto cadastrado, o qual deve ser especificado pelo ID.",
    )
    def delete(self, request, pk):
        aeroporto = self.get_object(pk)
        aeroporto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
class LeagueListAndCreate(APIView):
    @swagger_auto_schema(
        operation_description="Este endpoint lista todas as ligas presentes no banco.",
    )
    def get(self, request):
        leagues = League.objects.all()
        serializer = LeagueSerializer(leagues, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Este endpoint permite a criação de uma nova liga",
    )
    def post(self, request):
        serializer = LeagueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)