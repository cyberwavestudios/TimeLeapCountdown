# Time Leap Countdown — private Replit recovery

This repository preserves the self-hosting handoff for Time Leap Countdown. It is owned by `cyberwavestudios`, not the former designer account.

`source-code-snapshot.zip` contains the reviewed application source and the media imported by its frontend. It omits dependency caches, credentials, Replit platform state, the original unused working assets, and the two large uploaded videos.

For deployment, download **`TimeLeapCountdown-static-tested-v2.zip` from this repository's Releases page**. It contains the complete tested static site and both recovered MP4s. Unzip it into an HTTPS web root and configure `index.html` fallback for routes such as `/main` and `/caesura-progress`. The release ZIP's `SELF-HOSTING.md` has verification details. The countdown's original target date was November 20, 2025, so the current site shows the completed phase.

The same Release also includes `TimeLeapCountdown-source-preservation.zip`, retaining original Replit-era build output and unused uploaded assets for archival purposes; it is **not** the deployable release. Project secrets are **not** in this repository. Keep Replit active until the replacement passes owner testing and DNS is changed.
