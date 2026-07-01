# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

from django.apps import apps
from django.contrib.gis.db.models.functions import Area
from django.db.models import QuerySet, Prefetch

class SiteQuerySet(QuerySet):
    def active(self):
        return self.filter(site__deleted_at=None)
    
    def with_area_m2(self):
        return self.annotate(
            area=Area('site__polygon')
        )
    
    def denormalized(self):
        return self.select_related(
            'site__country',
            'site__state',
            'site__municipality',
            'site__biome',
            'site__vegetation_type',
            'site__country__name_text',
        ).prefetch_related(
            Prefetch(
                'site__trait_values',
                queryset=apps.get_model('agroforestry', 'SiteTraitValue').objects.active()
            ),
        ).defer(
            'site__country__area',
            'site__state__area',
            'site__biome__area',
        )
    
class FarmQuerySet(SiteQuerySet):
    def denormalized(self):
        return super().denormalized().select_related(
            'user',
        )
    
class FieldQuerySet(SiteQuerySet):    
    def denormalized(self):
        return super().denormalized().select_related(
            'user',
            'cropping',
        )
    
class CroppingPatternQuerySet(QuerySet):
    def active(self):
        return self.filter(deleted_at=None)
    
    def public(self):
        return self.filter(is_public=True)
    
    def private(self, author_id: int):
        return self.filter(is_public=False, author_id=author_id)

    def denormalized(self):
        return self.select_related(
            'author',
        ).prefetch_related(
            Prefetch(
                'pattern_rows',
                queryset=apps.get_model('agroforestry', 'CroppingPatternRow').objects.select_related(
                    'purpose',
                    'purpose__text',
                )
            )
        ).prefetch_related(
            Prefetch(
                'pattern_rows__row_crops',
                queryset=apps.get_model('agroforestry', 'CroppingPatternCrop').objects.select_related(
                    'plant',
                )
            )
        )

class SiteTraitQuerySet(QuerySet):
    def denormalized(self):
        return self.select_related(
            'name_text',
            'section_text',
        ).prefetch_related(
            'text_value_options'
        )

class SiteTraitValueQuerySet(QuerySet):
    def active(self):
        return self.filter(deleted_at=None)

    def denormalized(self):
        return self.select_related(
            'site',
            'trait',
            'trait__name_text',
            'trait__section_text',
        ).prefetch_related(
            'texts',
            'trait__text_value_options',
        ).defer(
            'site__polygon',
        )
