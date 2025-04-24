import os
from django.test import TestCase

class CustomerCleanupTests(TestCase):
    def test_cleanup_script_exists_and_is_executable(self):
        """Test that the cleanup script exists and is executable"""
        script_path = os.path.join('crm', 'cron_jobs', 'clean_inactive_customers.sh')
        self.assertTrue(os.path.exists(script_path), "Cleanup script does not exist")
        self.assertTrue(os.access(script_path, os.X_OK), "Cleanup script is not executable")

    def test_crontab_entry_is_correct(self):
        """Test that the crontab entry is correctly formatted"""
        crontab_path = os.path.join('crm', 'cron_jobs', 'customer_cleanup_crontab.txt')
        self.assertTrue(os.path.exists(crontab_path), "Crontab file does not exist")
        
        with open(crontab_path, 'r') as f:
            crontab_entry = f.read().strip()
        
        parts = crontab_entry.split()
        self.assertEqual(len(parts), 6, "Crontab entry does not have correct number of fields")
        self.assertEqual(parts[0], "0", "Minute should be 0")
        self.assertEqual(parts[1], "2", "Hour should be 2")
        self.assertEqual(parts[2], "*", "Day of month should be *")
        self.assertEqual(parts[3], "*", "Month should be *")
        self.assertEqual(parts[4], "0", "Day of week should be 0 (Sunday)")
        
        script_path = parts[5]
        self.assertTrue(script_path.endswith('clean_inactive_customers.sh'), 
                       "Script path should end with clean_inactive_customers.sh") 