-- Silver: cleaned + deduped facilities. nb() = non-blank ('', 'null', 'None', '[]' are nulls).
CREATE OR REPLACE TABLE workspace.hackathon.facilities_silver AS
WITH deduped AS (
  SELECT *,
         row_number() OVER (PARTITION BY coalesce(cluster_id, unique_id) ORDER BY unique_id) AS rn
  FROM workspace.hackathon.facilities_raw
),
nb AS (
  SELECT
    unique_id,
    nullif(nullif(nullif(trim(name), ''), 'null'), 'None')                    AS name,
    nullif(nullif(trim(coalesce(facilityTypeId, '')), ''), 'null')            AS facility_type,
    nullif(nullif(trim(coalesce(operatorTypeId, '')), ''), 'null')            AS operator_type,
    nullif(nullif(trim(coalesce(address_line1, '')), ''), 'null')             AS address_line1,
    nullif(nullif(trim(coalesce(address_city, '')), ''), 'null')              AS city,
    nullif(nullif(trim(coalesce(address_stateOrRegion, '')), ''), 'null')     AS state,
    CASE WHEN trim(coalesce(address_zipOrPostcode,'')) RLIKE '^[1-9][0-9]{5}$'
         THEN cast(trim(address_zipOrPostcode) AS bigint) END                 AS pincode,
    latitude, longitude,
    CASE WHEN latitude BETWEEN 6 AND 37 AND longitude BETWEEN 68 AND 98
         THEN true ELSE false END                                             AS geo_in_india,
    try_cast(nullif(nullif(trim(coalesce(capacity,'')), ''), 'null') AS int)        AS capacity_n,
    try_cast(nullif(nullif(trim(coalesce(numberDoctors,'')), ''), 'null') AS int)   AS doctors_n,
    try_cast(nullif(nullif(trim(coalesce(yearEstablished,'')), ''), 'null') AS int) AS year_est,
    nullif(nullif(trim(coalesce(description, '')), ''), 'null')               AS description,
    nullif(nullif(nullif(trim(coalesce(specialties, '')), ''), 'null'), '[]') AS specialties,
    nullif(nullif(nullif(trim(coalesce(capability, '')), ''), 'null'), '[]')  AS capability,
    nullif(nullif(nullif(trim(coalesce(procedure, '')), ''), 'null'), '[]')   AS procedure,
    nullif(nullif(nullif(trim(coalesce(equipment, '')), ''), 'null'), '[]')   AS equipment,
    CASE WHEN trim(coalesce(officialWebsite,'')) NOT IN ('', 'null')
              AND officialWebsite LIKE '%.%'
              AND lower(officialWebsite) NOT RLIKE 'justdial|practo|lybrate|facebook|google\\.'
         THEN trim(officialWebsite) END                                       AS website,
    CASE WHEN trim(coalesce(email,'')) LIKE '%@%' THEN trim(email) END        AS email,
    nullif(nullif(trim(coalesce(officialPhone, '')), ''), 'null')             AS phone,
    CASE WHEN lower(coalesce(facebookLink,'')) LIKE '%facebook%'
         THEN trim(facebookLink) END                                          AS facebook,
    (try_cast(engagement_metrics_n_followers AS int) > 0
       OR try_cast(post_metrics_post_count AS int) > 0
       OR lower(coalesce(custom_logo_presence,'')) IN ('true','1'))           AS social_active,
    cluster_id
  FROM deduped WHERE rn = 1
)
SELECT *,
  -- searchable lowercase blobs with LLM filler ("no specific ... listed") stripped
  regexp_replace(lower(coalesce(equipment,  '')), '[^"]*no specific[^"]*', '') AS equipment_s,
  regexp_replace(lower(coalesce(procedure,  '')), '[^"]*no specific[^"]*', '') AS procedure_s,
  regexp_replace(lower(coalesce(description,'')), '[^"]*no specific[^"]*', '') AS description_s,
  lower(coalesce(capability, ''))  AS capability_s,
  lower(coalesce(specialties, '')) AS specialties_s
FROM nb
