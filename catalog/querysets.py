# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from django.apps import apps
from django.db.models import QuerySet, Prefetch, Q
from core.querysets import ContentQuerySet

class PlantQuerySet(ContentQuerySet):
    def with_popular_names(self, custom_filters={}, q_filters=[]):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)

        return self.prefetch_related(
            Prefetch(
                'popular_names',
                queryset=apps.get_model('catalog', 'PopularName').objects.select_related(
                    'content',
                ).filter(*q_filters, **filters)
            ),
        )

    def with_taxa(self, custom_filters={}, q_filters=[]):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)
        
        return self.prefetch_related(
            Prefetch(
                'taxa',
                queryset=apps.get_model('catalog', 'Taxon').objects.select_related(
                    'content',
                ).filter(*q_filters, **filters)
            )
        )
    
    def with_trait_values(self, custom_filters={}, q_filters=[]):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)
        
        return self.prefetch_related(
            Prefetch(
                'trait_values',
                queryset=apps.get_model('catalog', 'TraitValue').objects.select_related(
                    'content',
                    'trait',
                    'trait__name_text',
                ).prefetch_related(
                    'texts',
                ).filter(*q_filters, **filters)
            )
        )
    
    def with_natural_occurrence_regions(self, custom_filters={}, q_filters=[]):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)
        
        return self.prefetch_related(
            Prefetch(
                'natural_occurrence_regions',
                queryset=apps.get_model('catalog', 'NaturalOccurrenceRegion').objects.select_related(
                    'content',
                ).filter(*q_filters, **filters)
            )
        )
    
    def with_invasion_risk_regions(self, custom_filters={}, q_filters=[]):
        filters = {'content__status__in': ['accepted']}
        filters.update(custom_filters)
        
        return self.prefetch_related(
            Prefetch(
                'invasion_risk_regions',
                queryset=apps.get_model('catalog', 'InvasionRiskRegion').objects.select_related(
                    'content',
                ).filter(*q_filters, **filters)
            )
        )

class TraitQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'name_text',
            'section_text',
            'description_text',
        ).prefetch_related(
            Prefetch(
                'trait_text_value_options',
                queryset=apps.get_model('catalog', 'TraitTextValueOption').objects.select_related(
                    'value_text',
                    'description_text',
                ).order_by('pk')
            )
        )

class TraitValueQuerySet(ContentQuerySet):
    def denormalized(self):
        return super().denormalized().select_related(
            'trait',
            'trait__name_text',
            'trait__section_text',
        ).prefetch_related(
            'texts',
            'trait__text_value_options',
        )
    
    def only_important_fields(self):
        return self.only(
            'content_id',
            'plant_id',
            'trait_id',
            'value',
            'trait__data_type',
            'trait__schema',
            'trait__name',
            'trait__name_text__pt_br',
            'trait__section',
            'trait__section_text__pt_br',
            'trait__numeric_value_min',
            'trait__numeric_value_max',
            'trait__text_value_options__pt_br',
            *ContentQuerySet.get_important_fields(self)
        )

class NaturalOccurrenceRegionQuerySet(ContentQuerySet):
    def denormalized(self):
        return super().denormalized().select_related(
            'country',
            'country__name_text',
            'state',
            'biome',
            'vegetation_type',
        )
    
    def only_important_fields(self):
        return self.only(
            'content_id',
            'plant_id',
            'country__name_text',
            'state__name',
            'state__code',
            'state__country_id',
            'biome__name',
            'biome__country_id',
            'vegetation_type__name',
            'vegetation_type__country_id',
            *ContentQuerySet.get_important_fields(self)
        )

class InvasionRiskRegionQuerySet(ContentQuerySet):
    def denormalized(self):
        return super().denormalized().select_related(
            'country',
            'country__name_text',
            'state',
            'biome',
        )
