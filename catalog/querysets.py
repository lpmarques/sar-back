from django.apps import apps
from django.db.models import QuerySet, Prefetch

class PlantQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related('content')

    def with_popular_names(self, custom_filters: dict):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)

        return self.prefetch_related(
            Prefetch(
                'popular_names',
                queryset=apps.get_model('catalog', 'PopularName').objects.filter(**filters)
            ),
        )
  
    def with_taxa(self, custom_filters: dict):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)
        
        return self.prefetch_related(
            Prefetch(
                'taxa',
                queryset=apps.get_model('catalog', 'Taxon').objects.filter(**filters)
            )
        )
  
    def with_trait_values(self, custom_filters: dict):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)
        
        return self.prefetch_related(
            Prefetch(
                'trait_values',
                queryset=apps.get_model('catalog', 'TraitValue').objects.select_related(
                    'trait',
                    'trait__name_text',
                ).prefetch_related(
                    'texts',
                ).filter(**filters)
            )
        )
  
    def with_natural_occurrence_regions(self, custom_filters: dict):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)
        
        return self.prefetch_related(
            Prefetch(
                'natural_occurrence_regions',
                queryset=apps.get_model('catalog', 'NaturalOccurrenceRegion').objects.filter(**filters)
            )
        )
  
    def with_invasion_risk_regions(self, custom_filters: dict):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)
        
        return self.prefetch_related(
            Prefetch(
                'invasion_risk_regions',
                queryset=apps.get_model('catalog', 'InvasionRiskRegion').objects.filter(**filters)
            )
        )

class PopularNameQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'content',
            'content__proposer',
            'content__source',
        )

class TaxonQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'content',
            'content__proposer',
            'content__source',
        )

class TraitQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'name_text',
            'section_text',
        ).prefetch_related(
            'text_value_options',
        )

class TraitValueQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'content',
            'content__proposer',
            'content__source',
            'trait',
            'trait__name_text',
            'trait__section_text',
        ).prefetch_related(
            'texts',
            'trait__text_value_options',
        )

class NaturalOccurrenceRegionQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'content',
            'content__proposer',
            'content__source',
            'country',
            'country__name_text',
            'state',
            'biome',
            'vegetation_type',
        ).only(
            'plant_id',
            'country__name_text',
            'state__name',
            'state__code',
            'biome__name',
            'vegetation_type__name',
            'content__status',
            'content__proposer__id',
            'content__proposer__email',
            'content__proposer__first_name',
            'content__proposer__last_name',
            'content__source__id',
            'content__source__type__is_static',
            'content__source__type__name_text__pt_br',
            'content__source__field_values__value',
            'content__source__field_values__field__schema',
            'content__source__field_values__field__name_text__pt_br',
            'content__source__created_at',
            'content__source__deleted_at',
            'content__proposed_at',
            'content__accepted_at',
            'content__rejected_at',
        )

class InvasionRiskRegionQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'content',
            'content__proposer',
            'content__source',
            'country',
            'country__name_text',
            'state',
            'biome',
        )
