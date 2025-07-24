from django.apps import apps
from django.db.models import QuerySet, Prefetch

class PlantQuerySet(QuerySet):
  def with_popular_names(self, custom_filters: dict):
    filters = {'content_status': 'accepted'}
    filters.update(custom_filters)

    return self.prefetch_related(
        Prefetch(
            'popular_names',
            queryset=apps.get_model('catalog', 'PlantPopularName').objects.filter(**filters)
        )
    )
  
  def with_scientific_names(self, custom_filters: dict):
    filters = {'content_status': 'accepted'}
    filters.update(custom_filters)

    return self.prefetch_related(
        Prefetch(
            'scientific_names',
            queryset=apps.get_model('catalog', 'PlantScientificName').objects.filter(**filters)
        )
    )
  
  def with_trait_values(self, custom_filters: dict):
    filters = {'content_status': 'accepted'}
    filters.update(custom_filters)
    
    return self.prefetch_related(
        Prefetch(
            'values',
            queryset=apps.get_model('catalog', 'PlantValue').objects.denormalized().filter(**filters)
        )
    )

class PlantValueQuerySet(PlantQuerySet):
  def denormalized(self):
    return self.select_related(
        'trait',
        'trait__name_text',
        'trait__section_text',
    ).prefetch_related(
        'plant_value_texts',
        'plant_value_texts__text'
    )

class PlantTraitQuerySet(PlantQuerySet):
  def denormalized(self):
    return self.select_related(
        'name_text',
        'section_text',
    ).prefetch_related(
        'text_value_options',
        'text_value_options__option_text'
    )
