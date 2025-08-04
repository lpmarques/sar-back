from django.apps import apps
from django.db.models import QuerySet, Prefetch

class PlantQuerySet(QuerySet):
  def with_popular_names(self, custom_filters: dict):
    filters = {'content_status__in': ['accepted']}
    filters.update(custom_filters)

    return self.prefetch_related(
        Prefetch(
            'popular_names',
            queryset=apps.get_model('catalog', 'PlantPopularName').objects.filter(**filters)
        )
    )
  
  def with_scientific_names(self, custom_filters: dict):
    filters = {'content_status__in': ['accepted']}
    filters.update(custom_filters)

    return self.prefetch_related(
        Prefetch(
            'scientific_names',
            queryset=apps.get_model('catalog', 'PlantScientificName').objects.filter(**filters)
        )
    )
  
  def with_trait_values(self, custom_filters: dict):
    filters = {'content_status__in': ['accepted']}
    filters.update(custom_filters)
    
    return self.prefetch_related(
        Prefetch(
            'values',
            queryset=apps.get_model('catalog', 'PlantValue').objects.denormalized().filter(**filters)
        )
    )
  
  def with_natural_occurrence_regions(self, custom_filters: dict):
    filters = {'content_status__in': ['proposed']} # TODO: change to 'accepted'
    filters.update(custom_filters)
    
    return self.prefetch_related(
        Prefetch(
            'natural_occurrence_regions',
            queryset=apps.get_model('catalog', 'PlantNaturalDistributionRegion').objects.denormalized().filter(**filters)
        )
    )
  
class PlantPopularNameQuerySet(QuerySet):
  def denormalized(self):
    return self.select_related(
      'content_author',
      'source',
    )
  
class PlantScientificNameQuerySet(QuerySet):
  def denormalized(self):
    return self.select_related(
      'content_author',
      'source',
    )

class PlantTraitQuerySet(QuerySet):
  def denormalized(self):
    return self.select_related(
        'name_text',
        'section_text',
    ).prefetch_related(
        'text_value_options',
        'text_value_options__option_text'
    )

class PlantValueQuerySet(QuerySet):
  def denormalized(self):
    return self.select_related(
        'content_author',
        'source',
        'trait',
        'trait__name_text',
        'trait__section_text',
    ).prefetch_related(
        'plant_value_texts',
        'plant_value_texts__text',
        'trait__text_value_options',
        'trait__text_value_options__option_text',
    )

class PlantNaturalOccurrenceRegionQuerySet(QuerySet):
  def denormalized(self):
    return self.select_related(
      'country',
      'country__name_text',
      'state',
      'biome',
      'vegetation_type',
      'content_author',
      'source',
    ).only(
      'plant_id',
      'country__name_text',
      'state__name',
      'state__code',
      'biome__name',
      'vegetation_type__name',
      'content_status',
      'content_author__id',
      'content_author__email',
      'content_author__first_name',
      'content_author__last_name',
      'source__id',
      'source__type',
      'source__year',
      'source__publication_title',
      'source__publication_authors',
      'source__publisher',
      'source__url',
      'source__description',
      'created_at',
    )
