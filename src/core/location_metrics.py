# src/core/location_metrics.py

import pandas as pd

def calculate_location_metrics(df):
    """
    Calculate location breakdown metrics (CORD vs ZOOM).
    
    Returns dict with:
    - breakdown: counts and percentages for each location
    - totals: overall summary
    """
    metrics = {}
    
    if 'Location' not in df.columns:
        return metrics
    
    total_sessions = len(df)
    location_counts = df['Location'].value_counts()
    location_pcts = (location_counts / total_sessions * 100).round(1)
    
    metrics['breakdown'] = {
        'counts': location_counts.to_dict(),
        'percentages': location_pcts.to_dict()
    }
    
    metrics['totals'] = {
        'total_sessions': total_sessions,
        'cord_count': location_counts.get('CORD', 0),
        'cord_pct': round(location_counts.get('CORD', 0) / total_sessions * 100, 1) if total_sessions > 0 else 0,
        'zoom_count': location_counts.get('ZOOM', 0),
        'zoom_pct': round(location_counts.get('ZOOM', 0) / total_sessions * 100, 1) if total_sessions > 0 else 0
    }
    
    return metrics
