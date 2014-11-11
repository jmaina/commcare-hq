# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'SyncLog.user_id'
        db.alter_column(u'sofabed_synclog', 'user_id', self.gf('django.db.models.fields.CharField')(max_length=64, null=True))

        # Changing field 'SyncLog.dependent_cases_on_phone'
        db.alter_column(u'sofabed_synclog', 'dependent_cases_on_phone', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'SyncLog.date'
        db.alter_column(u'sofabed_synclog', 'date', self.gf('django.db.models.fields.DateTimeField')(null=True))

        # Changing field 'SyncLog.previous_log_id'
        db.alter_column(u'sofabed_synclog', 'previous_log_id', self.gf('django.db.models.fields.CharField')(max_length=64, null=True))

        # Changing field 'SyncLog.last_seq'
        db.alter_column(u'sofabed_synclog', 'last_seq', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True))

        # Changing field 'SyncLog.owner_ids_on_phone'
        db.alter_column(u'sofabed_synclog', 'owner_ids_on_phone', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'SyncLog.duration'
        db.alter_column(u'sofabed_synclog', 'duration', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'SyncLog.cases_on_phone'
        db.alter_column(u'sofabed_synclog', 'cases_on_phone', self.gf('django.db.models.fields.IntegerField')(null=True))


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'SyncLog.user_id'
        raise RuntimeError("Cannot reverse this migration. 'SyncLog.user_id' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'SyncLog.dependent_cases_on_phone'
        raise RuntimeError("Cannot reverse this migration. 'SyncLog.dependent_cases_on_phone' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'SyncLog.date'
        raise RuntimeError("Cannot reverse this migration. 'SyncLog.date' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'SyncLog.previous_log_id'
        raise RuntimeError("Cannot reverse this migration. 'SyncLog.previous_log_id' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'SyncLog.last_seq'
        raise RuntimeError("Cannot reverse this migration. 'SyncLog.last_seq' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'SyncLog.owner_ids_on_phone'
        raise RuntimeError("Cannot reverse this migration. 'SyncLog.owner_ids_on_phone' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'SyncLog.duration'
        raise RuntimeError("Cannot reverse this migration. 'SyncLog.duration' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'SyncLog.cases_on_phone'
        raise RuntimeError("Cannot reverse this migration. 'SyncLog.cases_on_phone' and its values cannot be restored.")


    models = {
        u'sofabed.caseactiondata': {
            'Meta': {'unique_together': "(('case', 'index'),)", 'object_name': 'CaseActionData'},
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'case': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'actions'", 'to': u"orm['sofabed.CaseData']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'index': ('django.db.models.fields.IntegerField', [], {}),
            'server_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'sync_log_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'db_index': 'True'}),
            'xform_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'xform_xmlns': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'})
        },
        u'sofabed.casedata': {
            'Meta': {'object_name': 'CaseData'},
            'case_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128', 'primary_key': 'True'}),
            'closed': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'closed_by': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'db_index': 'True'}),
            'closed_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'doc_type': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'external_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True'}),
            'modified_by': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'db_index': 'True'}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True'}),
            'opened_by': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'db_index': 'True'}),
            'opened_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'owner_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'db_index': 'True'}),
            'server_modified_on': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'db_index': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'db_index': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'db_index': 'True'})
        },
        u'sofabed.caseindexdata': {
            'Meta': {'object_name': 'CaseIndexData'},
            'case': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'indices'", 'to': u"orm['sofabed.CaseData']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'referenced_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'referenced_type': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'})
        },
        u'sofabed.formdata': {
            'Meta': {'object_name': 'FormData'},
            'app_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'}),
            'device_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'doc_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'duration': ('django.db.models.fields.BigIntegerField', [], {}),
            'instance_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'primary_key': 'True'}),
            'received_on': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'time_end': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'time_start': ('django.db.models.fields.DateTimeField', [], {}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'xmlns': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'db_index': 'True'})
        },
        u'sofabed.synclog': {
            'Meta': {'object_name': 'SyncLog'},
            'cases_on_phone': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'dependent_cases_on_phone': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'primary_key': 'True'}),
            'last_seq': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True'}),
            'owner_ids_on_phone': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'previous_log_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'})
        }
    }

    complete_apps = ['sofabed']
