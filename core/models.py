from authemail.models import EmailUserManager, EmailAbstractUser
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Now
from django.contrib.postgres.fields import ArrayField
from core.querysets import ContentEndorsementQuerySet

class Content(models.Model):
    type = models.CharField(db_comment='[plant, popular_name, taxon, trait_value, natural_occurrence_region, invasion_risk_region]')
    status = models.CharField(db_default='proposed', db_comment='[proposed, accepted, rejected]')
    proposer = models.ForeignKey('User', models.DO_NOTHING, related_name="proposed_contents")
    acceptor = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True, related_name="accepted_contents")
    rejector = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True, related_name="rejected_contents")
    proposer_comment = models.CharField(blank=True, null=True)
    rejector_comment = models.CharField(blank=True, null=True)
    source = models.ForeignKey('Source', models.DO_NOTHING, blank=True, null=True, related_name="contents")
    endorsements = models.IntegerField(db_default=0)
    proposed_at = models.DateTimeField(db_default=Now())
    accepted_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"core"."contents"'


class ContentEndorsement(models.Model):
    content = models.ForeignKey(Content, models.DO_NOTHING)
    endorser = models.ForeignKey('User', models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = ContentEndorsementQuerySet().as_manager()

    class Meta:
        managed = True
        db_table = '"core"."content_endorsements"'
        unique_together = (('content', 'endorser', 'deleted_at'),)


class Source(models.Model):
    name = models.CharField(unique=True, blank=True, null=True)
    type = models.CharField() # TODO: create source_types table with is_static and name_text_id fields
    year = models.IntegerField(blank=True, null=True)
    title = models.CharField()
    authors = ArrayField(
        models.CharField(), blank=True, null=True
    )
    publisher = models.CharField(blank=True, null=True)
    url = models.CharField(blank=True, null=True)
    description = models.CharField(blank=True, null=True)
    content_author = models.ForeignKey('User', models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = '"core"."sources"'
        unique_together = (('title', 'year'),)


class Text(models.Model):
    pt_br = models.CharField()
    en = models.CharField(blank=True, null=True)
    es = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = True
        db_table = '"core"."texts"'


class User(EmailAbstractUser):
    first_name = models.CharField()
    last_name = models.CharField()
    email = models.CharField(unique=True)
    password = models.CharField()
    role = models.CharField(blank=True, null=True, db_default="regular")
    occupation = models.CharField()
    company = models.CharField(blank=True, null=True)
    country = models.CharField(blank=True, null=True)
    state = models.CharField(blank=True, null=True)
    municipality = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    date_joined = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(blank=True, null=True)
    is_staff = models.BooleanField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    is_verified = models.BooleanField(blank=True, null=True)

    objects = EmailUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'occupation']

    def anonymize(self):
        self.first_name = "Anon"
        self.last_name = "User"
        self.email = f"anon.{self.pk}@email.com"
        self.occupation = "Anon"
        self.company = None
        self.state = None
        self.municipality = None
        self.deleted_at = Now()
        self.save()

    class Meta:
        managed = True
        db_table = '"core"."users"'