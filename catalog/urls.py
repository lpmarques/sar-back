from django.urls import include, path
from . import views

urlpatterns = [
    path('plants', views.PlantListView.as_view()),
    path('plants/<int:plant_id>', views.PlantView.as_view()),
    path('plants/<int:plant_id>/taxa', views.PlantTaxonListView.as_view()),
    path('plants/<int:plant_id>/popular-names', views.PlantPopularNameListView.as_view()),
    path('plants/<int:plant_id>/trait-values', views.PlantTraitValueListView.as_view()),
    path('plants/<int:plant_id>/natural-occurrence-regions', views.PlantNaturalOccurrenceRegionListView.as_view()),
    path('traits', views.TraitListView.as_view()),
    path('traits/<int:trait_id>', views.TraitView.as_view()),
    path('trait-values', views.TraitValueListView.as_view()),
    path('trait-values/<int:trait_value_id>', views.TraitValueView.as_view()),
    path('taxa', views.TaxonListView.as_view()),
    path('taxa/<int:taxon_id>', views.TaxonView.as_view()),
    path('popular-names', views.PopularNameListView.as_view()),
    path('popular-names/<int:popular_name_id>', views.PopularNameView.as_view()),
    path('natural-occurrence-regions', views.NaturalOccurrenceRegionListView.as_view()),
    path('natural-occurrence-regions/<int:natural_occurrence_region_id>', views.NaturalOccurrenceRegionView.as_view()),
]