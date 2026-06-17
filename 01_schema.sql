-- ============================================================
-- Job Market Intelligence: Data & Business Analyst Roles
-- Schema: SQLite
-- Author: Siri Namala
-- ============================================================

-- 1. LinkedIn Analyst Job Postings
CREATE TABLE IF NOT EXISTS job_postings (
    job_id              TEXT PRIMARY KEY,
    company_name        TEXT,
    title               TEXT,
    role_category       TEXT,
    state               TEXT,
    city                TEXT,
    experience_level    TEXT,
    work_type           TEXT,
    is_remote           INTEGER,
    salary_usd          REAL,
    applies             REAL
);

-- 2. Skills per posting (long format for analysis)
CREATE TABLE IF NOT EXISTS job_skills (
    job_id      TEXT,
    skill       TEXT,
    FOREIGN KEY (job_id) REFERENCES job_postings(job_id)
);

-- 3. Salary benchmarks by role and experience
CREATE TABLE IF NOT EXISTS salary_benchmarks (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    work_year           INTEGER,
    job_title           TEXT,
    experience_level    TEXT,
    employment_type     TEXT,
    salary_usd          REAL,
    remote_ratio        INTEGER,
    remote_label        TEXT,
    company_size        TEXT,
    company_location    TEXT
);

-- 4. Skill demand summary (aggregated)
CREATE VIEW IF NOT EXISTS v_skill_demand AS
SELECT
    skill,
    COUNT(*) AS posting_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_postings), 2) AS demand_pct
FROM job_skills
GROUP BY skill
ORDER BY posting_count DESC;

-- 5. Salary by experience (from benchmarks)
CREATE VIEW IF NOT EXISTS v_salary_by_experience AS
SELECT
    experience_level,
    job_title,
    ROUND(AVG(salary_usd), 0) AS avg_salary_usd,
    ROUND(MIN(salary_usd), 0) AS min_salary_usd,
    ROUND(MAX(salary_usd), 0) AS max_salary_usd,
    COUNT(*) AS record_count
FROM salary_benchmarks
WHERE salary_usd BETWEEN 30000 AND 500000
GROUP BY experience_level, job_title
ORDER BY avg_salary_usd DESC;

-- 6. Jobs by state
CREATE VIEW IF NOT EXISTS v_demand_by_state AS
SELECT
    state,
    COUNT(*) AS job_count,
    role_category,
    ROUND(AVG(salary_usd), 0) AS avg_salary
FROM job_postings
WHERE state IS NOT NULL
GROUP BY state, role_category
ORDER BY job_count DESC;
