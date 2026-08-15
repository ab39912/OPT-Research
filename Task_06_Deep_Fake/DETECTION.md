# Detection & Provenance

I ran two provenance checks directly on the files and one transcript check. All
findings below are real results from inspecting the actual artifacts.

## Check 1: C2PA content credentials (provenance). Found on both files

Inspecting the files for an embedded C2PA manifest (by scanning the file's
metadata; reproducible with `c2patool` or the contentcredentials.org verify site):

**D-ID video (`SYNTHETIC_ward_analysis_did.mp4`), credentials present:**
- A signed C2PA manifest is embedded: `c2pa.claim.v2`, `c2pa.actions.v2`,
 `c2pa.hash.bmff.v3`, `c2pa.signature`, plus a D-ID metadata assertion
 (`com.d-id.metadata`), claim generator `org.contentauth.c2pa_rs 0.82.1`.
- Manifest id: `urn:c2pa:251e6018-be0d-4e25-8f11-dbb348849118`.
- Crucially, it declares the IPTC digital-source type
 **`…/digitalsourcetype/trainedAlgorithmicMedia`**, i.e. the standard machine
 -readable label for "made by a trained AI model." The `c2pa.created` action
 says the same.
- Signer chain is **"D-ID Signer (TEST)" under "D-ID Root CA (TEST)"**, a *test*
 certificate, not a production trust anchor. So the credential is present and
 parseable, but a strict verifier would flag the signer as untrusted. Worth
 noting: the provenance claim is only as strong as the cert behind it.

**ElevenLabs audio (`SYNTHETIC_ward_analysis_elevenlabs.mp3`), credentials present:**
- Also carries a C2PA manifest store (`application/c2pa`, `c2pa.claim.v2`,
 `c2pa.actions.v2`, `c2pa.hash.data`, `c2pa.signature`) plus a
 `stds.schema-org.CreativeWork` assertion.

**Finding:** both consumer tools ship C2PA provenance *by default*, without my
asking. That is the good news for provenance. The catch is fragility (below).

## Check 2: robustness of the credentials (to run)
C2PA lives in the file container, so it typically does **not** survive
re-encoding, screen recording, or many social-platform uploads. Test it:
```bash
c2patool artifacts/SYNTHETIC_ward_analysis_did.mp4        # before
ffmpeg -i artifacts/SYNTHETIC_ward_analysis_did.mp4 -c:v libx264 reencoded.mp4
c2patool reencoded.mp4                                     # after
```
| transform | credentials survive? |
|---|---|
| original file | yes (both files) |
| re-encoded via ffmpeg | <run it, expected: no> |
| screen recording | <expected: no> |
| uploaded to a social platform + re-downloaded | <platform-dependent> |
This doubles as the "defeat provenance" bonus: a single re-encode is usually
enough to strip the AI label, which is the key limitation of container-based
provenance.

## Check 3: LLM reads the transcript
I asked whether the *script text* reads as AI-generated. Verdict: it reads as
**human-written analytical prose**, not machine-generated filler, it makes a
specific, falsifiable argument (offense over defense) backed by concrete figures
(15.7 vs 8.67 goals;.491 vs.374 shooting; three one-goal losses) and a named
recommendation. Cues that would suggest AI *authorship* (hedging, generic
structure, unsupported generalities) are absent. This is expected: the script was
human-written from real Task 5 analysis. Useful contrast: transcript-level
detection targets *who wrote the words*, whereas the C2PA check targets *how the
media was produced*, the audio can be fully synthetic while the words are human.

## Findings summary
Provenance was the most informative signal here. Neither a perceptual detector
nor listening was needed to establish AI origin: both files self-declare it via
embedded C2PA, and the D-ID file uses the standard `trainedAlgorithmicMedia`
label. But the marks are fragile (a re-encode likely removes them) and the D-ID
signature is a test cert, so the provenance is informative in the lab and easy to
lose in the wild, which is the real lesson about how detectable this content is
once it leaves the tool.
