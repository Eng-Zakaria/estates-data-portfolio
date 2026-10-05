-- v04_dept_allocation.sql — m2 NIA per FTE vs median by department (synthetic).
-- Space->dept mapping comes from truth spaces (same synthetic grain);
-- promote into dim_space when available. Ties to: page 4 bars.
WITH dept_nia AS (
    SELECT department_id, SUM(nia_m2) AS nia_m2
    FROM read_parquet('data/truth/spaces.parquet')
    GROUP BY 1
),
per_fte AS (
    SELECT
        d.department_id, d.department_name,
        n.nia_m2, d.staff_fte, d.student_fte,
        n.nia_m2 / NULLIF(d.staff_fte, 0) AS m2_per_staff,
        n.nia_m2 / NULLIF(d.student_fte, 0) AS m2_per_student
    FROM main.dim_department AS d
    JOIN dept_nia AS n USING (department_id)
)
SELECT
    department_id, department_name,
    ROUND(nia_m2, 1) AS nia_m2,
    ROUND(m2_per_staff, 1) AS m2_per_staff_fte,
    ROUND(m2_per_student, 2) AS m2_per_student_fte,
    ROUND((m2_per_staff - MEDIAN(m2_per_staff) OVER ()) / NULLIF(MEDIAN(m2_per_staff) OVER (), 0), 3) AS variance_to_median
FROM per_fte
ORDER BY m2_per_staff_fte DESC;
