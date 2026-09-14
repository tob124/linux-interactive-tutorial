"""Check curriculum wiring and execute portable reference solutions in a temp project.

This does not replace Docker, SSH, GDB or OpenModelica end-to-end acceptance.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from lab.seed import seed

ROOT = Path(__file__).resolve().parents[1]
COURSE = json.loads((ROOT / 'course/curriculum.json').read_text())
SOFTWARE = json.loads((ROOT / 'course/software.json').read_text())


class CourseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.work = Path(self.temp.name)
        seed(self.work, 1)
        self.env = {**os.environ, 'COURSE_WORKSPACE': str(self.work),
                    'PYTHONPATH': os.pathsep.join([str(ROOT / 'server'), str(ROOT / 'lab')])}

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *args):
        return subprocess.run(args, cwd=self.work, env=self.env, capture_output=True, text=True, timeout=30)

    def check(self, identifier):
        result = self.command(sys.executable, str(ROOT / 'lab/checks.py'), identifier)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def reference(self, identifier):
        lesson = next(l for l in COURSE['lessons'] if l['id'] == identifier)
        result = self.command('bash', '-c', lesson['tasks'][0]['solution'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.check(identifier)['status'], 'passed')

    def test_course_links_and_assessments(self):
        expected = {f'w{w}-{n}' for w in range(1, 7) for n in range(1, 5)}
        self.assertEqual({l['id'] for l in COURSE['lessons']}, expected)
        self.assertEqual(COURSE['authors'], ['Connor He', 'Astra'])
        ids = {s['id'] for s in SOFTWARE}
        for lesson in COURSE['lessons']:
            self.assertTrue(set(lesson['softwareIds']) <= ids)
            self.assertEqual(lesson['tasks'][0]['check'], lesson['id'])
            self.assertEqual(len(lesson['quiz']), 2)
            for q in lesson['quiz']:
                self.assertEqual(len(set(q['options'])), 4)
                self.assertTrue(0 <= q['answer'] < 4)
        for track in COURSE['tracks']:
            self.assertTrue(set(track['softwareIds']) <= ids)

    def test_all_lesson_commands_parse_as_bash(self):
        for lesson in COURSE['lessons']:
            for command in [c['command'] for c in lesson['commands']] + [lesson['tasks'][0]['solution']]:
                with self.subTest(lesson=lesson['id']):
                    result = self.command('bash', '-n', '-c', command)
                    self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which('g++'), 'C++ compiler unavailable')
    def test_cpp_defect_and_corrected_units(self):
        # Compiler-only verification; container CMake/GDB still need acceptance.
        work = self.work / 'cpp'
        seed(work, 5)
        sensor = work / 'sensor'
        executable = sensor / 'test_units'
        def compile_test():
            result = self.command('g++', '-std=c++17', '-I', str(sensor / 'include'),
                                  str(sensor / 'tests/test_units.cpp'), '-o', str(executable))
            self.assertEqual(result.returncode, 0, result.stderr)
        compile_test()
        result = self.command(str(executable))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('actual=600', result.stderr)
        header = sensor / 'include/units.hpp'
        header.write_text(header.read_text().replace('x * 60.0', 'x * 60.0 / (2 * 3.141592653589793)'))
        compile_test()
        self.assertEqual(self.command(str(executable)).returncode, 0)

    def test_file_and_data_reference_solutions(self):
        for identifier in ('w1-1', 'w1-2', 'w1-3', 'w2-1', 'w2-2', 'w2-3', 'w2-4'):
            with self.subTest(lesson=identifier):
                self.reference(identifier)

    def test_checker_rejects_modified_original_and_wrong_filtered_values(self):
        self.reference('w2-2')
        output = self.work / 'results/high-current.csv'
        output.write_text(output.read_text().replace('4.0', '400'))
        self.assertEqual(self.check('w2-2')['status'], 'failed')
        self.reference('w1-2')
        (self.work / 'experiments/motor-01/raw/motor.csv').write_text('modified')
        self.assertEqual(self.check('w1-2')['status'], 'failed')

    def test_real_motor_cli_and_physical_checks(self):
        for args, identifier in [(['simulate'], 'w3-2'), (['batch'], 'w3-3'), (['closed-loop'], 'w6-3')]:
            result = self.command(sys.executable, str(ROOT / 'lab/labtool.py'), *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.check(identifier)['status'], 'passed')
        path = self.work / 'results/closedloop.csv'
        path.write_text(path.read_text().replace('900', 'nan'))
        self.assertEqual(self.check('w6-3')['status'], 'failed')

    def test_finite_bad_crosscheck_returns_single_json_failure(self):
        result = self.command(sys.executable, str(ROOT / 'lab/labtool.py'), 'simulate')
        self.assertEqual(result.returncode, 0, result.stderr)
        # Deliberately synthetic, wrong comparison fixture. It must never pass.
        (self.work / 'results/modelica.csv').write_text('time_s,speed_rpm,current_A\n' + '\n'.join(f'{i/2},0,0' for i in range(11)))
        (self.work / 'results/modelica-version.json').write_text('{"fixture": "deliberately incorrect, not an omc run"}')
        self.assertEqual(self.check('w6-2')['status'], 'failed')

    def test_report_requires_student_attribution(self):
        for args in (['diagnose'], ['report']):
            result = self.command(sys.executable, str(ROOT / 'lab/labtool.py'), *args)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.check('w6-4')['status'], 'failed')
        path = self.work / 'reports/report.md'
        path.write_text(path.read_text().replace('学生作者：待填写', '学生作者：Test Student'))
        result = self.command(sys.executable, str(ROOT / 'lab/labtool.py'), 'report', '--archive-only')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.check('w6-4')['status'], 'passed')

    def test_missing_artifacts_and_bad_ids_cannot_pass(self):
        self.assertNotEqual(self.check('w1-1')['status'], 'passed')
        self.assertEqual(self.check('w99-1')['status'], 'failed')
