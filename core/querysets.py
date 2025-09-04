from django.db.models import QuerySet

class ContentEndorsementQuerySet(QuerySet):
  def active(self):
    return self.filter(deleted_at=None)

  def denormalized(self):
    return self.select_related(
      'endorser',
    )
