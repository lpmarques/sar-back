from django.db.models import QuerySet

class ContentEndorsementQuerySet(QuerySet):
  def active(self):
    return self.filter(deleted_at=None)

  def denormalized(self):
    return self.select_related(
      'endorser'
    )

  def popular_name_endorsements(self):
    return self.denormalized().filter(content_type='plant_popular_name')

  def scientific_name_endorsements(self):
    return self.denormalized().filter(content_type="plant_scientific_name")

  def trait_value_endorsements(self):
    return self.denormalized().filter(content_type='plant_value')

  def natural_occurrence_region_endorsements(self):
    return self.denormalized().filter(content_type='plant_natural_occurrence_region')

  def invasion_risk_region_endorsements(self):
    return self.denormalized().filter(content_type='plant_invasion_risk_region')
