# Assignment Query Explanations

This document explains the SQL queries used to answer each question in the assignment. All queries are executed against the `applicants` table in the PostgreSQL database.

## Question 1: How many entries do you have in your database who have applied for Fall 2026?

**Query:**
```sql
SELECT COUNT(*) 
FROM applicants 
WHERE term ILIKE '%Fall 2026%';
```

**Explanation:**
We use the `check` operator `ILIKE` (case-insensitive distinct matching) to filter the `term` column for any entries containing "Fall 2026". `COUNT(*)` returns the total number of matching rows.

---

## Question 2: What percentage of entries are from international students (not American or Other)?

**Query:**
```sql
SELECT ROUND(
    (COUNT(CASE WHEN us_or_international = 'International' THEN 1 END) * 100.0 / 
    NULLIF(COUNT(*), 0)), 2
) AS international_percentage
FROM applicants;
```

**Explanation:**
1.  `COUNT(CASE WHEN us_or_international = 'International' THEN 1 END)`: Counts only the rows where the student is 'International'.
2.  `COUNT(*)`: Counts the total number of rows.
3.  `NULLIF(..., 0)`: Prevents division by zero if the table is empty.
4.  We multiply by 100.0 to get a percentage and use `ROUND(..., 2)` to format the result to two decimal places.

---

## Question 3: What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?

**Query:**
```sql
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
```

**Explanation:**
We use the aggregate function `AVG()` for each metric column (`gpa`, `gre`, `gre_v`, `gre_aw`). `AVG()` automatically ignores `NULL` values, so the average is calculated only over the entries that have a value for that specific metric. The `WHERE` clause excludes rows where *all* metrics are null, though strictly speaking `AVG` handles nulls per column independently.

---

## Question 4: What is their average GPA of American students in Fall 2026?

**Query:**
```sql
SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
FROM applicants
WHERE us_or_international = 'American'
  AND term ILIKE '%Fall 2026%'
  AND gpa IS NOT NULL;
```

**Explanation:**
We filter for rows identifying as 'American' AND applying for term 'Fall 2026'. Then we calculate the average of the `gpa` column for these specific rows.

---

## Question 5: What percent of entries for Fall 2025 are Acceptances?

**Query:**
```sql
SELECT ROUND(
    (COUNT(CASE WHEN status ILIKE '%Accepted%' THEN 1 END) * 100.0 / 
    NULLIF(COUNT(*), 0)), 2
) AS acceptance_percentage
FROM applicants
WHERE term ILIKE '%Fall 2025%';
```

**Explanation:**
1.  We filter the entire dataset to only consider 'Fall 2025' applicants (`WHERE term ILIKE '%Fall 2025%'`).
2.  From this subset, we count how many have a status containing "Accepted".
3.  We divide this "Accepted" count by the total count of Fall 2025 applicants to get the percentage.

---

## Question 6: What is the average GPA of applicants who applied for Fall 2026 who are Acceptances?

**Query:**
```sql
SELECT ROUND(AVG(gpa)::numeric, 2) AS avg_gpa
FROM applicants
WHERE term ILIKE '%Fall 2026%'
  AND status ILIKE '%Accepted%'
  AND gpa IS NOT NULL;
```

**Explanation:**
We filter for 'Fall 2026' term AND 'Accepted' status. Then we calculate the average `gpa` for this specific group of successful applicants.

---

## Question 7: How many entries are from applicants who applied to JHU for a masters degrees in Computer Science?

**Query:**
```sql
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
```

**Explanation:**
We filter for:
1.  University: "Johns Hopkins" or "JHU" in either the raw `program` string or the cleaning `llm_generated_university` field.
2.  Degree: "Masters".
3.  Program: "Computer Science" in either the raw or cleaned program fields.
This counts the specific applications matching all three criteria.

---

## Question 8: How many entries from 2026 are acceptances from applicants who applied to Georgetown, MIT, Stanford, or CMU for a PhD in Computer Science?

**Query:**
```sql
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
```

**Explanation:**
We filter for a specific combination of:
*   Year: 2026
*   Status: Accepted
*   Degree: PhD
*   Program: Computer Science
*   University: Any of the listed elite universities (using multiple `OR` conditions with wildcards).

---

## Question 9: Do your numbers for question 8 change if you use LLM Generated Fields?

**Query:**
```sql
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
```

**Explanation:**
This query is identical to Question 8, but it uses the standardized `llm_generated_university` and `llm_generated_program` columns instead of the raw `program` text. This allows us to compare if the cleaning process improved data capture.

---

## Question 10 (Custom): What are the top 10 universities with highest acceptance rates (minimum 20 total applications)?

**Query:**
```sql
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
```

**Explanation:**
1.  We group the data by `llm_generated_university`.
2.  We calculate the acceptance rate for each university.
3.  `HAVING COUNT(*) >= 20`: We filter out universities with fewer than 20 applications to avoid statistically insignificant results (e.g., 1/1 = 100%).
4.  `ORDER BY acceptance_rate DESC`: We sort the results from highest acceptance rate to lowest.
5.  `LIMIT 10`: We take only the top 10.

---

## Question 11 (Custom): What is the average GPA and acceptance rate by degree type?

**Query:**
```sql
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
```

**Explanation:**
We group the data by `degree` (Masters, PhD, etc.) and calculate the average GPA and acceptance rate for each group. This helps us understand the competitiveness of different degree types.
