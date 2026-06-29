WITH source AS (
    SELECT * FROM {{ source('raw', 'telegram_messages') }}
),

cleaned AS (
    SELECT
        message_id::BIGINT                                  AS message_id,
        TRIM(channel_name)                                  AS channel_name,
        message_date::TIMESTAMPTZ                           AS message_date,
        TRIM(COALESCE(message_text, ''))                    AS message_text,
        COALESCE(has_media, FALSE)                          AS has_media,
        image_path,
        GREATEST(COALESCE(views, 0), 0)                    AS views,
        GREATEST(COALESCE(forwards, 0), 0)                 AS forwards,
        LENGTH(TRIM(COALESCE(message_text, '')))           AS message_length,
        CASE WHEN has_media THEN TRUE ELSE FALSE END        AS has_image
    FROM source
    WHERE
        message_id IS NOT NULL
        AND channel_name IS NOT NULL
        AND message_date IS NOT NULL
        AND message_date <= NOW()
)

SELECT * FROM cleaned