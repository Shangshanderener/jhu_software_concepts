#!/usr/bin/env python3
"""
query_data.py - SQL queries for Grad Cafe applicant data analysis.

This module provides functions to execute SQL queries against the PostgreSQL
database to answer the assignment questions.
"""

import psycopg



# Database configuration
DB_CONFIG = {
    'dbname': 'gradcafe',
    'user': 'kamisama',
    'password': '',
    'host': 'localhost',
    'port': '5432'
}


def get_connection():
    """Get a database connection using psycopg3."""
    return psycopg.connect(
        dbname=DB_CONFIG['dbname'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port']
    )


def execute_query(query, params=None):
    """Execute a query and return results."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            results = cur.fetchall()
            return results



# ============================================================================
# Question 1: How many entries do you have in your database who have applied 
#             for Fall 2026?
# ============================================================================
def q1_fall_2026_count():
    """
    Count entries for Fall 2026 applications.
    
    Query explanation: We filter the 'term' column for entries containing 
    'Fall 2026' to count applicants for that specific term.
    """
    query = """
        SELECT COUNT(*) 
        FROM applicants 
        WHERE term ILIKE '%Fall 2026%';
    """
    result = execute_query(query)
    return result[0][0] if result else 0


# ============================================================================
# Question 2: What percentage of entries are from international students 
#             (not American or Other) (to two decimal places)?
# ============================================================================
def q2_international_percentage():
    """
    Calculate percentage of international students.
    
    Query explanation: We count entries where us_or_international is 'International'
    and divide by total count, then multiply by 100 for percentage.
    ROUND is used to limit to 2 decimal places.
    """
    query = """
        SELECT ROUND(
            (COUNT(CASE WHEN us_or_international = 'International' THEN 1 END) * 100.0 / 
            NULLIF(COUNT(*), 0)), 2
        ) AS international_percentage
        FROM applicants;
    """
    result = execute_query(query)
    return result[0][0] if result else 0


# ============================================================================
# Question 3: What is the average GPA, GRE, GRE V, GRE AW of applicants who 
#             provide these metrics?
# ============================================================================
def q3_average_scores():
    """
    Calculate average GPA, GRE, GRE_V, and GRE_AW for applicants who provide them.
    
    Query explanation: We use AVG which automatically ignores NULL values,
    so only applicants who provided each metric are included in that average.
    """
    query = """
        SELECT 
            ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
            ROUND(AVG(gre)::numeric, 2) AS avg_gre,
            ROUND(AVG(gre_v)::numeric, 2) AS avg_gre_v,
            ROUND(AVG(gre_aw)::numeric, 2) AS avg_gre_aw
        FROM applicants
        WHERE gpa IS NOT NULL 
           OR gre IS NOT NULL 
           OR gre_v IS NOT NULL 
           OR gre_aw IS NOT NULL;
    """
    result = execute_query(query)
    if result:
        return {
            'avg_gpa': result[0][0],
            'avg_gre': result[0][1],
            'avg_gre_v': result[0][2],
            'avg_gre_aw': result[0][3]
        }
    return None


# ============================================================================
# Question 4: What is their average GPA of American students in Fall 2026?
# ============================================================================
def q4_american_fall_2026_gpa():
    """
    Calculate average GPA of American students for Fall 2026.
    
    Query explanation: We filter for American students (us_or_international = 'American')
    AND Fall 2026 term, then calculate the average GPA.
    """
    query = """
        SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
        FROM applicants
        WHERE us_or_international = 'American'
          AND term ILIKE '%Fall 2026%'
          AND gpa IS NOT NULL;
    """
    result = execute_query(query)
    return result[0][0] if result else None


# ============================================================================
# Question 5: What percent of entries for Fall 2025 are Acceptances 
#             (to two decimal places)?
# ============================================================================
def q5_fall_2025_acceptance_rate():
    """
    Calculate acceptance percentage for Fall 2025.
    
    Query explanation: We count accepted entries (status contains 'Accepted')
    for Fall 2025 and divide by total Fall 2025 entries.
    """
    query = """
        SELECT ROUND(
            (COUNT(CASE WHEN status ILIKE '%Accepted%' THEN 1 END) * 100.0 / 
            NULLIF(COUNT(*), 0)), 2
        ) AS acceptance_percentage
        FROM applicants
        WHERE term ILIKE '%Fall 2025%';
    """
    result = execute_query(query)
    return result[0][0] if result else 0


# ============================================================================
# Question 6: What is the average GPA of applicants who applied for Fall 2026 
#             who are Acceptances?
# ============================================================================
def q6_fall_2026_accepted_gpa():
    """
    Calculate average GPA of accepted Fall 2026 applicants.
    
    Query explanation: We filter for Fall 2026 term AND accepted status,
    then calculate average GPA of those applicants.
    """
    query = """
        SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
        FROM applicants
        WHERE term ILIKE '%Fall 2026%'
          AND status ILIKE '%Accepted%'
          AND gpa IS NOT NULL;
    """
    result = execute_query(query)
    return result[0][0] if result else None


# ============================================================================
# Question 7: How many entries are from applicants who applied to JHU for a 
#             masters degrees in Computer Science?
# ============================================================================

def q7_jhu_masters_cs_count():
    """
    Count JHU Masters in Computer Science applications.
    
    Query explanation: We search for 'Johns Hopkins' or 'JHU' in program field
    OR llm_generated_university field to be more robust.
    'Masters' in degree, and 'Computer Science' in program or llm_generated_program.
    Using ILIKE for case-insensitive matching.
    """
    query = """
        SELECT COUNT(*)
        FROM applicants
        WHERE (
            program ILIKE '%Johns Hopkins%' 
            OR program ILIKE '%JHU%'
            OR llm_generated_university ILIKE '%Johns Hopkins%'
            OR llm_generated_university ILIKE '%JHU%'
        )
        AND degree ILIKE '%Masters%'
        AND (
            program ILIKE '%Computer Science%'
            OR llm_generated_program ILIKE '%Computer Science%'
        );
    """
    result = execute_query(query)
    return result[0][0] if result else 0



# ============================================================================
# Question 8: How many entries from 2026 are acceptances from applicants who 
#             applied to Georgetown University, MIT, Stanford University, or 
#             Carnegie Mellon University for a PhD in Computer Science?
# ============================================================================
def q8_elite_phd_cs_2026_accepts():
    """
    Count PhD CS acceptances from elite universities for 2026.
    
    Query explanation: We filter for 2026 (either Fall or Spring),
    accepted status, PhD degree, Computer Science program, and
    specific universities (Georgetown, MIT, Stanford, CMU).
    """
    query = """
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%2026%'
          AND status ILIKE '%Accepted%'
          AND degree ILIKE '%PhD%'
          AND program ILIKE '%Computer Science%'
          AND (
              program ILIKE '%Georgetown%'
              OR program ILIKE '%MIT%'
              OR program ILIKE '%Massachusetts Institute%'
              OR program ILIKE '%Stanford%'
              OR program ILIKE '%Carnegie Mellon%'
              OR program ILIKE '%CMU%'
          );
    """
    result = execute_query(query)
    return result[0][0] if result else 0


# ============================================================================
# Question 9: Do your numbers for question 8 change if you use LLM Generated 
#             Fields (rather than your downloaded fields)?
# ============================================================================
def q9_elite_phd_cs_2026_llm_accepts():
    """
    Count PhD CS acceptances from elite universities using LLM-generated fields.
    
    Query explanation: Same as Q8 but using llm_generated_university and 
    llm_generated_program instead of program field.
    """
    query = """
        SELECT COUNT(*)
        FROM applicants
        WHERE term ILIKE '%2026%'
          AND status ILIKE '%Accepted%'
          AND degree ILIKE '%PhD%'
          AND llm_generated_program ILIKE '%Computer Science%'
          AND (
              llm_generated_university ILIKE '%Georgetown%'
              OR llm_generated_university ILIKE '%MIT%'
              OR llm_generated_university ILIKE '%Massachusetts Institute%'
              OR llm_generated_university ILIKE '%Stanford%'
              OR llm_generated_university ILIKE '%Carnegie Mellon%'
              OR llm_generated_university ILIKE '%CMU%'
          );
    """
    result = execute_query(query)
    return result[0][0] if result else 0


# ============================================================================
# Question 10 (Custom): What are the top 10 universities with highest 
#                       acceptance rates (minimum 20 total applications)?
# ============================================================================
def q10_top_universities_by_acceptance_rate():
    """
    Find top universities by acceptance rate.
    
    Query explanation: We group by university, count total applications and
    acceptances, filter for universities with at least 20 applications,
    then order by acceptance rate descending.
    """
    query = """
        SELECT 
            llm_generated_university,
            COUNT(*) AS total_applications,
            COUNT(CASE WHEN status ILIKE '%Accepted%' THEN 1 END) AS acceptances,
            ROUND(
                (COUNT(CASE WHEN status ILIKE '%Accepted%' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(*), 0)), 2
            ) AS acceptance_rate
        FROM applicants
        WHERE llm_generated_university IS NOT NULL AND llm_generated_university != ''
        GROUP BY llm_generated_university
        HAVING COUNT(*) >= 20
        ORDER BY acceptance_rate DESC
        LIMIT 10;
    """
    result = execute_query(query)
    return result


# ============================================================================
# Question 11 (Custom): What is the average GPA and acceptance rate by 
#                       degree type (PhD, Masters, etc.)?
# ============================================================================
def q11_stats_by_degree_type():
    """
    Calculate statistics by degree type.
    
    Query explanation: We group by degree type and calculate average GPA
    and acceptance rate for each degree category.
    """
    query = """
        SELECT 
            degree,
            COUNT(*) AS total_applications,
            ROUND(AVG(gpa)::numeric, 2) AS avg_gpa,
            ROUND(
                (COUNT(CASE WHEN status ILIKE '%Accepted%' THEN 1 END) * 100.0 / 
                NULLIF(COUNT(*), 0)), 2
            ) AS acceptance_rate
        FROM applicants
        WHERE degree IS NOT NULL AND degree != ''
        GROUP BY degree
        ORDER BY total_applications DESC;
    """
    result = execute_query(query)
    return result


# ============================================================================
# Get all results function (for Flask app)
# ============================================================================
def get_all_results():
    """Get all query results as a dictionary."""
    return {
        'q1': q1_fall_2026_count(),
        'q2': q2_international_percentage(),
        'q3': q3_average_scores(),
        'q4': q4_american_fall_2026_gpa(),
        'q5': q5_fall_2025_acceptance_rate(),
        'q6': q6_fall_2026_accepted_gpa(),
        'q7': q7_jhu_masters_cs_count(),
        'q8': q8_elite_phd_cs_2026_accepts(),
        'q9': q9_elite_phd_cs_2026_llm_accepts(),
        'q10': q10_top_universities_by_acceptance_rate(),
        'q11': q11_stats_by_degree_type()
    }


# ============================================================================
# Main - Run all queries and print results
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("Grad Cafe Database Analysis Results")
    print("=" * 70)
    
    print("\n【Q1】Fall 2026 Entries Count:")
    print(f"   {q1_fall_2026_count()} entries")
    
    print("\n【Q2】International Students Percentage:")
    print(f"   {q2_international_percentage()}%")
    
    print("\n【Q3】Average Scores:")
    scores = q3_average_scores()
    if scores:
        print(f"   GPA: {scores['avg_gpa']}")
        print(f"   GRE: {scores['avg_gre']}")
        print(f"   GRE V: {scores['avg_gre_v']}")
        print(f"   GRE AW: {scores['avg_gre_aw']}")
    
    print("\n【Q4】Average GPA of American Students (Fall 2026):")
    print(f"   {q4_american_fall_2026_gpa()}")
    
    print("\n【Q5】Fall 2025 Acceptance Rate:")
    print(f"   {q5_fall_2025_acceptance_rate()}%")
    
    print("\n【Q6】Average GPA of Fall 2026 Acceptances:")
    print(f"   {q6_fall_2026_accepted_gpa()}")
    
    print("\n【Q7】JHU Masters CS Applications:")
    print(f"   {q7_jhu_masters_cs_count()} entries")
    
    print("\n【Q8】Elite PhD CS 2026 Acceptances (Downloaded Fields):")
    print(f"   {q8_elite_phd_cs_2026_accepts()} acceptances")
    
    print("\n【Q9】Elite PhD CS 2026 Acceptances (LLM Fields):")
    llm_count = q9_elite_phd_cs_2026_llm_accepts()
    downloaded_count = q8_elite_phd_cs_2026_accepts()
    print(f"   {llm_count} acceptances")
    if llm_count != downloaded_count:
        print(f"   ⚠ Different from Q8! (Difference: {llm_count - downloaded_count})")
    else:
        print("   ✓ Same as Q8")
    
    print("\n【Q10】Top 10 Universities by Acceptance Rate (min 20 applications):")
    top_unis = q10_top_universities_by_acceptance_rate()
    for i, row in enumerate(top_unis, 1):
        print(f"   {i}. {row[0]}: {row[3]}% ({row[2]}/{row[1]} accepted)")
    
    print("\n【Q11】Statistics by Degree Type:")
    degree_stats = q11_stats_by_degree_type()
    for row in degree_stats:
        print(f"   {row[0]}: {row[1]} apps, GPA {row[2]}, {row[3]}% accepted")
    
    print("\n" + "=" * 70)
