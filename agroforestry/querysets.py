from django.apps import apps
from django.db.models import QuerySet, Prefetch

class SiteQuerySet(QuerySet):
    def active(self):
        return self.filter(site__deleted_at=None)
    
    def denormalized(self):
        return self.select_related(
            'site__country',
            'site__state',
            'site__municipality',
            'site__biome',
            'site__vegetation_type',
            'site__country__name_text',
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
