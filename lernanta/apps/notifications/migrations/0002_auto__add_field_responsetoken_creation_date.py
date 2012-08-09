# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'ResponseToken.creation_date'
        db.add_column('notifications_responsetoken', 'creation_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, auto_now_add=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'ResponseToken.creation_date'
        db.delete_column('notifications_responsetoken', 'creation_date')


    models = {
        'notifications.responsetoken': {
            'Meta': {'object_name': 'ResponseToken'},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_callback': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'response_token': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['notifications']
