# Simulador Agroflorestal Regenera (SAR)
# Copyright (C) 2026  Lucas Marques and Regenera Mata Atlântica

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses>.

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
            # 'content__acceptor',
        )
    
    def with_user_endorsement_info(self, user):
        return self.prefetch_related(
            Prefetch(
                'content__endorsements',
                queryset=apps.get_model('core', 'ContentEndorsement').objects.active().filter(endorser_id=user.id)
            )
        )
    
    def get_important_fields(self):
        return [
            'content__status',
            'content__source_id',
            'content__endorsements_count',
            'content__endorsements__id',
            'content__endorsements__endorser_id',
            'content__proposed_at',
            'content__accepted_at',
            'content__rejected_at',
            'content__proposer__id',
            'content__proposer__email',
            'content__proposer__first_name',
            'content__proposer__last_name',
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
