# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Localization'
        db.create_table('translated_model_localization', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('description', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
        ))
        db.send_create_signal('translated_model', ['Localization'])

        # Adding model 'LocalizationTranslation'
        db.create_table('translated_model_localizationtranslation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translated_model.Language'])),
            ('localization', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['translated_model.Localization'])),
            ('text', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('translated_model', ['LocalizationTranslation'])

        # Adding unique constraint on 'LocalizationTranslation', fields ['language', 'localization']
        db.create_unique('translated_model_localizationtranslation', ['language_id', 'localization_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'LocalizationTranslation', fields ['language', 'localization']
        db.delete_unique('translated_model_localizationtranslation', ['language_id', 'localization_id'])

        # Deleting model 'Localization'
        db.delete_table('translated_model_localization')

        # Deleting model 'LocalizationTranslation'
        db.delete_table('translated_model_localizationtranslation')


    models = {
        'translated_model.language': {
            'Meta': {'ordering': "['order']", 'object_name': 'Language'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '10'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'})
        },
        'translated_model.localization': {
            'Meta': {'ordering': "['name']", 'object_name': 'Localization'},
            'description': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'translated_model.localizationtranslation': {
            'Meta': {'unique_together': "(('language', 'localization'),)", 'object_name': 'LocalizationTranslation'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['translated_model.Language']"}),
            'localization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['translated_model.Localization']"}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['translated_model']
