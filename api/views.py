from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes,authentication_classes
from rest_framework.views import APIView
from rest_framework import status,viewsets
from django.contrib.auth.hashers import make_password  
from .serializers import CustomUserSerializer,TagSerializer,PropertyTypeSerializer,PropertySerializer,ContactSerializer,PropertyListSerializer
import imghdr
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser,Tag,PropertyType,Property,Contact    
from rest_framework.generics import get_object_or_404
from django.http import Http404
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status,pagination
import json,re,os
import base64
from PIL import Image
from io import BytesIO
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.http import FileResponse
from django.conf import settings
from django.contrib.auth.models import update_last_login
import secrets
from rest_framework_simplejwt.authentication import JWTTokenUserAuthentication


def catch_all(path):
    # Construct the absolute path to the requested file
    file_path = os.path.join(settings.MEDIA_ROOT, path)

    # Check if the file exists and serve it if it does
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'))

    # If the file doesn't exist, return a 404 response
    else:
        raise Http404("File not found")



class LoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "success":True,
                    "message":"login successfully",
                    "data":
                            {
                                'name':user.name,
                                'email':user.email,
                                'role_type':user.role_type,
                                'access_token': str(refresh.access_token),
                                'refresh_token': str(refresh),
                            }
                }, status=status.HTTP_200_OK)
        else:
            return Response({"success":False,'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class CreateUserAPIView(APIView):

    # authentication_classes = [JWTTokenUserAuthentication]
    # permission_classes = [IsAuthenticated]
    def post(self, request):
        data = request.data.copy()  # Create a copy of the request data
        password = data.pop('password', None)  # Remove the password from data and get it

        if password:
            data['password'] = make_password(password)  # Hash the password

        serializer = CustomUserSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "User Created successfully",
                "data": serializer.data,
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "message": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class CountData(APIView):

    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):

        admin_count = CustomUser.objects.filter(role_type='admin').count()
        staff_count = CustomUser.objects.filter(role_type='staff').count()
        all_user_count = CustomUser.objects.all().count()

        enquiry_count = Contact.objects.all().count()
        
        all_property_count = Property.objects.all().count()
        sales_count = Property.objects.filter(category='sales').count()
        lettings_count = Property.objects.filter(category='lettings').count()
        commercial_count = Property.objects.filter(category='commercial').count()
        international_count = Property.objects.filter(category='international').count()
        
        data = {
            "user_counts": {
                "admin_count": admin_count,
                "staff_count": staff_count,
                "all_user_count": all_user_count,
            },
            "property_counts": {
                "all_property_count": all_property_count,
                "sales_count": sales_count,
                "lettings_count": lettings_count,
                "commercial_count": commercial_count,
                "international_count": international_count,
            },
            "enquiry_count": enquiry_count,
        }

        return Response({
            "success": True,
            "message": "Data retrieve sucessfully",
            "data": data,

        }, status=status.HTTP_200_OK)

class UpdateUserAPIView(APIView):
    
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]    
    def put(self, request, user_id):
        user = get_object_or_404(CustomUser, pk=user_id)  # Get the user instance by user_id

        data = request.data.copy()
        password = data.pop('password', None)
        if password:
            data['password'] = make_password(password)

        serializer = CustomUserSerializer(user, data=data, partial=True)  # Use partial=True for partial updates
        if serializer.is_valid():
            serializer.save()
            return Response({"success":True,"message": "User updated successfully.","data":serializer.data}, status=status.HTTP_200_OK)
        return Response({"success":False,"message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

class DeleteUserAPIView(APIView):

    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]
    def delete(self, request, user_id):
        try:
            user = get_object_or_404(CustomUser, pk=user_id)  # Get the user instance by user_id
            user.delete()
            return Response({"success":True,"message": "User deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

        except CustomUser.DoesNotExist:
            return Response({"success":False,"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"success":False,"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
class ListUserAPIView(APIView):
    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        custom_users = CustomUser.objects.all()
        serializer = CustomUserSerializer(custom_users, many=True)
        return Response({"success":True,"message":"data get successfully","data":serializer.data}, status=status.HTTP_200_OK)

class ListTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)
class TagViewSet(viewsets.ModelViewSet):

    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            data = {
                "success": False,
                "message": "Id not found"
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            data = {
                "success": True,
                "message": "Data created successfully",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = {
                "success": False,
                "message": serializer.errors
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        try:
            instance = self.get_object()
        except Http404:
            data = {
                "success": False,
                "message": "Data not found"
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            respDt = {
                "success": True,
                "message": "Data updated successfully",
                "data": serializer.data
            }
            return Response(data=respDt, status=status.HTTP_200_OK)
        else:
            data = {
                "success": False,
                "message": serializer.errors
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            data = {
                "success": False,
                "message": "Id not found"
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        self.perform_destroy(instance)
        data = {
            "success": True,
            "message": "Data deleted successfully"
        }
        return Response(data, status=status.HTTP_204_NO_CONTENT)
     
class ListPropertyTypeViewSet(viewsets.ReadOnlyModelViewSet):

    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer 
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)
   
class PropertyTypeViewSet(viewsets.ModelViewSet):

    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = PropertyType.objects.all()
    serializer_class = PropertyTypeSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            data = {
                "success": False,
                "message": "Id not found"
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            data = {
                "success": True,
                "message": "Data created successfully",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = {
                "success": False,
                "message": serializer.errors
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        try:
            instance = self.get_object()
        except Http404:
            data = {
                "success": False,
                "message": "Data not found"
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            data = {
                "success": True,
                "message": "Data updated successfully",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                "success": False,
                "message": serializer.errors
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            data = {
                "success": False,
                "message": "Id not found"
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        self.perform_destroy(instance)
        data = {
            "success": True,
            "message": "Data deleted successfully"
        }
        return Response(data, status=status.HTTP_204_NO_CONTENT)
class ListPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertyListSerializer
    # for slug
    def retrieve(self, request, *args, **kwargs):
        try:
            slug = kwargs.get('pk')
            print(slug)
            # instance = self.get_object()
            instance = Property.objects.filter(slug=slug).first()
            print(instance)
            if instance is None:
                raise Http404 
        except Http404:
            data = {
                "success": False,
                "message": "Slug not found"
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        page = request.query_params.get('page')
        category_type = request.query_params.get('category_type')
        
        queryset = self.get_queryset()
        if page is None and category_type is None:
            print("hello")
            serializer = self.get_serializer(queryset, many=True)
            data = {
                "success": True,
                "message": "Data retrieved successfully",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        
        if category_type:
            queryset = queryset.filter(category=category_type)
        
        paginator = pagination.PageNumberPagination()
        paginator.page_size = 12 
        
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = self.get_serializer(paginated_queryset, many=True)
        
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": {
                    "results": serializer.data,  # Serialize properties
                    "pagination": {
                        "total_pages": paginator.page.paginator.num_pages
                    }
            }
        }
        return Response(data, status=status.HTTP_200_OK)
class PropertyViewSet(viewsets.ModelViewSet):

    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    def get_serializer_class(self):
        if self.action == 'list' or self.action == 'retrieve':
            return PropertyListSerializer
        return PropertySerializer
    
    def custom_response(self, success, message=None, data=None, status_code=status.HTTP_200_OK):
        response_data = {
            "success": success,
            "message": message,
            "data": data
        }
        return Response(response_data, status=status_code)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            data = {
                "success": True,
                "message": "Data created successfully",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = {
                "success": False,
                "message": serializer.errors
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
    def list(self, request, *args, **kwargs):
        page = request.query_params.get('page')
        category_type = request.query_params.get('category_type')
        
        queryset = self.get_queryset()
        if page is None and category_type is None:
            print("hello")
            serializer = self.get_serializer(queryset, many=True)
            data = {
                "success": True,
                "message": "Data retrieved successfully",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        
        if category_type:
            queryset = queryset.filter(category=category_type)
        
        paginator = pagination.PageNumberPagination()
        paginator.page_size = 12 
        
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        
        serializer = self.get_serializer(paginated_queryset, many=True)
        
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": {
                    "results": serializer.data,  # Serialize properties
                    "pagination": {
                        "total_pages": paginator.page.paginator.num_pages
                    }
            }
        }
        return Response(data, status=status.HTTP_200_OK)
    # def list(self, request, *args, **kwargs):
    #     queryset = self.get_queryset()
    #     serializer = self.get_serializer(queryset, many=True)
    #     data = {
    #         "success": True,
    #         "message": "Data retrieved successfully",
    #         "data": serializer.data
    #     }
    #     return Response(data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            data = {
                "success": False,
                "message": "Id not found"
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance)
        data = {
            "success": True,
            "message": "Data retrieved successfully",
            "data": serializer.data
        }
        return Response(data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            data = {
                "success": False,
                "message": "Id not found"
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

        self.perform_destroy(instance)
        data = {
            "success": True,
            "message": "Data deleted successfully"
        }
        return Response(data, status=status.HTTP_204_NO_CONTENT)

class CreateContactViewSet(viewsets.GenericViewSet):
    serializer_class = ContactSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Save the object to the database
            serializer.save()
            data = {
                "success": True,
                "message": "Data created successfully",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = {
                "success": False,
                "message": serializer.errors
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
class ListContactViewSet(viewsets.ReadOnlyModelViewSet):

    authentication_classes = [JWTTokenUserAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer

@api_view(['GET'])
def index(request):
    return Response({"message": "hii"})