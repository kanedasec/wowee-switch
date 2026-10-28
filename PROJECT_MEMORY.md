# WoWee Switch shared project memory

Last updated: 2026-10-27

This is the tool-neutral handoff for both Codex and Claude working on Kane's
WoWee Switch fork. Read it before acting and update it whenever a decision,
diagnosis, implementation, deployment target, or verification result changes.
The deeper historical/technical ledger remains [docs/FINDINGS.md](docs/FINDINGS.md).

## Operator intent and safety boundaries

- The target is a modded Nintendo Switch using Hekate + Atmosphere.
- Do not install the bundled local server unless the operator explicitly asks.
  Current play is against the external realm `logon.warstorm.org`.
- Do not delete, move, or overwrite unrelated SD-card files, installed games,
  `Nintendo`, `emuMMC`, or `/wowps/Data`.
- Deploy only files produced for the requested change. The active runtime addon
  tree is `/switch/wowee/addons`; do not assume the staging mirror under
  `/switch/wowee/data/addons` is active.
- Every code fix for this customized fork gets its own commit and is pushed to
  the `personal` fork. Do not combine unrelated fixes into one commit.
- Hardware deployment is permitted while `ftpd` is running because the WoWee
  title is then not running. Never overwrite the NRO while WoWee is active.

## Repository and console state

- Checkout: `/home/kanedasec/Projects/wowee-switch`
- Working branch: `feature/single-player-rates-forwarder`
- Upstream: `origin = joshshiman/wowee-switch`
- Operator fork: `personal = kanedasec/wowee-switch`
- Current console FTP: `192.168.0.55:5000`, anonymous, passive mode.
- Executable: `/switch/wowee/wowee.nro`
- Loose addons: `/switch/wowee/addons`
- Client data: `/wowps/Data` (about 17 GiB; preserve it)
- Logs: `/wowps/wowps/logs/{boot.log,wowps.log}`
- Local Switch toolchain: `/home/kanedasec/Projects/devkitpro`
- Switch build tree: `build-switch`; staged package:
  `wowee/out/switch/switch/wowee`

Build with all three toolchain variables because the linker also reads
`DEVKITPRO`:

```sh
DEVKITPRO=/home/kanedasec/Projects/devkitpro \
DEVKITARM=/home/kanedasec/Projects/devkitpro/devkitARM \
DEVKITA64=/home/kanedasec/Projects/devkitpro/devkitA64 \
cmake --build build-switch --parallel 4
```

## Custom fork implementation ledger

- `73b2984` — local single-player settings for XP/reward rates and raid boss
  scaling. These affect the embedded/local realm only; an external server owns
  its own rates and boss tuning.
- `0cb87a8` — WoWee icon and Switch forwarder packaging.
- `3a89733` — recognize the normalized forwarder title ID.
- `c47a4a3` — keep the virtual keyboard above the Connection Options sheet so
  an external realmlist can be entered without a USB keyboard.
- `200d4bb` — restore remote-realm combat controls and animations by routing
  controller actions through the remote client/server action path.
- `ceb25cd` — direct-dispatch every mapped action slot through `UseAction`.
  ConsolePort hides the Blizzard multi-action frames, so ZR slots previously
  ran dead `MultiActionButton` scripts. Presses now use slots directly and
  releases are consumed. ZR+B is migrated from nonexistent
  `EXTRAACTIONBUTTON1` to `MULTIACTIONBAR1BUTTON4` (action slot 64).
- `9afc6ac` — present non-NPC/item-originated gossip. Warstorm's Book of Powers
  returns a valid `SMSG_GOSSIP_MESSAGE`, but its owner is an item or player,
  not a creature. Such a menu now supersedes stale quest details and explicitly
  shows/refreshes `GossipFrame`; `SelectGossipOption` still sends the original
  owner GUID/menu/option to the server.

## Current controller/action model

- Base action-bar commands and all four multi-action-bar tiers map to slots
  1..120 in `LuaEngine::dispatchBindingKey` and execute `UseAction` directly.
- ZR face layer is a contiguous four-slot bar:
  ZR+Y = slot 61, ZR+X = 62, ZR+A = 63, ZR+B = 64.
- Saved ConsolePort bindings carry `woweeBindRev`; revision 8 performs the
  ZR+B migration and reloads override bindings.
- Placing a carried spell/item on an empty mapped slot is supported. Occupied
  slots are deliberately not silently overwritten.

## Evidence and verification for the 2026-10-27 fixes

- Console logs showed ZR commands reaching
  `MULTIACTIONBAR1BUTTON1..3 -> script` without a cast, while a base action
  reached `-> action` and produced server spell packets. This isolated the
  hidden multi-bar FrameXML path rather than the realm or skill data.
- The same log showed three successful Warstorm replies for the Book of Powers:
  `SMSG_GOSSIP_MESSAGE`, wire `0x17d`, size 958. The item use and server were
  therefore working; client presentation was the missing stage.
- Regression tests:
  `python3 wowee/tools/tests/switch_action_dispatch_test.py` and
  `python3 wowee/tools/tests/item_gossip_framexml_test.py`.
- Both fixes compile/link and package in the Switch build. The staged and built
  NROs were byte-identical, and `verify_tls_access.py` passed against the linked
  ELF.
- Deployed on 2026-10-27 to `192.168.0.55`: only
  `/switch/wowee/wowee.nro` and the two modified ConsolePort files were
  replaced. All three installed files were read back over FTP and matched their
  local SHA-256 hashes. NRO SHA-256:
  `8edea3b13aea770a864be43c10a9e4abe37106c4f839d3501c3e95a7352c9d6a`.
- Previous deployed versions are recoverable at the same paths with suffix
  `.pre-zr-gossip-20261027.bak`. No other SD-card path was modified.

## Pending on-device behavior checks

- Confirm ZR+Y/X/A/B use the four actions shown in slots 61..64 and do not drop
  the current target.
- Confirm the Book of Powers opens its Warstorm menu and a selected power is
  applied. The release log should contain `[WOWEE_GOSSIP] virtual owner=...`.
- If a check fails, fetch both console logs before changing code. Do not infer
  failure from the UI alone.
