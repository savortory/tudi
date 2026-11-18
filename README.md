# Tudi

Tudi is a home device gateway with a companion app. This repository hosts the open-source device recipe catalog.

## Device recipes

Camera recipes are grouped by manufacturer under `devices/camera`. Generic RTSP, MJPEG and ONVIF recipes sit under `generic`. Tudi Sense sits under `tudi`.

The [catalog manifest](devices/manifest.json) lists each recipe and its SHA-256 checksum. Reference-derived profiles require hardware verification and may vary by model and firmware. Some cameras require enabling local RTSP in the manufacturer app.

Use the [recipe schema](devices/recipe.schema.json) when adding a profile. Keep the ID stable, increment the revision when changing a published recipe, and use relative local endpoint paths. Enter device credentials in Gateway during setup. See THIRD_PARTY_NOTICES for attribution to LAN Camera Viewer.
