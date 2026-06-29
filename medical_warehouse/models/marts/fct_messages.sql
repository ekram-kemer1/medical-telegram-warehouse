WITH stg AS (
    SELECT * FROM {{ ref('stg_telegram_messages') }}
),

channels AS (
    SELECT channel_key, channel_name FROM {{ ref('dim_channels') }}
),

dates AS (
    SELECT date_key, full_date FROM {{ ref('dim_dates') }}
)

SELECT
    stg.message_id,
    c.channel_key,
    d.date_key,
    stg.message_text,
    stg.message_length,
    stg.views,
    stg.forwards,
    stg.has_image
FROM stg
LEFT JOIN channels c ON stg.channel_name = c.channel_name
LEFT JOIN dates    d ON stg.message_date::DATE = d.full_date