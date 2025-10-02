from django.urls import include, path
from . import views

urlpatterns = [
    path('plant', views.PlantView.as_view()),
    path('plant/<int:content_id>', views.PlantView.as_view()),
    path('plants', views.PlantListView.as_view()),
    path('plants/<int:plant_id>', views.PlantView.as_view()),
    path('plants/<int:plant_id>/taxa', views.PlantTaxonListView.as_view()),
    path('plants/<int:plant_id>/popular-names', views.PlantPopularNameListView.as_view()),
    path('plants/<int:plant_id>/trait-values', views.PlantTraitValueListView.as_view()),
    path('plants/<int:plant_id>/natural-occurrence-regions', views.PlantNaturalOccurrenceRegionListView.as_view()),
    path('traits', views.TraitListView.as_view()),
    path('traits/<int:trait_id>', views.TraitView.as_view()),
    path('trait-value', views.TraitValueView.as_view()),
    path('trait-value/<int:content_id>', views.TraitValueView.as_view()),
    path('taxon', views.TaxonView.as_view()),
    path('taxon/<int:content_id>', views.TaxonView.as_view()),
    path('taxa', views.TaxonListView.as_view()),
    path('popular-name', views.PopularNameView.as_view()),
    path('popular-name/<int:content_id>', views.PopularNameView.as_view()),
    # path('popular-names', views.PopularNameListView.as_view()),
    path('natural-occurrence-region', views.NaturalOccurrenceRegionView.as_view()),
    path('natural-occurrence-region/<int:content_id>', views.NaturalOccurrenceRegionView.as_view()),
    # path('natural-occurrence-regions', views.NaturalOccurrenceRegionListView.as_view()),
]