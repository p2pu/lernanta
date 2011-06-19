# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Page.language'
        db.add_column('pages_page', 'language', self.gf('django.db.models.fields.CharField')(default='es', max_length=16), keep_default=False)

        # Adding field 'Page.updated'
        db.add_column('pages_page', 'updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, default=datetime.date(2011, 6, 2), blank=True), keep_default=False)

        # Adding field 'Page.original'
        db.add_column('pages_page', 'original', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pages.Page'], null=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Page.language'
        db.delete_column('pages_page', 'language')

        # Deleting field 'Page.updated'
        db.delete_column('pages_page', 'updated')

        # Deleting field 'Page.original'
        db.delete_column('pages_page', 'original_id')


    models = {
        'pages.page': {
            'Meta': {'object_name': 'Page'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'es'", 'max_length': '16'}),
            'original': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pages.Page']", 'null': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '110', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pages']
