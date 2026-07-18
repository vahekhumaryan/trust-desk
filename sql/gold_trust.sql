-- Gold: facility_trust — rubric v1 (docs/data-profile.md). One row per facility,
-- per-capability claim/corroboration columns + component scores + tier.
CREATE OR REPLACE TABLE workspace.hackathon.facility_trust AS
WITH pin_dim AS (  -- pincodes has one row per post office; collapse to pincode grain
  SELECT pincode,
         first(district, true)  AS district,
         first(statename, true) AS statename
  FROM workspace.hackathon.pincodes
  GROUP BY pincode
),
caps AS (
  SELECT s.*,
    capability_s RLIKE '\\bicu\\b|intensive care|critical care|ventilator|\\bhdu\\b' AS claim_icu,
    cast(equipment_s   RLIKE '\\bicu\\b|intensive care|critical care|ventilator|\\bhdu\\b' AS int)
  + cast(procedure_s   RLIKE '\\bicu\\b|intensive care|critical care|ventilator|\\bhdu\\b' AS int)
  + cast(description_s RLIKE '\\bicu\\b|intensive care|critical care|ventilator|\\bhdu\\b' AS int) AS corr_icu,

    capability_s RLIKE 'surger|surgical|operation theat|operating theat|anesthes|anaesthes' AS claim_surgery,
    cast(equipment_s   RLIKE 'surger|surgical|operation theat|operating theat|anesthes|anaesthes|c-arm|cautery' AS int)
  + cast(procedure_s   RLIKE 'surger|surgical|operation theat|operating theat|anesthes|anaesthes' AS int)
  + cast(description_s RLIKE 'surger|surgical|operation theat|operating theat|anesthes|anaesthes' AS int) AS corr_surgery,

    capability_s RLIKE 'matern|obstet|deliver|labour room|labor room|gynec|midwif' AS claim_maternity,
    cast(equipment_s   RLIKE 'matern|obstet|deliver|labour|labor room|gynec|midwif|ctg|foetal|fetal' AS int)
  + cast(procedure_s   RLIKE 'matern|obstet|deliver|labour|labor room|gynec|midwif|caesar|cesar' AS int)
  + cast(description_s RLIKE 'matern|obstet|deliver|labour|labor room|gynec|midwif' AS int) AS corr_maternity,

    capability_s RLIKE 'emergency|casualty|ambulance|24x7|24 x 7|24/7' AS claim_emergency,
    cast(equipment_s   RLIKE 'emergency|casualty|ambulance|defibrillator|resuscitat' AS int)
  + cast(procedure_s   RLIKE 'emergency|casualty|ambulance|resuscitat' AS int)
  + cast(description_s RLIKE 'emergency|casualty|ambulance' AS int) AS corr_emergency,

    capability_s RLIKE 'oncolog|cancer|chemother|radiother|radiation therap|tumor|tumour' AS claim_oncology,
    cast(equipment_s   RLIKE 'oncolog|cancer|chemother|radiother|linear accelerator|linac|brachyther|cobalt' AS int)
  + cast(procedure_s   RLIKE 'oncolog|cancer|chemother|radiother|tumou?r|brachyther' AS int)
  + cast(description_s RLIKE 'oncolog|cancer|chemother|radiother|tumou?r' AS int) AS corr_oncology,

    capability_s RLIKE 'trauma|accident|fracture|orthopa' AS claim_trauma,
    cast(equipment_s   RLIKE 'trauma|c-arm|fracture|orthopa|implant' AS int)
  + cast(procedure_s   RLIKE 'trauma|accident|fracture|orthopa' AS int)
  + cast(description_s RLIKE 'trauma|accident|fracture|orthopa' AS int) AS corr_trauma,

    capability_s RLIKE '\\bnicu\\b|neonatal|incubator|premature|newborn' AS claim_nicu,
    cast(equipment_s   RLIKE '\\bnicu\\b|neonatal|incubator|phototherap|warmer' AS int)
  + cast(procedure_s   RLIKE '\\bnicu\\b|neonatal|premature|newborn' AS int)
  + cast(description_s RLIKE '\\bnicu\\b|neonatal|premature|newborn' AS int) AS corr_nicu,

    capability_s RLIKE 'dialysis|nephrolog|renal|kidney' AS claim_dialysis,
    cast(equipment_s   RLIKE 'dialysis|dialyser|dialyzer|nephrolog|renal|kidney|ro plant' AS int)
  + cast(procedure_s   RLIKE 'dialysis|nephrolog|renal|kidney|transplant' AS int)
  + cast(description_s RLIKE 'dialysis|nephrolog|renal|kidney' AS int) AS corr_dialysis,

    (capability_s RLIKE 'anesth|anaesth' OR equipment_s RLIKE 'anesth|anaesth'
      OR procedure_s RLIKE 'anesth|anaesth' OR description_s RLIKE 'anesth|anaesth'
      OR specialties_s RLIKE 'anesth|anaesth') AS anesthesia_signal
  FROM workspace.hackathon.facilities_silver s
),
scored AS (
  SELECT c.*, p.district AS pin_district, p.statename AS pin_state,
    -- A. Corroboration (40): credit 1.0 if >=2 fields, 0.5 if 1, 0 if none; neutral 0.5 when no claims
    (cast(claim_icu AS int) + cast(claim_surgery AS int) + cast(claim_maternity AS int)
     + cast(claim_emergency AS int) + cast(claim_oncology AS int) + cast(claim_trauma AS int)
     + cast(claim_nicu AS int) + cast(claim_dialysis AS int)) AS n_claims,
    (CASE WHEN claim_icu       THEN CASE WHEN corr_icu >= 2       THEN 1.0 WHEN corr_icu = 1       THEN 0.5 ELSE 0 END ELSE 0 END
   + CASE WHEN claim_surgery   THEN CASE WHEN corr_surgery >= 2   THEN 1.0 WHEN corr_surgery = 1   THEN 0.5 ELSE 0 END ELSE 0 END
   + CASE WHEN claim_maternity THEN CASE WHEN corr_maternity >= 2 THEN 1.0 WHEN corr_maternity = 1 THEN 0.5 ELSE 0 END ELSE 0 END
   + CASE WHEN claim_emergency THEN CASE WHEN corr_emergency >= 2 THEN 1.0 WHEN corr_emergency = 1 THEN 0.5 ELSE 0 END ELSE 0 END
   + CASE WHEN claim_oncology  THEN CASE WHEN corr_oncology >= 2  THEN 1.0 WHEN corr_oncology = 1  THEN 0.5 ELSE 0 END ELSE 0 END
   + CASE WHEN claim_trauma    THEN CASE WHEN corr_trauma >= 2    THEN 1.0 WHEN corr_trauma = 1    THEN 0.5 ELSE 0 END ELSE 0 END
   + CASE WHEN claim_nicu      THEN CASE WHEN corr_nicu >= 2      THEN 1.0 WHEN corr_nicu = 1      THEN 0.5 ELSE 0 END ELSE 0 END
   + CASE WHEN claim_dialysis  THEN CASE WHEN corr_dialysis >= 2  THEN 1.0 WHEN corr_dialysis = 1  THEN 0.5 ELSE 0 END ELSE 0 END
    ) AS credit_sum,
    -- B. Completeness (20): 8 checks x 2.5
    2.5 * (cast((name IS NOT NULL AND name NOT RLIKE '^\\[') IS TRUE AS int)
         + cast((capacity_n BETWEEN 1 AND 5000) IS TRUE AS int)
         + cast((doctors_n BETWEEN 1 AND 1000) IS TRUE AS int)
         + cast((year_est BETWEEN 1800 AND 2026) IS TRUE AS int)
         + cast(length(coalesce(description, '')) >= 60 AS int)
         + cast(specialties IS NOT NULL AS int)
         + cast((equipment IS NOT NULL AND equipment_s NOT LIKE '%no specific%') IS TRUE AS int)
         + cast((procedure IS NOT NULL AND procedure_s NOT LIKE '%no specific%') IS TRUE AS int)) AS completeness_score,
    -- C. Web presence (25)
    (CASE WHEN website IS NOT NULL THEN 10 ELSE 0 END
   + CASE WHEN email IS NOT NULL THEN 5 ELSE 0 END
   + CASE WHEN phone IS NOT NULL THEN 4 ELSE 0 END
   + CASE WHEN facebook IS NOT NULL THEN 2 ELSE 0 END
   + CASE WHEN social_active THEN 4 ELSE 0 END) AS web_score,
    -- D. Geo validity (15)
    (CASE WHEN geo_in_india THEN 8 ELSE 0 END
   + CASE WHEN p.pincode IS NOT NULL THEN 5 ELSE 0 END
   + CASE WHEN p.pincode IS NOT NULL AND
              (upper(coalesce(c.state, '')) = p.statename
               OR upper(coalesce(c.state, '')) = upper(coalesce(p.district, ''))) THEN 2 ELSE 0 END) AS geo_score,
    -- Penalties
    (CASE WHEN name IS NULL OR (facility_type IS NOT NULL AND facility_type NOT IN
            ('hospital','clinic','dentist','doctor','pharmacy','farmacy','nursing_home')) THEN 15 ELSE 0 END
   + CASE WHEN (lower(coalesce(name,'')) RLIKE 'multi.?special' OR capability_s RLIKE 'multi.?special')
              AND capacity_n < 10 THEN 5 ELSE 0 END
   + CASE WHEN capacity_n = 0 OR capacity_n > 5000 THEN 3 ELSE 0 END
   + CASE WHEN doctors_n > 1000 THEN 3 ELSE 0 END
   + CASE WHEN year_est BETWEEN 0 AND 15 THEN 3 ELSE 0 END
   + CASE WHEN claim_surgery AND NOT anesthesia_signal AND capacity_n < 50 THEN 3 ELSE 0 END) AS penalty
  FROM caps c
  LEFT JOIN pin_dim p ON c.pincode = p.pincode
)
SELECT unique_id, name, facility_type, operator_type, address_line1, city, state,
       pincode, pin_district, pin_state, latitude, longitude, geo_in_india,
       capacity_n, doctors_n, year_est, website, email, phone, facebook, social_active,
       claim_icu, corr_icu, claim_surgery, corr_surgery, claim_maternity, corr_maternity,
       claim_emergency, corr_emergency, claim_oncology, corr_oncology,
       claim_trauma, corr_trauma, claim_nicu, corr_nicu, claim_dialysis, corr_dialysis,
       anesthesia_signal, n_claims,
       round(CASE WHEN n_claims = 0 THEN 20.0 ELSE 40.0 * credit_sum / n_claims END, 1) AS corr_score,
       completeness_score, web_score, geo_score, penalty,
       greatest(0, round(
         (CASE WHEN n_claims = 0 THEN 20.0 ELSE 40.0 * credit_sum / n_claims END)
         + completeness_score + web_score + geo_score - penalty, 1)) AS trust_score,
       CASE
         WHEN greatest(0, (CASE WHEN n_claims = 0 THEN 20.0 ELSE 40.0 * credit_sum / n_claims END)
              + completeness_score + web_score + geo_score - penalty) >= 75 THEN 'Trusted'
         WHEN greatest(0, (CASE WHEN n_claims = 0 THEN 20.0 ELSE 40.0 * credit_sum / n_claims END)
              + completeness_score + web_score + geo_score - penalty) >= 50 THEN 'Plausible'
         WHEN greatest(0, (CASE WHEN n_claims = 0 THEN 20.0 ELSE 40.0 * credit_sum / n_claims END)
              + completeness_score + web_score + geo_score - penalty) >= 25 THEN 'Thin evidence'
         ELSE 'Red flag'
       END AS tier
FROM scored
