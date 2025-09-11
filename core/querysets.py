from django.apps import apps
from django.db.models import QuerySet, Prefetch

class ContentEndorsementQuerySet(QuerySet):
    def active(self):
        return self.filter(deleted_at=None)

    def denormalized(self):
        return self.select_related(
            'endorser',
        )

class SourceQuerySet(QuerySet):
    def active(self):
        return self.filter(deleted_at=None)
    
    def static(self):
        return self.filter(type__is_static=True)

    def denormalized(self):
        return self.select_related(
            'type',
            'type__name_text',
        ).prefetch_related(
            Prefetch(
                'field_values',
                queryset=apps.get_model('core', 'SourceFieldValue').objects.active().select_related(
                    'field',
                    'field__name_text',
                    'field__description_text',
                )
            ),
        )
  
class SourceFieldQuerySet(QuerySet):
    def active(self):
        return self.filter(deleted_at=None)
  
    def denormalized(self):
        return self.select_related(
            'name_text',
        )
    
class SourceFieldValueQuerySet(QuerySet):
    def active(self):
        return self.filter(deleted_at=None)

class SourceTypeQuerySet(QuerySet):
    def active(self):
        return self.filter(deleted_at=None)
  
    def denormalized(self):
        return self.select_related(
            'name_text',
        ).prefetch_related(
            Prefetch(
                'field_set',
                queryset=apps.get_model('core', 'SourceField').objects.active().select_related(
                    'name_text',
                    'description_text',
                )
            ),
        )
