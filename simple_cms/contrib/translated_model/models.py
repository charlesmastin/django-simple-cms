from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from positions.fields import PositionField
from simple_cms.models import CommonAbstractModel

class Language(CommonAbstractModel):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=10, unique=True)
    display_name = models.CharField(max_length=255, blank=True, default='')
    order = PositionField()
    
    class Meta:
        ordering = ['order']
    
    @property
    def title(self):
        if self.display_name:
            return self.display_name
        return self.name

    def __unicode__(self):
        return self.name

class Translation(CommonAbstractModel):
    language = models.ForeignKey(Language)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        abstract = True

class Localization(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.CharField(max_length=255, default='', blank=True)
    
    class Meta:
        ordering = ['name']
    
    def __unicode__(self):
        return self.name

class LocalizationTranslation(models.Model):
    language = models.ForeignKey(Language)
    localization = models.ForeignKey(Localization)
    text = models.TextField()
    
    class Meta:
        unique_together = ('language', 'localization')
    
    def __unicode__(self):
        return self.text
