-- ============================================================
-- Job Market Intelligence: Key Analysis Queries
-- Author: Siri Namala
-- ============================================================

-- Q1: Top Skills in Demand across Analyst Roles
SELECT skill,
       COUNT(*) AS posting_count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_postings), 1) AS demand_pct
FROM job_skills
GROUP BY skill
ORDER BY posting_count DESC;

-- Q2: Job Demand by State (Top 20)
SELECT state,
       COUNT(*) AS job_count,
       ROUND(AVG(salary_usd), 0) AS avg_salary_usd
FROM job_postings
WHERE state IS NOT NULL
GROUP BY state
ORDER BY job_count DESC
LIMIT 20;

-- Q3: Demand by Experience Level
SELECT experience_level,
       COUNT(*) AS job_count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_postings), 1) AS pct,
       ROUND(AVG(salary_usd), 0) AS avg_salary_usd
FROM job_postings
WHERE experience_level != 'Not Specified'
GROUP BY experience_level
ORDER BY job_count DESC;

-- Q4: Average Salary by Role Category
SELECT role_category,
       COUNT(*) AS job_count,
       ROUND(AVG(salary_usd), 0) AS avg_salary_usd,
       ROUND(MIN(salary_usd), 0) AS min_salary,
       ROUND(MAX(salary_usd), 0) AS max_salary
FROM job_postings
WHERE salary_usd IS NOT NULL
GROUP BY role_category
ORDER BY avg_salary_usd DESC;

-- Q5: Work Type Distribution (Full-time vs Contract vs Remote)
SELECT work_type,
       COUNT(*) AS job_count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_postings), 1) AS pct,
       ROUND(AVG(salary_usd), 0) AS avg_salary_usd
FROM job_postings
GROUP BY work_type
ORDER BY job_count DESC;

-- Q6: Salary Benchmark by Experience Level (from DS Salaries dataset)
SELECT experience_level,
       job_title,
       ROUND(AVG(salary_usd), 0) AS avg_salary,
       COUNT(*) AS records
FROM salary_benchmarks
WHERE salary_usd BETWEEN 30000 AND 400000
  AND job_title IN ('Data Analyst', 'Business Analyst', 'Data Scientist',
                    'Data Engineer', 'Analytics Engineer')
GROUP BY experience_level, job_title
ORDER BY job_title, avg_salary DESC;

-- Q7: Skill Co-occurrence (which skills appear together most)
SELECT a.skill AS skill_1,
       b.skill AS skill_2,
       COUNT(*) AS co_count
FROM job_skills a
JOIN job_skills b ON a.job_id = b.job_id AND a.skill < b.skill
GROUP BY a.skill, b.skill
ORDER BY co_count DESC
LIMIT 20;

-- Q8: Top Hiring Companies
SELECT company_name,
       COUNT(*) AS openings,
       ROUND(AVG(salary_usd), 0) AS avg_salary
FROM job_postings
WHERE company_name IS NOT NULL
GROUP BY company_name
ORDER BY openings DESC
LIMIT 15;
