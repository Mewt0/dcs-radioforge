# Radio Preset Guide

The SRS-like pack is built with ffmpeg filters. It shapes the voice with band limits, EQ, compression, noise, mic clicks, and short transmission tails.

## Presets

| Preset | Sound | Suggested use |
| --- | --- | --- |
| Clean studio | Normalized, clean | Editing source, trailers, custom external processing |
| SRS VHF AM | Narrow, bright, busy | JTAC, FAC, low-level package comms |
| SRS UHF AM | Cleaner, compressed | Fighter-to-fighter, package lead |
| SRS FM | Fuller and tactical | Ground, helicopters, convoy, CSAR |
| SRS cockpit mic | Close helmet mic | Wingmen, player flight, cockpit chatter |
| SRS AWACS | Clear, authoritative | AWACS, GCI, controller calls |
| SRS bad reception | Noisy, clipped, masked | Weak signal, terrain masking, distant calls |
| Old Soviet radio | Gritty and narrow | Russian GCI, legacy ground radio |

## Signal Quality

- `85-100`: readable, professional radio.
- `65-84`: lightly degraded tactical comms.
- `40-64`: obvious weak reception.
- `15-39`: emergency or badly masked transmission.

## Mic Clicks

Enable mic clicks for push-to-talk realism. Disable them if you plan to add your own clicks in an external editor.

## DCS Mixing Tip

If a mission has engine noise, SAM launches, explosions, and music, make the radio slightly louder and clearer than it feels in isolation. In-mission context hides a lot of detail.
