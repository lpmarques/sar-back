from django.urls import path
from . import views

urlpatterns = [
    path('farms', views.FarmListView.as_view()),
    path('farms/<int:site_id>', views.FarmView.as_view()),
    path('farms/<int:site_id>/site-trait-values', views.SiteTraitValueListView.as_view()),
    path('farm', views.FarmView.as_view()),
    path('site-traits', views.SiteTraitListView.as_view()),
    path('site-trait-value', views.SiteTraitValueView.as_view()),
    path('site-trait-value/<int:site_trait_value_id>', views.SiteTraitValueView.as_view()),
]