from django.db import models

class PlantValueManager(models.Manager):
  def denormalized(self):
    return self.get_queryset().select_related(
        'trait',
        'trait__name_text',
        'trait__section_text',
    ).prefetch_related(
      'plant_value_texts',
      'plant_value_texts__text'
    )
