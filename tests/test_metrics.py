import pandas as pd

from src.core.metrics import calculate_all_metrics


def test_calculate_all_metrics_returns_expected_top_level_keys():
    df = pd.DataFrame(
        {
            'Booking_Lead_Time_Days': [0.5, 2.0, 5.0],
            'Appointment_DateTime': pd.to_datetime(['2026-01-05 10:00', '2026-01-06 11:00', '2026-01-07 12:00']),
            'Attendance_Status': ['Present', 'Absent', 'Present'],
            'Status': ['Completed', 'Completed', 'Cancelled'],
            'Actual_Session_Length': [0.7, 0.6, 0.8],
            'Tutor_Anon_ID': ['TUT_0001', 'TUT_0002', 'TUT_0001'],
            'Student_Anon_ID': ['STU_0001', 'STU_0002', 'STU_0001'],
            'Semester_Label': ['Spring 2026', 'Spring 2026', 'Spring 2026'],
            'Location': ['CORD', 'ZOOM', 'CORD'],
        }
    )

    metrics = calculate_all_metrics(df)

    expected = {
        'booking', 'time_patterns', 'attendance', 'session_length', 'satisfaction',
        'tutors', 'students', 'semesters', 'incentives', 'location',
        'hourly_location', 'daily_patterns', 'monthly_patterns', 'semester_trends'
    }
    assert expected.issubset(set(metrics.keys()))
    assert metrics['attendance']['overall']['total_sessions'] == 3
