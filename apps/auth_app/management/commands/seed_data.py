import uuid
import sqlite3
import json
import datetime
import random
from django.core.management.base import BaseCommand
from django.conf import settings
from eduaims.supabase_client import supabase


def make_uuid(seed_str):
    """Stable repeatable UUID from a seed string."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed_str))


class Command(BaseCommand):
    help = 'Seeds Supabase (using real existing student IDs) and local SQLite with consistent dummy data.'

    def handle(self, *args, **options):
        db_path = str(settings.BASE_DIR / 'db.sqlite3')
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        self.stdout.write("Fetching existing Supabase students to use their real IDs...")
        # ── Load real student IDs from Supabase ──────────────────────────────
        res = supabase.table('students').select('id,name,class_name,attendance_pct,grade_avg,risk_score').execute()
        sb_students = res.data or []

        if not sb_students:
            self.stdout.write("No students found in Supabase! Inserting seeded students...")
            seed_roster = [
                {"name": "Ahmed Khan",     "class_name": "Class 9-A",  "att": 72,  "grade": 58,  "risk": "red",    "score": 84},
                {"name": "Fatima Malik",   "class_name": "Class 10-B", "att": 85,  "grade": 62,  "risk": "yellow", "score": 68},
                {"name": "Hamza Tariq",    "class_name": "Class 11-A", "att": 78,  "grade": 68,  "risk": "yellow", "score": 78},
                {"name": "Sana Javed",     "class_name": "Class 11-A", "att": 95,  "grade": 90,  "risk": "green",  "score": 10},
                {"name": "Umer Farooq",    "class_name": "Class 10-B", "att": 96,  "grade": 91,  "risk": "green",  "score": 8},
            ]
            for s in seed_roster:
                sid = str(uuid.uuid4())
                row = {
                    "id": sid, "name": s["name"],
                    "class_name": s["class_name"],
                    "registration_no": f"REG-{random.randint(1000,9999)}",
                    "attendance_pct": s["att"], "grade_avg": s["grade"],
                    "risk_score": s["score"], "is_active": True,
                }
                try:
                    supabase.table('students').insert(row).execute()
                    sb_students.append({"id": sid, "name": s["name"], "class_name": s["class_name"],
                                        "attendance_pct": s["att"], "grade_avg": s["grade"], "risk_score": s["score"]})
                    self.stdout.write(f"  + Inserted: {s['name']}")
                except Exception as e:
                    self.stdout.write(f"  ! Insert failed for {s['name']}: {e}")

        self.stdout.write(f"Working with {len(sb_students)} students.")

        # ── Map real Supabase students to local risk config ────────────────────
        risk_config = {}
        for s in sb_students:
            score = s.get('risk_score') or 30
            if score >= 70:
                level = 'red'
            elif score >= 50:
                level = 'yellow'
            else:
                level = 'green'
            att_pct = s.get('attendance_pct') or 85
            grade = s.get('grade_avg') or 75
            risk_config[s['id']] = {
                'level': level, 'score': score,
                'att': att_pct, 'grade': grade,
                'name': s.get('name', ''),
                'class': s.get('class_name', ''),
            }

        # ── Upsert risk_scores using real student IDs ─────────────────────────
        self.stdout.write("Seeding risk_scores...")
        for sid, cfg in risk_config.items():
            rid = make_uuid(f"risk-{sid}")
            if cfg['level'] == 'red':
                reason = f"Low attendance ({cfg['att']}%) and declining grades"
            elif cfg['level'] == 'yellow':
                reason = f"Grade average at {cfg['grade']}% - needs monitoring"
            else:
                reason = "Student performing within expected range"

            sb_row = {
                "id": rid,
                "student_id": sid,
                "score": int(cfg['score']),
                "level": cfg['level'],
                "risk_level": cfg['level'],
                "reason": reason,
                "attendance_pct": float(cfg['att']),
                "grade_avg": float(cfg['grade']),
                "grade_trend": -8.0 if cfg['level'] in ('red', 'yellow') else 3.0,
                "assignments_missed": 2 if cfg['level'] == 'red' else (1 if cfg['level'] == 'yellow' else 0),
                "top_factors": [reason],
                "calculated_at": str(datetime.date.today()),
            }
            try:
                existing = supabase.table('risk_scores').select('id').eq('student_id', sid).execute()
                if not existing.data:
                    supabase.table('risk_scores').insert(sb_row).execute()
                    self.stdout.write(f"  + Risk score for {cfg['name']}")
                else:
                    supabase.table('risk_scores').update(sb_row).eq('student_id', sid).execute()
                    self.stdout.write(f"  ~ Updated risk for {cfg['name']}")
            except Exception as e:
                self.stdout.write(f"  ! risk_score fail ({cfg['name']}): {e}")

            # Also update SQLite
            try:
                cur.execute(
                    "INSERT OR REPLACE INTO risk_scores (id, student_id, score, level, risk_level, reason, attendance_pct, grade_avg, grade_trend, assignments_missed, top_factors, calculated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    [rid, sid, int(cfg['score']), cfg['level'], cfg['level'], reason, float(cfg['att']), float(cfg['grade']),
                     sb_row['grade_trend'], sb_row['assignments_missed'], json.dumps([reason]), sb_row['calculated_at']]
                )
                conn.commit()
            except Exception:
                pass

        self.stdout.write("Risk scores done.")

        # ── Attendance records (last 10 days) — NO subject_id (it expects UUID) ─
        self.stdout.write("Seeding attendance records (last 10 days)...")
        today = datetime.date.today()
        att_inserted = 0
        class_subject_map = {
            'Class 9-A': 'Mathematics', 'Class 9-B': 'Mathematics',
            'Class 10-A': 'Physics',    'Class 10-B': 'Physics',
            'Class 11-A': 'Chemistry',  'Class 11-B': 'Chemistry',
        }
        for i in range(10):
            date_str = str(today - datetime.timedelta(days=i))
            for s in sb_students:
                sid = s['id']
                cfg = risk_config.get(sid, {})
                att_pct = cfg.get('att', 85)
                rand = random.randint(1, 100)
                status = 'present' if rand <= att_pct else ('late' if rand <= att_pct + 5 else 'absent')
                att_id = make_uuid(f"att-{sid}-{date_str}")
                subject = class_subject_map.get(s.get('class_name', ''), 'General Studies')

                # Supabase — omit subject_id (it's a UUID FK we don't have)
                sb_row = {
                    "id": att_id,
                    "student_id": sid,
                    "date": date_str,
                    "status": status,
                    "class_name": s.get('class_name', ''),
                }
                try:
                    existing = supabase.table('attendance').select('id').eq('id', att_id).execute()
                    if not existing.data:
                        supabase.table('attendance').insert(sb_row).execute()
                        att_inserted += 1
                except Exception:
                    pass

                # SQLite
                try:
                    cur.execute(
                        "INSERT OR REPLACE INTO attendance (id, student_id, date, subject_id, status) VALUES (?,?,?,?,?)",
                        [att_id, sid, date_str, subject, status]
                    )
                    conn.commit()
                except Exception:
                    pass

        self.stdout.write(f"Attendance done ({att_inserted} new Supabase rows).")

        # ── Grades (3 exam types per student) — NO subject_id ─────────────────
        self.stdout.write("Seeding grades...")
        exams = [
            {"term": "Monthly Test", "exam_type": "Monthly Test", "weight": 0.8},
            {"term": "Mid-Term",     "exam_type": "Mid-Term",     "weight": 0.95},
            {"term": "Final Exam",   "exam_type": "Final Exam",   "weight": 1.05},
        ]
        grades_inserted = 0
        for s in sb_students:
            sid = s['id']
            cfg = risk_config.get(sid, {})
            grade_base = cfg.get('grade', 75)
            subject = class_subject_map.get(s.get('class_name', ''), 'General Studies')
            for ex in exams:
                score = round(min(100, max(20, grade_base * ex['weight'] + random.randint(-5, 5))))
                gid = make_uuid(f"grd-{sid}-{ex['term']}")

                # Supabase — no subject_id
                sb_row = {
                    "id": gid,
                    "student_id": sid,
                    "subject": subject,
                    "exam_type": ex['exam_type'],
                    "term": ex['term'],
                    "marks": score,
                    "marks_obtained": score,
                    "total_marks": 100,
                    "score": float(score),
                    "total_score": 100.0,
                    "percentage": float(score),
                    "month": "2026-05",
                    "year": "2026",
                    "class_name": s.get('class_name', ''),
                }
                try:
                    existing = supabase.table('grades').select('id').eq('id', gid).execute()
                    if not existing.data:
                        supabase.table('grades').insert(sb_row).execute()
                        grades_inserted += 1
                    else:
                        supabase.table('grades').update(sb_row).eq('id', gid).execute()
                except Exception:
                    pass

                # SQLite
                try:
                    cur.execute(
                        "INSERT OR REPLACE INTO grades (id, student_id, subject_id, subject, term, score, total_score, percentage, month, class_name) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        [gid, sid, subject, subject, ex['term'], score, 100, score, "2026-05", s.get('class_name', '')]
                    )
                    conn.commit()
                except Exception:
                    pass

        self.stdout.write(f"Grades done ({grades_inserted} new Supabase rows).")

        # ── Interventions using real student IDs ──────────────────────────────
        self.stdout.write("Seeding interventions...")
        # Pick students who are red/yellow risk
        at_risk = [s for s in sb_students if risk_config.get(s['id'], {}).get('level') in ('red', 'yellow')]
        if not at_risk:
            at_risk = sb_students[:3]

        actions = [
            ("Parent Call",  "Called parent to discuss attendance and performance concerns.", "resolved"),
            ("Counseling",   "One-on-one counseling session; assigned peer tutor.", "pending"),
            ("Email Alert",  "Sent email alert to parent regarding grade decline.", "resolved"),
        ]
        for i, s in enumerate(at_risk[:5]):
            sid = s['id']
            action_type, notes, outcome = actions[i % len(actions)]
            iid = make_uuid(f"int-{sid}-{i}")
            date_str = str(today - datetime.timedelta(days=i*3 + 5))

            sb_row = {
                "id": iid, "student_id": sid,
                "action_type": action_type,
                "notes": notes, "outcome": outcome, "date": date_str,
                "student_name": s.get('name', ''),
            }
            try:
                existing = supabase.table('interventions').select('id').eq('id', iid).execute()
                if not existing.data:
                    supabase.table('interventions').insert(sb_row).execute()
                    self.stdout.write(f"  + Intervention for {s.get('name', '')}")
                else:
                    supabase.table('interventions').update(sb_row).eq('id', iid).execute()
            except Exception as e:
                self.stdout.write(f"  ! intervention fail ({s.get('name', '')}): {e}")

            try:
                cur.execute(
                    "INSERT OR REPLACE INTO interventions (id, student_id, student_name, action_type, notes, outcome, date) VALUES (?,?,?,?,?,?,?)",
                    [iid, sid, s.get('name', ''), action_type, notes, outcome, date_str]
                )
                conn.commit()
            except Exception:
                pass

        self.stdout.write("Interventions done.")
        conn.close()
        self.stdout.write(self.style.SUCCESS("[OK] Seeding complete! SQLite and Supabase are synced."))
