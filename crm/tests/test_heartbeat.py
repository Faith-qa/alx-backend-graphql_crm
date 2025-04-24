import os
import subprocess
import time
from datetime import datetime
from django.test import TestCase
from unittest.mock import patch, mock_open, MagicMock
from crm.cron import log_crm_heartbeat
from django.core.management import call_command

class HeartbeatTests(TestCase):
    @patch('gql.Client.execute')
    def test_heartbeat_logging_with_graphql_success(self, mock_execute):
        """Test heartbeat logging when GraphQL endpoint is responsive"""
        # Mock successful GraphQL response
        mock_execute.return_value = {'hello': 'world'}
        
        # Mock file operations
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            # Execute heartbeat function
            log_crm_heartbeat()
            
            # Verify file was opened for appending
            mock_file.assert_called_with('/tmp/crm_heartbeat_log.txt', 'a')
            
            # Get the written content
            handle = mock_file()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            
            # Verify timestamp format and message
            self.assertRegex(
                written_content,
                r'\d{2}/\d{2}/\d{4}-\d{2}:\d{2}:\d{2} CRM is alive \(GraphQL endpoint responsive\)\n',
                "Log message should contain timestamp and GraphQL success indication"
            )
    
    @patch('gql.Client.execute')
    def test_heartbeat_logging_with_graphql_failure(self, mock_execute):
        """Test heartbeat logging when GraphQL endpoint is not responsive"""
        # Mock GraphQL failure
        mock_execute.side_effect = Exception("Connection failed")
        
        # Mock file operations
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            # Execute heartbeat function
            log_crm_heartbeat()
            
            # Verify file was opened for appending
            mock_file.assert_called_with('/tmp/crm_heartbeat_log.txt', 'a')
            
            # Get the written content
            handle = mock_file()
            written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
            
            # Verify timestamp format and message
            self.assertRegex(
                written_content,
                r'\d{2}/\d{2}/\d{4}-\d{2}:\d{2}:\d{2} CRM is alive \(GraphQL check failed: Connection failed\)\n',
                "Log message should contain timestamp and GraphQL failure indication"
            )
    
    def test_cronjob_configuration(self):
        """Test that the cronjob is properly configured in settings"""
        from django.conf import settings
        
        # Verify django_crontab is in INSTALLED_APPS
        self.assertIn('django_crontab', settings.INSTALLED_APPS,
                     "django_crontab should be in INSTALLED_APPS")
        
        # Verify CRONJOBS setting exists and contains our job
        self.assertTrue(hasattr(settings, 'CRONJOBS'),
                       "CRONJOBS setting should be defined")
        
        # Find our heartbeat job
        heartbeat_jobs = [job for job in settings.CRONJOBS 
                         if job[1] == 'crm.cron.log_crm_heartbeat']
        
        self.assertEqual(len(heartbeat_jobs), 1,
                        "Should find exactly one heartbeat job configuration")
        
        job = heartbeat_jobs[0]
        self.assertEqual(job[0], '*/5 * * * *',
                        "Heartbeat job should run every 5 minutes")

    def test_crontab_add_and_log_creation(self):
        """Test that crontab can be added and creates log entries"""
        log_file = '/tmp/crm_heartbeat_log.txt'
        
        # Remove existing log file if it exists
        if os.path.exists(log_file):
            os.remove(log_file)
        
        try:
            # Add the crontab entry
            call_command('crontab', 'add')
            
            # Run the heartbeat function directly to simulate cron execution
            log_crm_heartbeat()
            
            # Verify log file was created
            self.assertTrue(os.path.exists(log_file),
                          "Log file should be created")
            
            # Read the log file content
            with open(log_file, 'r') as f:
                content = f.read()
            
            # Verify log content
            self.assertRegex(
                content,
                r'\d{2}/\d{2}/\d{4}-\d{2}:\d{2}:\d{2} CRM is alive',
                "Log file should contain heartbeat message with timestamp"
            )
            
        finally:
            # Clean up - remove crontab entry
            call_command('crontab', 'remove')
            
            # Clean up - remove log file
            if os.path.exists(log_file):
                os.remove(log_file) 