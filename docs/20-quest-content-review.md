# Quest content to check by hand

Found on 2026-10-01 while the quest pages were reworded for learners (intro, steps, "done when").
The rewording kept every name, path and requirement as the original had it, so anything wrong below is
still wrong on the page. Nothing here has been checked in the engine: each line is "this looks off", not "this is wrong".

## Choices made during the rewording (confirm these)

- **Old quest ids replaced.** Steps that named ids that no longer exist now name current quests: LD-01…08 became
  LDQ11…18, WL-03 became EAQ10, BP-02/03/04 became GDQ2/3/4, "LD-03 lock and key" became LDQ29. Matched by quest
  title, not by a record. Affected: GDQ3, LDQ13, LDQ18, LDQ20, LDQ27, LDQ29, LDQ32.
- **O1 to O4** have nothing to send, so their "done when" says so instead of starting with "Send".
- **Rank and thread wording removed.** "Rank 2 loop" / "R2 interactables" (EAQ22, EAQ23) became "built earlier".
  "Turn-in thread" (PQ18, LDQ27, SQ14) became "send your work". TAQ23's "another major / this rank" became
  "another specialization / quests at this level". EAQ14 and EAQ17 still say "R1".
- **Mentor line added** to the "done when" of AQ23, AQ29 and AQ36 (their proof type is mentor).
- **PQ8** step 5 named the internal file `majors.yaml`; it now says "another option is allowed here".

## Originals that look wrong, outdated or unclear

### Starter Quests
- SQ13: does not say where High Resolution Screenshot is found.
- SQ15: depends on a pinned bad example and a template in #help-desk.
- SQ16, SQ17: the proof is a Discord link, although work is reviewed on the site.

### Animation
- AQ28: "Animation Interface" is probably "Animation Layer Interface".
- AQ31: an Animation Modifier is named `AM_FootSync` (the montage prefix).
- AQ42: a blend profile is named `BP_LegsFast` (the Blueprint prefix).
- AQ56: "Gizmo Library / Gizmos" is now Shape Library / Shapes.
- AQ62: "Setup Event" is now Construction Event.
- AQ71, AQ73, AQ75: "Windows >" should be "Window >".
- AQ79: `SK_Mannequin_Skeleton` is the UE4 name.
- AQ84: nearly the same content as AQ45.
- AQ13, AQ21, AQ27: "Enable Root Motion" and "EnableRootMotion" are both used.
- AQ34: `[ViewDistanceQuality@0..3]` is shorthand a beginner may type as written.
- AQ43 step 4, AQ66 step 4: vague.
- AQ4, AQ5, AQ7, AQ8: very thin steps for expert topics.

### Cinematics
- CQ29, CQ55: "Master Config" is now "Primary Config".
- CQ52: plays `LS_Hair`, which no step creates.
- CQ63: the "Settings component" of a Post Process Volume is not a component.
- CQ61: the console variable names could not be confirmed.
- CQ44 vs CQ30, CQ46: the VCam app has two different names.
- CQ74: "done when" asks about Duration Type, which no step mentions.
- CQ42, CQ48: both create `LS_Intro`.
- CQ4, CQ5, CQ42: three names for the same Camera button.
- CQ43: "Revert Axis Y" may be a typo. CQ72 step 3 and CQ21's extra step are very compressed.

### Gameplay design
- GDQ35: "Apply Gameplay Effect To Owner" on an enemy should be "To Target".
- GDQ39: mixes two streaming methods on one level, which its own quiz warns against.
- GDQ40: "instance generator" is Spawn Data Generators.
- GDQ44: Can Crouch sits under Movement Capabilities.
- GDQ47: Homing Target cannot be set in defaults.
- GDQ56: the safe-zone step does not say where (`r.DebugSafeZone.TitleRatio`).
- GDQ61: uses legacy UE4 Gameplay Debugger names.
- GDQ64: says backtick for the Gameplay Debugger; other quests say apostrophe.
- GDQ69: `DefaultEngine.ini` may be the wrong ini file.
- GDQ79: the Dynamic Material Instance never replaces the blendable.
- GDQ85: seamless travel generally does not work in PIE.
- GDQ88: Add Components needs a component-receiver actor.
- GDQ7, LDQ40: "#showcase tagged Critique-wanted" and "/critique post" do not match.
- GDQ9: the steps do not cover the proof asked for.
- GDQ2 step 1: confusing.

