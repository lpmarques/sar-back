from django.urls import include, path
from . import views

urlpatterns = [
    # path('routes', views.getRoutes),
    path('countries', views.CountryListView.as_view()),
    path('countries/<int:country_id>', views.CountryView.as_view()),
    path('countries/<int:country_id>/states', views.StateListView.as_view()),
    path('states/<int:state_id>', views.StateView.as_view()),
    path('states/<int:state_id>/municipalities', views.MunicipalityListView.as_view()),
    path('municipalities/<int:municipality_id>', views.MunicipalityView.as_view()),
]