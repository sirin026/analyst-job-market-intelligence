"""
Job Market Intelligence — Full Pipeline
Author: Siri Namala

Loads cleaned CSVs into SQLite, runs 8 analysis queries,
and exports Tableau-ready CSVs to the dashboard/ folder.

Usage:
    python sql/02_load_and_query.py
"""

import pandas as pd
import sqlite3
import os

# ── PATHS (relative to repo root) ────────────────────────────────────────────
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, 'sql', 'job_market.db')
OUT     = os.path.join(ROOT, 'data', 'cleaned')
SCHEMA  = os.path.join(ROOT, 'sql', '01_schema.sql')
TAB     = os.path.join(ROOT, 'dashboard')

# ── BUILD DATABASE ────────────────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)

with open(SCHEMA) as f:
    conn.executescript(f.read())

# Load LinkedIn cleaned data
linkedin = pd.read_csv(os.path.join(OUT, 'linkedin_analyst_clean.csv'))

# job_postings table
postings = linkedin[['job_id', 'company_name', 'title', 'role_category',
                      'state', 'city', 'experience_level', 'work_type',
                      'is_remote', 'normalized_salary', 'applies']].copy()
postings.rename(columns={'normalized_salary': 'salary_usd'}, inplace=True)
postings.to_sql('job_postings', conn, if_exists='replace', index=False)

# job_skills table (unpivot skill flag columns)
skill_cols = [c for c in linkedin.columns if c.startswith('skill_')]
skills_long = []
for _, row in linkedin.iterrows():
    for col in skill_cols:
        if row[col] == 1:
            skill_name = col.replace('skill_', '').replace('_', ' ')
            skills_long.append({'job_id': row['job_id'], 'skill': skill_name})

skills_df = pd.DataFrame(skills_long)
skills_df.to_sql('job_skills', conn, if_exists='replace', index=False)

# salary_benchmarks table
sal = pd.read_csv(os.path.join(OUT, 'salaries_clean.csv'))
sal_insert = sal[['work_year', 'job_title', 'experience_level', 'employment_type',
                   'salary_in_usd', 'remote_ratio', 'remote_label',
                   'company_size_label', 'company_location']].copy()
sal_insert.rename(columns={'salary_in_usd': 'salary_usd',
                            'company_size_label': 'company_size'}, inplace=True)
sal_insert.to_sql('salary_benchmarks', conn, if_exists='replace', index=False)

conn.commit()
print("Database built.\n")

# ── KEY SQL QUERIES ───────────────────────────────────────────────────────────

queries = {

    "1. Top Skills in Demand": """
        SELECT skill, COUNT(*) as posting_count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_postings), 1) as demand_pct
        FROM job_skills
        GROUP BY skill
        ORDER BY posting_count DESC;
    """,

    "2. Jobs by State (Top 15)": """
        SELECT state, COUNT(*) as job_count,
               ROUND(AVG(salary_usd), 0) as avg_salary_usd
        FROM job_postings
        WHERE state IS NOT NULL
        GROUP BY state
        ORDER BY job_count DESC
        LIMIT 15;
    """,

    "3. Demand by Experience Level": """
        SELECT experience_level,
               COUNT(*) as job_count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_postings), 1) as pct,
               ROUND(AVG(salary_usd), 0) as avg_salary_usd
        FROM job_postings
        WHERE experience_level != 'Not Specified'
        GROUP BY experience_level
        ORDER BY job_count DESC;
    """,

    "4. Avg Salary by Role Category": """
        SELECT role_category,
               COUNT(*) as job_count,
               ROUND(AVG(salary_usd), 0) as avg_salary_usd,
               ROUND(MIN(salary_usd), 0) as min_salary,
               ROUND(MAX(salary_usd), 0) as max_salary
        FROM job_postings
        WHERE salary_usd IS NOT NULL
        GROUP BY role_category
        ORDER BY avg_salary_usd DESC;
    """,

    "5. Remote vs On-site Breakdown": """
        SELECT work_type,
               COUNT(*) as job_count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_postings), 1) as pct,
               ROUND(AVG(salary_usd), 0) as avg_salary_usd
        FROM job_postings
        GROUP BY work_type
        ORDER BY job_count DESC;
    """,

    "6. Salary Benchmark by Experience (DS Salaries)": """
        SELECT experience_level, job_title,
               ROUND(AVG(salary_usd), 0) as avg_salary,
               COUNT(*) as records
        FROM salary_benchmarks
        WHERE salary_usd BETWEEN 30000 AND 400000
          AND job_title IN ('Data Analyst', 'Business Analyst', 'Data Scientist',
                            'Data Engineer', 'Analytics Engineer')
        GROUP BY experience_level, job_title
        ORDER BY job_title, avg_salary DESC;
    """,

    "7. Skill Co-occurrence (top pairs)": """
        SELECT a.skill as skill_1, b.skill as skill_2, COUNT(*) as co_count
        FROM job_skills a
        JOIN job_skills b ON a.job_id = b.job_id AND a.skill < b.skill
        GROUP BY a.skill, b.skill
        ORDER BY co_count DESC
        LIMIT 15;
    """,

    "8. Top Hiring Companies": """
        SELECT company_name, COUNT(*) as openings,
               ROUND(AVG(salary_usd), 0) as avg_salary
        FROM job_postings
        WHERE company_name IS NOT NULL
        GROUP BY company_name
        ORDER BY openings DESC
        LIMIT 15;
    """,
}

results = {}
for name, q in queries.items():
    print(f"\n{'='*60}")
    print(f"  {name}")
    print('='*60)
    result = pd.read_sql_query(q, conn)
    print(result.to_string(index=False))
    results[name] = result

conn.close()

# ── EXPORT TABLEAU-READY CSVs ─────────────────────────────────────────────────
os.makedirs(TAB, exist_ok=True)
results["1. Top Skills in Demand"].to_csv(os.path.join(TAB, 'skill_demand.csv'), index=False)
results["2. Jobs by State (Top 15)"].to_csv(os.path.join(TAB, 'jobs_by_state.csv'), index=False)
results["3. Demand by Experience Level"].to_csv(os.path.join(TAB, 'experience_demand.csv'), index=False)
results["4. Avg Salary by Role Category"].to_csv(os.path.join(TAB, 'salary_by_role.csv'), index=False)
results["5. Remote vs On-site Breakdown"].to_csv(os.path.join(TAB, 'work_type.csv'), index=False)
results["6. Salary Benchmark by Experience (DS Salaries)"].to_csv(os.path.join(TAB, 'salary_benchmark.csv'), index=False)
results["7. Skill Co-occurrence (top pairs)"].to_csv(os.path.join(TAB, 'skill_cooccurrence.csv'), index=False)
results["8. Top Hiring Companies"].to_csv(os.path.join(TAB, 'top_companies.csv'), index=False)

print(f"\n\nAll Tableau CSVs exported to: {TAB}")
