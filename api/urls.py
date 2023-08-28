from django.urls import path
from . import views
from .views import CreateUserAPIView,UpdateUserAPIView,DeleteUserAPIView,ListUserAPIView
from .views import LoginAPIView,TagViewSet,PropertyViewSet,PropertyTypeViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'propertyType', PropertyTypeViewSet)
router.register(r'properties', PropertyViewSet)

urlpatterns = [
    path('', views.index,name="index"),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('users/', ListUserAPIView.as_view(), name='list-user'),
    path('create/', CreateUserAPIView.as_view(), name='create-user'),
    path('update/<str:user_id>/', UpdateUserAPIView.as_view(), name='update-user'),
    path('user/<str:user_id>/delete/', DeleteUserAPIView.as_view(), name='delete-user'),
    path('api/', include(router.urls)),  # Include the router's URLs

]