### Level design
- LDQ62: "Settings > Plugins"; other quests use Edit > Plugins.
- LDQ63, LDQ110: enabling EQS, or an "Environment Query Editor plugin", is a UE4 leftover.
- LDQ68: the Viewport Options arrow may not match the newer toolbar.
- LDQ50: the visualizer path needs a check.
- LDQ74: key input placed in the Game Mode.
- LDQ76: loads the save on Game Mode BeginPlay "before the player spawns".
- LDQ79 step 5: unclear.
- LDQ89, LDQ94: "note in the docs" with no page named.
- LDQ102: does not name the node (Copy Mesh to Static Mesh).
- LDQ119: `MPQ_LevelReview` is probably MRQ_.
- LDQ120: relies on the Collab Viewer template.
- LDQ28: asks for an `L_Metrics` gym although LDQ11 builds `L_MetricsGym`.
- LDQ23: Kill Z destroys the player and no respawn is explained.
- LDQ34: sample "linked in #epic-games-resources".
- LDQ40: "a mentor or two peers" while the proof type is mentor.
- LDQ1–10, LDQ21–26: only two or three very short steps with no click paths.
- LDQ21, LDQ23, LDQ25, LDQ26, LDQ29, GDQ3: proof type is "screenshot" but the proof asked for is a clip.

### Lookdev and lighting
- EAQ36: "Right Ctrl + L" (usually Ctrl+L) and "Show > Shadow Frustum".
- EAQ44, TAQ39: use the FBX Import Options dialog; newer UE5 uses Interchange.
- EAQ53 vs EAQ91: "Show > Visualize" and "Show > Visualization".
- EAQ57: changing the parent Blend Mode affects all four spheres.
- EAQ58: the Refraction pin condition may be outdated.
- EAQ59: Substrate assumptions depend on the engine version.
- EAQ64: "dropdown next to Build" is UE4 wording.
- EAQ71: "Material" vs "Materials" menu.
- EAQ86 vs EAQ92: the option name differs.
- EAQ97 vs EAQ113: the window name differs.
- EAQ98: a corner piece sized 20×20×400, and power-of-two snapping against a grid of 100.
- EAQ99, EAQ101: unclear requirements.
- EAQ105: `stat tsr` labels unconfirmed.
- EAQ35: garbled reference "(EAQ25..03)".
- EAQ30: vague LUT workflow.
- EAQ5–7, EAQ19–21, EAQ32–34: very thin steps.

### Programming
- PQ46 steps 2 and 5: unclear.
- PQ49: "New Plugin" and "Plugin Content" are UE4 names.
- PQ50: the whole quest uses "Source Control" names (now Revision Control).
- PQ53: vague about how to cause the error.
- PQ55, PQ57, PQ59, PQ105: these tools are now under Tools > Debug.
- PQ62: an invalid object gives "Accessed None", not an editor crash.
- PQ63: cannot set a default for an Actor reference input.
- PQ43, PQ44, PQ65: key events in plain Actors need input enabled.
- PQ75: legacy input setting.
- PQ76 step 4: unclear.
- PQ79: the node names are Make/Break ItemRow.
- PQ87: the class wizard adds the U itself.
- PQ92, TAQ6: Execute Python Script is under Tools, not File.
- PQ102: NetworkProfiler.exe is legacy.
- PQ104: Session Frontend Profiler and .uestats are deprecated.
- PQ106: UE4 Gameplay Debugger extension, likely cannot be done as written.
- PQ107: missing the memory trace flag.
- PQ5: "done when" asks for "3 settings changed" but the steps do not cover it.
- PQ6: no location given for starting a trace.
- PQ9, PQ14, PQ15, PQ16: the steps are goals, not instructions.
- PQ20, PQ26, PQ27, PQ28: refer to unnamed pages ("Coder 03").
- PQ19: depends on GDQ4 from another path.

### Tech art
- TAQ47: Sampler Type Linear Color with Masks compression may not compile.
- TAQ43 step 4: confusing.
- TAQ36: two different filter paths for redirectors.
- TAQ5, TAQ9, TAQ12 and others: the Niagara prefix is `NS_` in some quests and `FXS_` in others.
- TAQ55: depends on an unnamed "sprite smoke quest" and unexplained materials.
- TAQ18: "blur code from the doc page" with no page named.
- TAQ1: "done when" lists 6 views and omits Lighting Only.
- TAQ99: "Tangent Y" is probably Tangent Z.
- TAQ88 vs TAQ82: "Scripted Actor Actions" and "Scripted Actions".
- TAQ97: "Launcher > Learn" is outdated, and "short PIE screenshot" probably means a clip.
- TAQ95: Editing Tools is in the Skeletal Mesh editor.
- TAQ104: asks for Epic timings the steps never set.
- TAQ107: `r.TemporalAA.Upsampling` is UE4-era.
- TAQ103: RenderDoc durations are not shown by default.
- TAQ72: QualitySwitch has no Medium input named, and the menu name depends on the version.
- TAQ63: the category step conflicts with its own quiz facts.
- TAQ58, TAQ100: steps too compressed to follow.
- TAQ60: color "B 50" looks odd.
