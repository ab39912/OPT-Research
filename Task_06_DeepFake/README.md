> ## SYNTHETIC MEDIA DISCLOSURE
> **Every audio/video artifact in this repository is AI-GENERATED (synthetic).**
> The voice is not a real person speaking; any face is generic or self-supplied,
> not a real named individual. Artifacts are labeled `SYNTHETIC_...` in their
> filenames and carry a spoken disclosure at the start and end. Nothing here
> should be taken as a genuine recording of any person.

# Task_06_Deep_Fake

A hands-on experiment in turning a written analytical narrative into synthetic
audio/video with free-tier AI tools, then evaluating where the output holds up,
where it breaks, and what marks it as synthetic. The goal is a **thoroughly
documented experiment**, not a polished product.

## What this project is

- **Source narrative:** the coach-advisory answer from Task 5 (the 2025 Syracuse
 Women's Lacrosse "focus on offense" recommendation), rewritten as a spoken
 monologue. See [`script.md`](script.md).
- **Construction:** the script is run through two distinct pipelines (ElevenLabs
 for voice, then D-ID for an audio-driven talking head).
- **Evaluation:** each artifact is assessed against a shared failure-mode
 vocabulary. See [`EVALUATION.md`](EVALUATION.md).
- **Detection/provenance:** at least one artifact is run through a detector
 and/or checked for content credentials. See [`DETECTION.md`](DETECTION.md).
- **Process log:** every attempt, tool version, prompt, setting, failure, and
 time cost is recorded as I go. See [`PROCESS_LOG.md`](PROCESS_LOG.md).

## Repository layout

```
README.md       this file (disclosure at top)
script.md       the source script + provenance to Task 5
PROCESS_LOG.md  running log: tool/version, prompts, settings, failures, time
EVALUATION.md   per-artifact critical assessment
DETECTION.md    detection/provenance check, results, interpretation
artifacts/      the generated media, labeled SYNTHETIC_...
```

## How to reproduce (as far as free tools allow)

1. Read [`script.md`](script.md), which is the exact text fed to every tool.
2. Pipeline A (voice): paste the script into ElevenLabs (free tier) and download
 the MP3 as `artifacts/SYNTHETIC_ward_analysis_elevenlabs.mp3`.
3. Pipeline B (video): in D-ID (free tier), pick a generic avatar and use the
 "upload audio" option to drive it with the ElevenLabs MP3 (this sidesteps the
 free-tier text limit); export `artifacts/SYNTHETIC_ward_analysis_did.mp4`.
4. Record each run in [`PROCESS_LOG.md`](PROCESS_LOG.md) as you go.
5. Assess each output in [`EVALUATION.md`](EVALUATION.md).
6. Check provenance / run a detector and record it in
 [`DETECTION.md`](DETECTION.md). Both artifacts are also labeled synthetic in
 their filenames and carry a spoken disclosure.

## What I learned

Grounded in the two runs (full detail in `PROCESS_LOG.md`, `EVALUATION.md`,
`DETECTION.md`):

- **Free tiers gate on text length, not effort.** Two tools (the first TTS tool
 and D-ID's text box) both capped input at ~20 words. The fix that unlocked the
 whole task was feeding D-ID my pre-generated ElevenLabs **audio** instead of
 typing a script, free tiers meter typed text, not uploaded audio.
- **Both outputs were convincing; the tells are specific.** The ElevenLabs clip
 has clean levels (mean −26.2 dB, no clipping) and sensible sentence-boundary
 pauses in one pass. The D-ID video's facial animation was genuinely strong on
 playback, the main real weakness was **slight lip-sync async** (mouth movement
 lagging/leading the audio). The clearest *external* tells were the free-tier
 **D-iD watermark** and the **static office background**, not the face itself.
- **The subtle audio tell is rhythm, not tone.** Measured pause lengths were
 fairly uniform (~0.35-0.48 s); humans vary pauses more. That regularity, not
 any single glitch, is what a careful listener would catch.
- **Provenance was the strongest detection signal, and the most fragile.** Both
 tools embed C2PA content credentials by default; the D-ID file even carries the
 standard `trainedAlgorithmicMedia` label. But it is signed with a *test* cert,
 and container-based credentials generally do not survive a re-encode or a
 social upload. So the AI label is trivial to read in the lab and easy to lose
 in the wild.
- **Detection layers answer different questions.** C2PA says *how the media was
 made*; an LLM reading the transcript says *who wrote the words*. Here the words
 are human (real analysis) while the voice is fully synthetic, the two checks
 can and did disagree, and both were right.

## Status
Done:
- Pipeline A: `artifacts/SYNTHETIC_ward_analysis_elevenlabs.mp3` (76.7 s)
- Pipeline B: `artifacts/SYNTHETIC_ward_analysis_did.mp4` (76.7 s)
- Evaluation, detection/provenance, and process log completed
- Remaining: drop in the exact slider values / minutes where noted, and
 (optional) the robustness re-encode test and a self-recorded voice comparison.

## Notes on scope and ethics
- This is a research task, not a production task. Rough edges are fine and, when
 documented, are the point.
- No deepfakes of real, identifiable people. The synthetic element is a generic
 or self voice/face reading analysis. Emma Ward is named only as an analytical
 reference to public stats, not impersonated.
- Every artifact is labeled synthetic in filename, in this README, and in-media.
- GitHub blocks files over 100 MB. Keep clips short and compressed, or use Git
 LFS for anything large. Prefer MP3/MP4 at modest bitrate.
