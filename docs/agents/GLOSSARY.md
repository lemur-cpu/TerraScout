# Engineering glossary

## Candidate site

A place TerraScout nominated for investigation from terrain evidence. It is not a confirmed archaeological site.
_Code_: `CandidateFeature`
_Avoid_: new site (as an automatic label), discovery, find (as a claim)

## Confirmed site

A candidate a qualified reviewer has marked `expert_reviewed`, with community consultation where that is required. Software cannot assign this status.
_Code_: `ReviewStatus` value `expert_reviewed`
_Avoid_: auto-confirmed, model-validated site

## Evidence packet

The inspectable facts attached to a candidate site: residual score and its definition, geometry metrics, provenance/`observation_kind`, and skeptic alternatives.
_Code_: fields on `CandidateFeature`
_Avoid_: probability, confidence, P(archaeological)

## Anomaly score

A dimensionless residual/shape statistic (LRM z-score × compactness). Ranking key for the finder queue. Not a calibrated archaeological probability.
_Code_: `anomaly_score`, `ANOMALY_SCORE_DEFINITION`
_Avoid_: confidence, site probability

## New to search

A candidate this run had not already recorded. Not a claim that archaeologists or Indigenous communities do not know the place.
_Avoid_: undocumented, unknown site, new site (unqualified)
