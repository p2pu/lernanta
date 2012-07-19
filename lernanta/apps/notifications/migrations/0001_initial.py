# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ResponseToken'
        db.create_table('notifications_responsetoken', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('response_token', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('response_callback', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('notifications', ['ResponseToken'])


    def backwards(self, orm):
        
        # Deleting model 'ResponseToken'
        db.delete_table('notifications_responsetoken')


    models = {
        'notifications.responsetoken': {
            'Meta': {'object_name': 'ResponseToken'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'response_callback': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'response_token': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        }
    }

    complete_apps = ['notifications']
