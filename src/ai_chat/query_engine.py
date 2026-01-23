"""
DuckDB Query Engine for AI Chat.

Provides fast, flexible querying capabilities for ad-hoc data questions.
DuckDB can query pandas DataFrames directly in-memory for optimal performance.
"""

import duckdb
import pandas as pd
from typing import Dict, Any, Optional, List
import re


class QueryEngine:
    """
    Execute safe, parameterized SQL queries on session data using DuckDB.
    
    DuckDB is chosen over SQLite because:
    - 10-100x faster for analytics queries (GROUP BY, COUNT, SUM)
    - Can query pandas DataFrames directly (no need to load into tables)
    - Column-oriented storage optimized for aggregations
    - Nearly identical SQL syntax to SQLite
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize query engine with DataFrame.
        
        Args:
            df: Cleaned pandas DataFrame with session data
        """
        self.df = df
        self.registered = False
        
        # Register DataFrame with DuckDB
        try:
            duckdb.register('df', df)
            self.registered = True
        except Exception as e:
            print(f"Warning: Could not register DataFrame with DuckDB: {e}")
    
    def execute_query(self, query_template: str, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Execute a parameterized SQL query.
        
        Args:
            query_template: SQL query template with {param} placeholders
            params: Dictionary of parameters to fill in
            
        Returns:
            DataFrame with query results
        """
        if not self.registered:
            raise RuntimeError("DataFrame not registered with DuckDB")
        
        # Fill in parameters (simple string substitution for templates)
        query = query_template.format(**params)
        
        try:
            result = duckdb.query(query).df()
            return result
        except Exception as e:
            raise RuntimeError(f"Query execution failed: {e}\nQuery: {query}")
    
    def sessions_by_date(self, 
                        semester: Optional[str] = None,
                        location: Optional[str] = None,
                        limit: int = 10,
                        ascending: bool = False) -> pd.DataFrame:
        """
        Get session counts by date, with optional filtering.
        
        Args:
            semester: Filter by semester label (e.g., "Spring 2024")
            location: Filter by location (e.g., "CORD", "ZOOM")
            limit: Number of results to return
            ascending: Sort order (False = most sessions first)
            
        Returns:
            DataFrame with date and session_count columns
        """
        where_clauses = []
        if semester:
            where_clauses.append(f"Semester_Label = '{semester}'")
        if location:
            where_clauses.append(f"Location = '{location}'")
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        order = "ASC" if ascending else "DESC"
        
        query = f"""
            SELECT 
                DATE(Appointment_DateTime) as date,
                COUNT(*) as session_count
            FROM df
            {where_clause}
            GROUP BY DATE(Appointment_DateTime)
            ORDER BY session_count {order}
            LIMIT {limit}
        """
        
        return duckdb.query(query).df()
    
    def sessions_on_specific_date(self, date_str: str) -> Dict[str, Any]:
        """
        Get session count for a specific date.
        
        Args:
            date_str: Date string in format 'YYYY-MM-DD'
            
        Returns:
            Dictionary with count and details
        """
        query = f"""
            SELECT 
                COUNT(*) as count,
                COUNT(DISTINCT Student_Anon_ID) as unique_students,
                AVG(Actual_Session_Length * 60) as avg_duration_minutes
            FROM df
            WHERE DATE(Appointment_DateTime) = '{date_str}'
        """
        
        result = duckdb.query(query).df()
        
        if len(result) > 0:
            return {
                'count': int(result.iloc[0]['count']) if pd.notna(result.iloc[0]['count']) else 0,
                'unique_students': int(result.iloc[0]['unique_students']) if pd.notna(result.iloc[0]['unique_students']) else 0,
                'avg_duration_minutes': round(result.iloc[0]['avg_duration_minutes'], 1) if pd.notna(result.iloc[0]['avg_duration_minutes']) else 0
            }
        
        return {'count': 0, 'unique_students': 0, 'avg_duration_minutes': 0}
    
    def metric_by_semester(self, 
                         metric_column: str,
                         aggregation: str = 'AVG') -> pd.DataFrame:
        """
        Calculate a metric by semester.
        
        Args:
            metric_column: Column name to aggregate (e.g., 'Overall_Satisfaction', 'Actual_Session_Length')
            aggregation: SQL aggregation function (AVG, SUM, COUNT, MEDIAN, etc.)
            
        Returns:
            DataFrame with semester and metric columns
        """
        query = f"""
            SELECT 
                Semester_Label,
                {aggregation}({metric_column}) as {metric_column}
            FROM df
            GROUP BY Semester_Label
            ORDER BY Semester_Label
        """
        
        return duckdb.query(query).df()
    
    def top_n_metric_by_semester(self,
                                  metric_column: str,
                                  semester: str,
                                  n: int = 10,
                                  ascending: bool = False) -> pd.DataFrame:
        """
        Get top N records for a metric within a specific semester.
        
        Args:
            metric_column: Column to rank by
            semester: Semester label
            n: Number of results
            ascending: Sort order
            
        Returns:
            DataFrame with top N records
        """
        order = "ASC" if ascending else "DESC"
        
        query = f"""
            SELECT *
            FROM df
            WHERE Semester_Label = '{semester}'
                AND {metric_column} IS NOT NULL
            ORDER BY {metric_column} {order}
            LIMIT {n}
        """
        
        return duckdb.query(query).df()
    
    def filter_and_count(self,
                        filters: Dict[str, Any],
                        count_column: str = '*') -> int:
        """
        Count records matching multiple filter conditions.
        
        Args:
            filters: Dictionary of column: value pairs
            count_column: What to count (default: all rows)
            
        Returns:
            Count of matching records
        """
        where_clauses = []
        for column, value in filters.items():
            if isinstance(value, str):
                where_clauses.append(f"{column} = '{value}'")
            elif pd.isna(value):
                where_clauses.append(f"{column} IS NULL")
            else:
                where_clauses.append(f"{column} = {value}")
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT COUNT({count_column}) as count
            FROM df
            {where_clause}
        """
        
        result = duckdb.query(query).df()
        return int(result.iloc[0]['count'])
    
    def compare_semesters(self,
                         metric_column: str,
                         semester1: str,
                         semester2: str,
                         aggregation: str = 'AVG') -> Dict[str, Any]:
        """
        Compare a metric between two semesters.
        
        Args:
            metric_column: Column to compare
            semester1: First semester
            semester2: Second semester
            aggregation: SQL aggregation function
            
        Returns:
            Dictionary with values for both semesters and difference
        """
        query = f"""
            SELECT 
                Semester_Label,
                {aggregation}({metric_column}) as value
            FROM df
            WHERE Semester_Label IN ('{semester1}', '{semester2}')
            GROUP BY Semester_Label
        """
        
        result = duckdb.query(query).df()
        
        if len(result) >= 2:
            val1 = result[result['Semester_Label'] == semester1].iloc[0]['value']
            val2 = result[result['Semester_Label'] == semester2].iloc[0]['value']
            difference = float(val2) - float(val1)
            
            return {
                semester1: float(val1) if pd.notna(val1) else None,
                semester2: float(val2) if pd.notna(val2) else None,
                'difference': round(difference, 2),
                'direction': 'increased' if difference > 0 else 'decreased' if difference < 0 else 'no change'
            }
        
        return {'semester1': None, 'semester2': None, 'difference': None}
    
    def sessions_by_month(self,
                         semester: Optional[str] = None) -> pd.DataFrame:
        """
        Get session counts by month.
        
        Args:
            semester: Optional semester filter
            
        Returns:
            DataFrame with month and session_count columns
        """
        where_clause = f"WHERE Semester_Label = '{semester}'" if semester else ""
        
        query = f"""
            SELECT 
                MONTHNAME(Appointment_DateTime) as month,
                COUNT(*) as session_count
            FROM df
            {where_clause}
            GROUP BY MONTH(Appointment_DateTime), MONTHNAME(Appointment_DateTime)
            ORDER BY MONTH(Appointment_DateTime)
        """
        
        return duckdb.query(query).df()
    
    def sessions_by_day_of_week(self,
                               semester: Optional[str] = None,
                               location: Optional[str] = None) -> pd.DataFrame:
        """
        Get session counts by day of week with optional filters.
        
        Args:
            semester: Optional semester filter
            location: Optional location filter
            
        Returns:
            DataFrame with day_of_week and session_count columns
        """
        where_clauses = []
        if semester:
            where_clauses.append(f"Semester_Label = '{semester}'")
        if location:
            where_clauses.append(f"Location = '{location}'")
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT 
                DAYNAME(Appointment_DateTime) as day_of_week,
                COUNT(*) as session_count
            FROM df
            {where_clause}
            GROUP BY DAYOFWEEK(Appointment_DateTime), DAYNAME(Appointment_DateTime)
            ORDER BY DAYOFWEEK(Appointment_DateTime)
        """
        
        return duckdb.query(query).df()
    
    def sessions_by_hour(self,
                       semester: Optional[str] = None,
                       location: Optional[str] = None) -> pd.DataFrame:
        """
        Get session counts by hour with optional filters.
        
        Args:
            semester: Optional semester filter
            location: Optional location filter
            
        Returns:
            DataFrame with hour and session_count columns
        """
        where_clauses = []
        if semester:
            where_clauses.append(f"Semester_Label = '{semester}'")
        if location:
            where_clauses.append(f"Location = '{location}'")
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT 
                EXTRACT(HOUR FROM Appointment_DateTime) as hour,
                COUNT(*) as session_count
            FROM df
            {where_clause}
            GROUP BY hour
            ORDER BY hour
        """
        
        return duckdb.query(query).df()
    
    def get_busiest_date(self,
                        semester: Optional[str] = None,
                        location: Optional[str] = None) -> Dict[str, Any]:
        """
        Get date with most sessions (with optional filters).
        
        Args:
            semester: Optional semester filter
            location: Optional location filter
            
        Returns:
            Dictionary with date and count information
        """
        result = self.sessions_by_date(semester=semester, location=location, limit=1, ascending=False)
        
        if len(result) > 0:
            row = result.iloc[0]
            return {
                'date': str(row['date']),
                'session_count': int(row['session_count'])
            }
        
        return {'date': 'N/A', 'session_count': 0}
    
    def get_slowest_date(self,
                        semester: Optional[str] = None,
                        location: Optional[str] = None) -> Dict[str, Any]:
        """
        Get date with fewest sessions (with optional filters).
        
        Args:
            semester: Optional semester filter
            location: Optional location filter
            
        Returns:
            Dictionary with date and count information
        """
        result = self.sessions_by_date(semester=semester, location=location, limit=1, ascending=True)
        
        if len(result) > 0:
            row = result.iloc[0]
            return {
                'date': str(row['date']),
                'session_count': int(row['session_count'])
            }
        
        return {'date': 'N/A', 'session_count': 0}
