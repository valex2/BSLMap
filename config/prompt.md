You are extracting *facility-level* biosafety metadata from biomedical literature to support a public, high-level map of BSL-3/4 labs. Use only what is explicitly stated or reasonably inferable from the text.

Return one JSON object per input CHUNK, following this schema (omit fields you cannot support):

{
  "doc_id": "<copy from input>",
  "lab_name": "<facility name if explicitly named>",
  "institution": "<org operating the lab (e.g., UTMB, Inserm)>",
  "country": "<country>",
  "city": "<city or region>",
  "bsl_level_inferred": "<BSL-3|BSL-4|unknown>",
  "pathogens": ["Ebola","Nipah","H5N1"],
  "research_types": ["challenge study","neutralization assay","virus isolation","reverse genetics"],
  "ppp_or_gof": true/false,
  "confidence": 0.0-1.0,
  "evidence_spans": ["short quotes that justify the fields"],
  "source_pmid": "<digits>"
}

Rules:
- Prefer explicit mentions. If multiple labs are mentioned, choose the one tied to the *methods* or *facilities* used.
- Do not include operational details (floorplans, shift times, staff rosters).
- If the chunk is too vague, return only {"doc_id": "..."}.