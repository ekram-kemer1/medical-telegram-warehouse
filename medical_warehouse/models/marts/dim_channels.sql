WITH base AS (
    SELECT DISTINCT channel_name
    FROM {{ ref('stg_telegram_messages') }}
),

with_stats AS (
    SELECT
        channel_name,
        MIN(message_date)    AS first_post_date,
        MAX(message_date)    AS last_post_date,
        COUNT(*)             AS total_posts,
        ROUND(AVG(views), 2) AS avg_views
    FROM {{ ref('stg_telegram_messages') }}
    GROUP BY channel_name
)

SELECT
    MD5(channel_name)           AS channel_key,
    channel_name,
    CASE
        WHEN LOWER(channel_name) LIKE '%pharma%'  THEN 'Pharmaceutical'
        WHEN LOWER(channel_name) LIKE '%cosmet%'  THEN 'Cosmetics'
        WHEN LOWER(channel_name) LIKE '%lobelia%' THEN 'Cosmetics'
        ELSE 'Medical'
    END                         AS channel_type,
    first_post_date,
    last_post_date,
    total_posts,
    avg_views
FROM with_stats