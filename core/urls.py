from django.urls import include, path
from . import views

urlpatterns = [
    path('routes/', views.getRoutes),
    path('user', views.OwnUserView.as_view()),
	path('user/token', views.UserTokenView.as_view()),
    path('users/<str:id>', views.UserView.as_view()),
]