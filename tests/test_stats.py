import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parents[1] / 'src/core/stats_manager.py'
spec = importlib.util.spec_from_file_location('tracker_stats', source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StatsTests(unittest.TestCase):
    def test_saved_tickets_reload_and_old_timestamps_migrate(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'stats.json'
            file.write_text(json.dumps({'tickets': ['2026-10-07T12:00:00']}))
            manager = module.StatsManager(file)
            self.assertTrue(manager.data['tickets'][0]['has_reply'])
            manager.log_ticket()
            self.assertEqual(len(module.StatsManager(file).data['tickets']), 2)

    def test_corrupt_file_is_preserved_before_a_new_save(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'stats.json'
            file.write_text('incomplete original data')
            manager = module.StatsManager(file)
            manager.log_ticket()
            backups = list(Path(folder).glob('stats.json.corrupt-*'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), 'incomplete original data')
            self.assertEqual(len(json.loads(file.read_text())['tickets']), 1)

    def test_failed_replacement_keeps_old_data_and_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / 'stats.json'
            original = '{"tickets": [], "activity": {}}'
            file.write_text(original)
            manager = module.StatsManager(file)
            with patch.object(module.os, 'replace', side_effect=OSError('test replacement failure')):
                with self.assertRaises(OSError):
                    manager.log_ticket()
            self.assertEqual(file.read_text(), original)
            self.assertFalse(list(Path(folder).glob('*.tmp')))


if __name__ == '__main__':
    unittest.main()
