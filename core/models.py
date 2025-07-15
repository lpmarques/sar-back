from authemail.models import EmailUserManager, EmailAbstractUser
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Now
from django.contrib.postgres.fields import ArrayField


class ContentEndorsement(models.Model):
    plant_data_id = models.IntegerField(blank=True, null=True)
    plant_popular_name_id = models.IntegerField(blank=True, null=True)
    plant_scientific_name_id = models.IntegerField(blank=True, null=True)
    content_type = models.CharField(db_comment='[plant_data, plant_popular_name, plant_scientific_name]')
    endorser = models.ForeignKey('User', models.DO_NOTHING)
    created_at = models.DateTimeField(db_default=Now())
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"core"."content_endorsements"'
        unique_together = (('plant_data_id', 'plant_popular_name_id', 'plant_scientific_name_id', 'endorser'),)


class Source(models.Model):
    name = models.CharField(unique=True, blank=True, null=True)
    type = models.CharField()
    year = models.IntegerField(blank=True, null=True)
    publication_title = models.CharField()
    publication_authors = ArrayField(
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
        managed = False
        db_table = '"core"."sources"'


class Text(models.Model):
    pt_br = models.CharField()
    en = models.CharField(blank=True, null=True)
    es = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(db_default=Now())
    updated_at = models.DateTimeField(db_default=Now())

    class Meta:
        managed = False
        db_table = '"core"."texts"'


class User(EmailAbstractUser):
    first_name = models.CharField()
    last_name = models.CharField()
    email = models.CharField(unique=True)
    password = models.CharField()
    role = models.CharField(blank=True, null=True, db_default="regular")
    occupation = models.CharField()
    company = models.CharField(blank=True, null=True)
    country = models.ForeignKey('geography.Country', on_delete=models.DO_NOTHING, blank=True, null=True)
    state = models.ForeignKey('geography.State', on_delete=models.DO_NOTHING, blank=True, null=True)
    municipality = models.ForeignKey('geography.Municipality', on_delete=models.DO_NOTHING, blank=True, null=True)
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

    class Meta:
        managed = False
        db_table = '"core"."users"'

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
