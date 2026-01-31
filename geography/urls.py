from django.urls import include, path
from . import views

urlpatterns = [
    # path('routes', views.getRoutes),
    path('land', views.LandSummaryView.as_view()),
    path('land/countries', views.CountryListView.as_view()),
    path('land/countries/<int:country_id>', views.CountryView.as_view()),
    path('land/countries/<int:country_id>/states', views.StateListView.as_view()),
    path('land/countries/<int:country_id>/biomes', views.BiomeListView.as_view()),
    path('land/countries/<int:country_id>/vegetation-types', views.VegetationTypeListView.as_view()),
    path('land/countries/<int:country_id>', views.BiomeListView.as_view()),
    path('land/states/<int:state_id>', views.StateView.as_view()),
    path('land/states/<int:state_id>/municipalities', views.MunicipalityListView.as_view()),
    path('land/municipalities/<int:municipality_id>', views.MunicipalityView.as_view()),
    path('land/biomes/<int:biome_id>', views.BiomeView.as_view()),
    path('land/vegetation-types/<int:vegetation_type_id>', views.VegetationTypeView.as_view()),
    path('climate', views.ClimateSummaryView.as_view()),
    path('climate/droughts', views.DroughtListView.as_view()),
    path('climate/normals', views.ClimateNormalListView.as_view()),
    path('climate/elevation', views.ElevationView.as_view()),
    path('soil', views.SoilSummaryView.as_view()),
    path('soil/acidity-levels', views.SoilAcidityLevelListView.as_view()),
    path('soil/ph', views.SoilPhView.as_view()),
    path('soil/texture-types', views.SoilTextureTypeListView.as_view()),
]