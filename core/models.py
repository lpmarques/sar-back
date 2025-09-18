from authemail.models import EmailUserManager, EmailAbstractUser
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Now
from core.querysets import ContentEndorsementQuerySet, SourceFieldQuerySet, SourceFieldValueQuerySet, SourceQuerySet, SourceTypeQuerySet

class Content(models.Model):
    class STATUS(models.TextChoices):
        PRO = "proposed"
        ACC = "accepted"
        REJ = "rejected"

    type = models.CharField()
    status = models.CharField(db_default='proposed', choices=STATUS.choices)
    proposer = models.ForeignKey('User', models.DO_NOTHING, related_name="proposed_contents")
    acceptor = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True, related_name="accepted_contents")
    rejector = models.ForeignKey('User', models.DO_NOTHING, blank=True, null=True, related_name="rejected_contents")
    proposer_comment = models.CharField(max_length=300, blank=True, null=True)
    rejector_comment = models.CharField(max_length=300, blank=True, null=True)
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
    type = models.ForeignKey('SourceType', models.DO_NOTHING)
    creator = models.ForeignKey('User', models.DO_NOTHING)
    creator_notes = models.CharField(max_length=300, blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SourceQuerySet.as_manager()

    class Meta:
        managed = True
        db_table = '"core"."sources"'


class SourceField(models.Model):
    source_type = models.ForeignKey('SourceType', models.DO_NOTHING, related_name="field_set") # must be that name orelse serializer's default to_representation will mess things up
    name_text = models.ForeignKey('Text', models.DO_NOTHING, related_name="name_text_fields")
    description_text = models.ForeignKey('Text', models.DO_NOTHING, blank=True, null=True, related_name="description_text_fields")
    schema = models.JSONField()
    is_nullable = models.BooleanField(db_default=True)
    position = models.IntegerField()
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SourceFieldQuerySet().as_manager()

    class Meta:
        db_table = '"core"."source_fields"'
        unique_together = (('source_type', 'name_text'),)


class SourceFieldValue(models.Model):
    source = models.ForeignKey(Source, models.DO_NOTHING, related_name="field_values")
    field = models.ForeignKey(SourceField, models.DO_NOTHING)
    value = models.CharField()
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SourceFieldValueQuerySet.as_manager()

    class Meta:
        db_table = '"core"."source_field_values"'


class SourceType(models.Model):
    class Level(models.IntegerChoices):
        TYPE = 1, "type"
        SUBTYPE = 2, "subtype"

    name_text = models.OneToOneField('Text', models.DO_NOTHING)
    parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True, related_name="children")
    level = models.IntegerField(choices=Level.choices)
    is_static = models.BooleanField()
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = SourceTypeQuerySet().as_manager()

    class Meta:
        db_table = '"core"."source_types"'


class Text(models.Model):
    pt_br = models.CharField(unique=True)
    en = models.CharField(unique=True, blank=True, null=True)
    es = models.CharField(unique=True, blank=True, null=True)
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