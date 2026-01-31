from django.urls import include, path
from . import views

urlpatterns = [
    path('plants', views.PlantListView.as_view()),
    path('plants/<int:id>', views.PlantView.as_view()),
    path('plants/<int:id>/taxa', views.PlantTaxonListView.as_view()),
    path('plants/<int:id>/popular-names', views.PlantPopularNameListView.as_view()),
    path('plants/<int:id>/trait-values', views.PlantTraitValueListView.as_view()),
    path('plants/<int:id>/natural-occurrence-regions', views.PlantNaturalOccurrenceRegionListView.as_view()),
    path('traits', views.TraitListView.as_view()),
    path('traits/<int:id>', views.TraitView.as_view()),
    path('trait-values', views.TraitValueListView.as_view()),
    path('trait-values/<int:id>', views.TraitValueView.as_view()),
    path('taxa', views.TaxonListView.as_view()),
    path('taxa/<int:id>', views.TaxonView.as_view()),
    path('popular-names', views.PopularNameListView.as_view()),
    path('popular-names/<int:id>', views.PopularNameView.as_view()),
    path('natural-occurrence-regions', views.NaturalOccurrenceRegionListView.as_view()),
    path('natural-occurrence-regions/<int:id>', views.NaturalOccurrenceRegionView.as_view()),
]