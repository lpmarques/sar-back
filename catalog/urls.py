from django.urls import include, path
from . import views

urlpatterns = [
    # path('routes', views.getRoutes),
    path('plants', views.PlantListView.as_view()),
    path('plants/<int:plant_id>', views.PlantView.as_view()),
    path('plants/<int:plant_id>/scientific-names', views.ScientificNameListView.as_view()),
    path('plants/<int:plant_id>/popular-names', views.PopularNameListView.as_view()),
    path('plants/<int:plant_id>/traits', views.PlantTraitListView.as_view()),
    path('popular-names', views.PopularNameListView.as_view()),
    path('scientific-names', views.ScientificNameListView.as_view()),
]