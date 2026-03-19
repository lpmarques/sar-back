# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from django.urls import path
from . import views

urlpatterns = [
    path('farms', views.FarmListView.as_view()),
    path('farms/<int:farm_id>', views.FarmView.as_view()),
    path('farms/<int:farm_id>/fields', views.FieldListView.as_view()),
    path('farms/<int:farm_id>/site-trait-values', views.FarmTraitValueListView.as_view()),
    path('farms/<int:farm_id>/site-plant-fitnesses', views.FarmPlantFitnessListView.as_view()),
    path('farms/<int:farm_id>/site-plant-fitnesses/<int:plant_id>', views.FarmPlantFitnessView.as_view()),
    path('site-traits', views.SiteTraitListView.as_view()),
    path('site-trait-values', views.SiteTraitValueView.as_view()),
    path('site-trait-values/<int:site_trait_value_id>', views.SiteTraitValueView.as_view()),
    path('fields', views.FieldView.as_view()),
    path('fields/<int:field_id>', views.FieldView.as_view()),
    path('fields/<int:field_id>/site-trait-values', views.FieldTraitValueListView.as_view()),
]