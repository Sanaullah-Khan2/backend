# Schedule on Railway:  0 2 * * * python manage.py run_daily_scoring
# Windows Task Scheduler: run daily at 2:00 AM

from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
import os
from pathlib import Path

# Load .env explicitly so env vars are available in the management command
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parents[4] / '.env'
    load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass  # dotenv not installed; rely on system env vars

from supabase import create_client

def get_sb():
    from supabase import create_client as _create
    url = os.environ.get('SUPABASE_URL', '')
    key = os.environ.get('SUPABASE_SERVICE_KEY', '').strip()
    if not url or not key:
        raise Exception("Supabase credentials not found in environment variables.")
    return _create(url, key)

class Command(BaseCommand):
    help = 'Run daily AI risk scoring for all active students'

    def handle(self, *args, **kwargs):
        self.stdout.write('=' * 50)
        self.stdout.write('EduAIMS Daily AI Scoring Started')
        self.stdout.write(f'Time: {datetime.utcnow()}')
        self.stdout.write('=' * 50)

        sb         = get_sb()
        today      = datetime.utcnow().strftime('%Y-%m-%d')
        this_month = datetime.utcnow().strftime('%Y-%m')
        last_month = (datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m')

        # Fetch all active students
        students = sb.table('students')\
            .select('id, full_name, class_name')\
            .eq('is_active', True)\
            .execute().data

        total   = len(students)
        success = 0
        errors  = 0

        self.stdout.write(f'Found {total} active students')
        self.stdout.write('-' * 50)

        for student in students:
            sid  = student['id']
            name = student['full_name']

            try:
                # Step 1: Calculate attendance %
                att = sb.table('attendance')\
                    .select('status')\
                    .eq('student_id', sid)\
                    .gte('date', this_month + '-01')\
                    .execute().data

                total_days = len(att)
                present    = sum(1 for a in att if a['status'] == 'present')
                att_pct    = (present / total_days * 100) if total_days > 0 else 100

                # Step 2: Calculate grade average this month
                g_now = sb.table('grades')\
                    .select('percentage')\
                    .eq('student_id', sid)\
                    .eq('month', this_month)\
                    .execute().data

                avg_now = sum(g['percentage'] for g in g_now) / len(g_now) \
                          if g_now else 100

                # Step 3: Calculate grade average last month
                g_last = sb.table('grades')\
                    .select('percentage')\
                    .eq('student_id', sid)\
                    .eq('month', last_month)\
                    .execute().data

                avg_last = sum(g['percentage'] for g in g_last) / len(g_last) \
                           if g_last else avg_now

                # Step 4: Grade trend
                grade_trend = avg_now - avg_last

                # Step 5: Calculate risk score
                score = 0
                if att_pct    < 75:  score += 40
                if avg_now    < 50:  score += 35
                if grade_trend < -15: score += 25
                score = min(score, 100)

                # Step 6: Determine level
                if score >= 70:
                    level = 'red'
                elif score >= 40:
                    level = 'yellow'
                else:
                    level = 'green'

                # Step 7: Generate reason
                if att_pct < 75 and avg_now < 50:
                    reason = f'Low attendance ({att_pct:.0f}%) and failing grades ({avg_now:.0f}%)'
                elif att_pct < 75:
                    reason = f'Low attendance ({att_pct:.0f}%)'
                elif avg_now < 50:
                    reason = f'Low grade average ({avg_now:.0f}%)'
                elif grade_trend < -15:
                    reason = f'Grade dropped {abs(grade_trend):.0f}% from last month'
                else:
                    reason = 'Student performing well'

                # Step 8: Save to Supabase
                sb.table('risk_scores').insert({
                    'student_id':     sid,
                    'score':          round(score, 2),
                    'level':          level,
                    'reason':         reason,
                    'attendance_pct': round(att_pct, 2),
                    'grade_avg':      round(avg_now, 2),
                    'grade_trend':    round(grade_trend, 2),
                    'calculated_at':  today,
                }).execute()

                success += 1
                self.stdout.write(
                    f'  [{level.upper():6}] {name:30} score={score:3} att={att_pct:.0f}% grade={avg_now:.0f}%'
                )

            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  [ERROR] {name}: {str(e)}')
                )

        # Final summary
        self.stdout.write('=' * 50)
        self.stdout.write(
            self.style.SUCCESS(f'Done! Success: {success} | Errors: {errors} | Total: {total}')
        )
        self.stdout.write('=' * 50)
