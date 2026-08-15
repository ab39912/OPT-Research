# Process Log

Running log of the experiment. One block per attempt, including what failed on
the way to what worked.

---

## Attempt 1, ElevenLabs, 2026-08-10 (Pipeline A: voice-only)

- **Tool + version / free-tier limits:** ElevenLabs (web, Aug 2026), free tier
 (~10k characters/month). The full ~260-word script fit in one generation.
- **Pipeline:** Voice-only (text-to-speech).
- **Input:** full text of `script.md`, including the opening/closing spoken
 disclosures.
- **Voice:** "Jessa - Easygoing and Effortless."
- **Settings (from export filename, replace with the real slider values you
 set):** speed, stability, similarity, style, speaker-boost, model. Filename
 encodes `sp96 s41 sb100 se49` and model `m2`.
- **Minor snag:** an early paste dropped a space, rendering "scored about fifteen"
 as one run-together word in the preview; re-copying the script fixed it before
 the final generation.
- **Result:** -> `artifacts/SYNTHETIC_ward_analysis_elevenlabs.mp3`
 (measured: 76.7 s, 130 kbps, mono; mean volume −26.2 dB, peak −2.0 dB -> healthy
 dynamic range, no clipping).
- **Notes:** provenance check later showed ElevenLabs embeds C2PA content
 credentials in the MP3 (see DETECTION.md).
- **Time spent:** <minutes>

## Attempt 2, D-ID, 2026-08-10 (Pipeline B: audio-driven face)

- **Tool + version / free-tier limits:** D-ID Studio (web, Aug 2026), free
 credits. Output carries a visible tiled "D-iD" watermark on the free tier.
- **Pipeline:** audio-driven talking-head video (distinct from Pipeline A).
- **Key workaround:** D-ID's *text* box has the same ~20-word free limit, so I
 used **"Upload audio"** and fed it the ElevenLabs MP3 instead of typing a
 script. This sidesteps the text cap entirely, a useful finding about how these
 free tiers are structured (they meter text input, not uploaded audio).
- **Presenter:** <generic D-ID stock avatar / my own photo, state which; do not
 use a real named person>.
- **Result:** -> `artifacts/SYNTHETIC_ward_analysis_did.mp4`
 (measured: 76.7 s, 1920×1920 square, H.264 + AAC, ~10.6 MB, ~1.1 Mbps).
- **Notes:** carries embedded C2PA credentials declaring AI origin (see
 DETECTION.md). Visible artifacts noted in EVALUATION.md.
- **Time spent:** <minutes>

---

## Refusals, filters, and degradations
| tool | what I asked | response | likely trigger |
|---|---|---|---|
| D-ID | type full script into text box | blocked at ~20 words | free-tier text cap (dodged via audio upload) |
| D-ID | free render | forced visible D-iD watermark | free-tier branding |
| ElevenLabs | voice a prebuilt voice reading analysis | allowed | (no consent gate hit; I did not attempt to clone a real person) |

## Time & cost summary
| pipeline | tool | time (min) | free-tier cost | result |
|---|---|---|---|---|
| A | ElevenLabs | <> | ~part of monthly char cap | 76.7 s MP3 |
| B | D-ID | <> | free credits + watermark | 76.7 s MP4 |

## Bonus attempts (optional)
- **Local open-source pipeline:** <Coqui/XTTS + SadTalker/Wav2Lip? setup notes,
 what the consumer tools hide, hardware needed.>
- **Defeat detection:** <after DETECTION.md, did re-encoding strip the C2PA
 credentials? that is the natural "defeat provenance" experiment here.>
- **C2PA survive transforms:** <re-encode / screen-record / social upload and
 re-check the C2PA credentials with c2patool.>
