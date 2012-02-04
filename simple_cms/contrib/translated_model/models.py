from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models

from positions.fields import PositionField
from simple_cms.models import CommonAbstractModel

class Language(CommonAbstractModel):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=10, unique=True)
    order = PositionField()
    
    class Meta:
        ordering = ['order']
    
    def __unicode__(self):
        return self.name

class Translation(CommonAbstractModel):
    language = models.ForeignKey(Language)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    
    class Meta:
        abstract = True
