# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from django.urls import include, path
from . import views

urlpatterns = [
    path('land', views.LandSummaryView.as_view()),
    path('land/countries', views.CountryListView.as_view()),
    path('land/countries/<int:country_id>', views.CountryView.as_view()),
    path('land/countries/<int:country_id>/states', views.StateListView.as_view()),
    path('land/countries/<int:country_id>/biomes', views.BiomeListView.as_view()),
    path('land/countries/<int:country_id>/vegetation-types', views.VegetationTypeListView.as_view()),
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