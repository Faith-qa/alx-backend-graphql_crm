import os
import sys
import tempfile
from django.test import TestCase
from unittest.mock import patch, MagicMock, mock_open
import datetime

# Add the cron_jobs directory to the Python path so we can import the script
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cron_jobs'))
import send_order_reminders

class OrderRemindersTests(TestCase):
    def test_reminder_script_exists_and_is_executable(self):
        """Test that the reminder script exists and is executable"""
        script_path = os.path.join('crm', 'cron_jobs', 'send_order_reminders.py')
        self.assertTrue(os.path.exists(script_path), "Reminder script does not exist")
        self.assertTrue(os.access(script_path, os.X_OK), "Reminder script is not executable")

    def test_crontab_entry_is_correct(self):
        """Test that the crontab entry is correctly formatted"""
        crontab_path = os.path.join('crm', 'cron_jobs', 'order_reminders_crontab.txt')
        self.assertTrue(os.path.exists(crontab_path), "Crontab file does not exist")
        
        with open(crontab_path, 'r') as f:
            crontab_entry = f.read().strip()
        
        parts = crontab_entry.split()
        self.assertEqual(len(parts), 7, "Crontab entry should have 7 fields (including Python interpreter)")
        self.assertEqual(parts[0], "0", "Minute should be 0")
        self.assertEqual(parts[1], "8", "Hour should be 8")
        self.assertEqual(parts[2], "*", "Day of month should be *")
        self.assertEqual(parts[3], "*", "Month should be *")
        self.assertEqual(parts[4], "*", "Day of week should be *")
        self.assertEqual(parts[5], "/usr/bin/python3", "Python interpreter should be /usr/bin/python3")
        
        script_path = parts[6]
        self.assertTrue(script_path.endswith('send_order_reminders.py'), 
                       "Script path should end with send_order_reminders.py")

    @patch('gql.Client.execute')
    def test_script_queries_graphql_and_logs(self, mock_execute):
        """Test that the script queries GraphQL and logs to the specified file"""
        # Mock the GraphQL response
        mock_execute.return_value = {
            'orders': {
                'edges': [
                    {
                        'node': {
                            'id': '1',
                            'orderDate': '2023-01-01T00:00:00Z',
                            'customer': {
                                'email': 'test@example.com'
                            }
                        }
                    }
                ]
            }
        }
        
        # Mock the file operations
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            # Call the process_orders function directly
            success = send_order_reminders.process_orders('/tmp/test_log.txt')
            
            # Verify success
            self.assertTrue(success, "Process orders should return True on success")
            
            # Verify that the GraphQL client was called
            mock_execute.assert_called_once()
            
            # Verify that the log file was written to
            mock_file.assert_called_with('/tmp/test_log.txt', 'a')
            
            # Verify the content written to the log file
            handle = mock_file()
            self.assertTrue(any('Order 1 - Customer: test@example.com' in call[0][0] 
                              for call in handle.write.call_args_list),
                          "Log file should contain order and customer information") 