from django.urls import include, path
from . import views

urlpatterns = [
    path('plants', views.PlantListView.as_view()),
    path('plants/<int:plant_id>', views.PlantView.as_view()),
    path('plants/<int:plant_id>/trait-values', views.PlantTraitValueListView.as_view()),
    path('plants/<int:plant_id>/popular-names', views.PlantPopularNameListView.as_view()),
    path('plants/<int:plant_id>/scientific-names', views.PlantTaxonListView.as_view()),
    path('plants/<int:plant_id>/natural-occurrence-regions', views.PlantNaturalOccurrenceRegionListView.as_view()),
    path('traits', views.TraitListView.as_view()),
    path('traits/<int:trait_id>', views.TraitView.as_view()),
    path('trait-value', views.TraitValueView.as_view()),
    path('trait-value/<int:content_id>', views.TraitValueView.as_view()),
    path('popular-names', views.PopularNameListView.as_view()),
    path('scientific-names', views.TaxonListView.as_view()),
    path('natural-occurrence-regions', views.NaturalOccurrenceRegionListView.as_view()),
]