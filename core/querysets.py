from django.apps import apps
from django.db.models import QuerySet, Prefetch

class ContentQuerySet(QuerySet):
    def proposed(self):
        return self.filter(content__status='proposed')
    
    def accepted(self):
        return self.filter(content__status='accepted')
    
    def rejected(self):
        return self.filter(content__status='rejected')

    def denormalized(self):
        return self.select_related(
            'content',
            'content__proposer',
            'content__source',
            'content__source__type',
            'content__source__type__name_text',
        ).prefetch_related(
            Prefetch(
                'content__source__field_values',
                queryset=apps.get_model('core', 'SourceFieldValue').objects.active().select_related(
                    'field',
                    'field__name_text',
                )
            ),
        )
    
    def get_important_fields(self):
        return [
            'content__status',
            'content__endorsements',
            'content__proposed_at',
            'content__accepted_at',
            'content__rejected_at',
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
            'content__source__creator_id',
            'content__source__created_at',
            'content__source__deleted_at',
        ]

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
