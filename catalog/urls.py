from django.urls import include, path
from . import views

urlpatterns = [
    path('plants', views.PlantListView.as_view()),
    path('plants/<int:plant_id>', views.PlantView.as_view()),
    path('plants/<int:plant_id>/scientific-names', views.PlantScientificNameListView.as_view()),
    path('plants/<int:plant_id>/popular-names', views.PlantPopularNameListView.as_view()),
    path('plants/<int:plant_id>/trait-values', views.PlantTraitValueListView.as_view()),
    path('plants/<int:plant_id>/natural-occurrence-regions', views.PlantNaturalOccurrenceRegionListView.as_view()),
    path('popular-names', views.PopularNameListView.as_view()),
    path('scientific-names', views.ScientificNameListView.as_view()),
    path('traits', views.TraitListView.as_view()),
    path('natural-occurrence-regions', views.NaturalOccurrenceRegionListView.as_view()),
]