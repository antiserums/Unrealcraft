# Quest content review

Checked on 2026-10-01 against Epic's documentation for Unreal Engine 5.8 (dev.epicgames.com).
The first version of this file was a list of suspicions. Each one has now been checked and sorted into one of four lists.

There were two passes. The first pass is in `tools/quest_wording/update-0001.json` to `update-0008.json`. The second
pass is in `update-0101.json` to `update-0160.json`. Both were put into the curriculum with `tools/quest_wording.py apply`.
Only page text changed (title, docs link, intro, steps, "done when", quiz text). Nothing was run inside the editor, but
the second pass checked asset names, templates and engine settings in the files of a local Unreal Engine 5.8 install.

Where both passes changed the same quest, the second pass wins. The lists under "Fixed" that have no "second pass" in
their heading describe the first pass.

How to read the source of a fix:

- **docs** = confirmed on the named Epic documentation page for 5.8.
- **local** = confirmed in the files of a local Unreal Engine 5.8 install (templates, engine content, engine source).
- **known** = changed from knowledge of UE5, with no docs page that confirms it. Where the docs page still shows an
  older name, the quest now gives both names.
- **text** = a fix inside the quest set (names that did not match, proof that could not be sent, a missing step).

## Fixed

### Second pass: things that were removed from the engine
- Starter Content (all quests): the pack is no longer part of the engine, so no quest asks for it any more. 32 quests named it before this pass. Every such step now uses assets of the Third Person template (the mannequin textures T_Quinn_01_D, _N and _MRA, the LevelPrototyping meshes and T_GridChecker_A), engine content (basic shapes, grid textures, WhiteNoise and the compile sounds, the light profiles in EngineLightProfiles), shapes from Modeling Mode, or a small asset the quest makes itself. Hand-fixed steps: AQ16, CQ24, CQ71, CQ72, GDQ50, GDQ76, LDQ6, LDQ8, LDQ26, LDQ35 (quiz), LDQ54, LDQ55, LDQ97, LDQ99, LDQ101, EAQ3, EAQ11, EAQ14 to EAQ17, EAQ19, EAQ20, EAQ27, EAQ32, EAQ34, EAQ41, EAQ45, EAQ48 to EAQ51, EAQ58, EAQ60 to EAQ65, EAQ68, EAQ70 to EAQ76, EAQ80 to EAQ85, EAQ87, EAQ90, EAQ93 to EAQ96, EAQ105, EAQ108, EAQ109, EAQ112, PQ32 to PQ35, PQ67, SQ2 (step and quiz question 4), SQ4, SQ8, TAQ17 (quiz), TAQ55, TAQ56, TAQ57. local: `TemplateProjectDefs.h` marks StarterContent as deprecated in 5.6 ("Ability to add Starter Content has been removed"), `GameProjectUtils::IsEngineStarterContentAvailable` returns false, and the install has no Starter Content pack.
- PQ33, PQ34: the lamp is now a small Blueprint the quest makes (BP_Lamp), not Blueprint_CeilingLight. PQ35: the explosions are now alarm lights the quest makes (BP_AlarmLight). text.
- CQ72: uses engine sounds and a bomb Blueprint the quest makes, because the First Person template has no projectile and no Starter Content sounds any more. local.
- TAQ55, TAQ56, TAQ57: rewritten without Starter Content materials and without the emitter of another quest; they use the default sprite material of Niagara or a simple smoke material the quest makes. local.
- PQ102: rewritten around Networking Insights. New title "Record a Networking Insights session" (was "Record a Network Profiler session"), new docs link (networking-insights-in-unreal-engine), all quiz questions rewritten. docs: Networking Insights; local: NetworkProfiler.exe is not in the 5.8 install.
- PQ104: rewritten around Unreal Insights traces. New title "Stat groups and a trace" (was "Stat groups and stat files"); quiz questions 4 to 6 replaced. local: the Session Frontend of 5.8 has the tabs Session Browser, Trace Control, Console, Automation and Screen Comparison, and no Profiler tab.
- PQ106: rewritten around the current way to extend the Gameplay Debugger (a class derived from FGameplayDebuggerCategory, registered in code with IGameplayDebugger). Quiz questions 3, 5, 6 and 7 replaced. local: GameplayDebugger module headers.
- PQ56: names the default Gameplay Debugger categories of 5.8. local.
- Template names (many animation quests, CQ48, AQ11, AQ17, AQ34, AQ61, AQ76, AQ84): the template Animation Blueprint is ABP_Unarmed (ABP_Manny and ABP_Quinn are given as the older names), the meshes are SKM_Manny_Simple and SKM_Quinn_Simple, the animation folder is Characters/Mannequins/Anims, the physics asset is PA_Mannequin in Characters/Mannequins/Rigs, and the foot IK rig is CR_Mannequin_FootIK. AQ11 quiz questions 2, 3 and 4 updated. local.
- AQ4, AQ33, CQ50: no longer say that the template may include the UE4 mannequin; a second skeleton comes from a free Fab character. local.
- GDQ30, GDQ37: now start from the First Person template with the Arena Shooter variant, because the plain First Person template has no weapon. GDQ37 uses BP_ShooterProjectileBase. GDQ47 (step and quiz question 6) and GDQ43 (step and quiz question 2) name the current Blueprints (BP_ShooterProjectileBase, BP_HorrorCharacter). local.

### Second pass: duplicates
- AQ84: was almost the same quest as AQ45 (thread safe Animation Blueprint and Fast Path). AQ45 stays. AQ84 is now about cheaper crowds: Update Rate Optimizations, fixed skeletal bounds and notifies. New title "Cheaper crowds: update rates and fixed bounds" (was "Thread-safe AnimBP and Fast Path"); quiz questions 2 to 6 replaced. docs: Animation Optimization.
- Looked at and left alone, because the angle or the specialization is different: LDQ89 and EAQ38, LDQ54 and EAQ112, LDQ104 and EAQ78, LDQ101 and EAQ109.

### Second pass: older info
- AQ12, AQ79, EAQ44, TAQ39: the import steps now follow the Interchange window (Interchange Pipeline Configuration) and say that older versions show FBX Import Options. Quiz questions updated in AQ79 (2, 4, 5, 7), EAQ44 (4, 5) and TAQ39 (1, 2). docs: Importing Assets Using Interchange, Interchange Import Reference; local: FBX import through Interchange is on by default in 5.8.
- TAQ38, TAQ40: import wording aligned with the same window. docs.
- TAQ97: the vehicle mesh now comes from the Vehicle template (SKM_SportsCar), not from an old sample project. local.
- LDQ120: the Collab Viewer template is in the 5.8 install, so the quest stays as it is. local.
- GDQ61: reworded so that it does not depend on the old replicator setup. known.
- EAQ3, EAQ87: the engine light profiles are offered next to a downloaded IES file. local.

### Second pass: things that could not be verified
- SQ15: the bad help post is now on the quest page; no pinned example in Discord. text.
- SQ16, SQ17: the steps and the proof no longer ask for a Discord post or link; you write what you did on the quest page. text. (The step checks still need a change, see "Still open".)
- GDQ7, LDQ40: no Critique-wanted tag and no #showcase post; the proof is sent on the quest page. Quiz questions that asked about the Discord tag were replaced (GDQ7 questions 4 and 5, LDQ40 question 2). text.
- SQ1: quiz question 1 no longer has a Discord channel as a choice, and question 5 no longer asks about a numbered rule in #welcome. text.
- LDQ27, LDQ31, LDQ34, EAQ35, AQ36, CQ29, CQ23, GDQ25, GDQ38, TAQ23, TAQ29, PQ19, PQ30: no zip files, no unnamed pages, no long videos; proof is screenshots or a short video clip (30 seconds or less) sent on the quest page. text.
- All proofs: "GIF" and "link to a video" wording replaced with "a short video clip (30 seconds or less)" or screenshots. text.

### Starter Quests
- SQ13: says where High Resolution Screenshot is (Viewport Options menu, top left of the viewport). docs: Taking Screenshots.

### Animation
- AQ28: menu item given as Animation Layer Interface, with the docs name (Animation Interface) next to it. known; the docs page (Animation Blueprint Linking) says Animation Interface.
- AQ31, TAQ96: Animation Modifiers renamed from the montage prefix AM_ to BP_FootSyncModifier and BP_BoneHeightCurveModifier. text; Epic's naming page lists AM_ for montages.
- AQ42: blend profile renamed from BP_LegsFast to Profile_LegsFast. text.
- AQ56: Gizmo Library / Gizmos / Gizmo Name are now Shape Libraries / Shapes / Shape Name, with the old names mentioned; asset renamed CRSL_Project; three quiz texts updated. known; the docs page (Control Shapes and Control Shape Library) still uses the Gizmo names.
- AQ62, AQ55 (quiz only): Setup Event is now Construction Event, old name mentioned. known; the docs page (Pose Caching) still says Setup Event.
- AQ71, AQ73, AQ75: "Windows >" is now "Window >", also in the quiz text. known.
- AQ79: example Skeleton is now SK_Mannequin (the UE5 name). known.
- AQ13, AQ21, AQ27: all three now say Enable Root Motion and explain that the panel writes it as EnableRootMotion. docs: Root Motion page uses "Enable Root Motion"; the panel label is known.
- AQ34: the four section names are written out in full. known.
- AQ43: step 4 now says what Always Update Source Pose does and what to note; proof no longer needs a clip. known.
- AQ66: step 4 now says where the settings are and how to find the right axis. known.
- AQ4: steps now follow the Retarget Animations window (Target Preview Mesh, Auto Generate Retargeter, Export Animations, Export Retarget Assets). docs: Auto Retargeting.
- AQ5: steps now give the clicks (Create, Control Rig; New Element, New Control; Get Control, Set Bone; Forwards Solve). docs: Control Rig Quick Start.
- AQ7, AQ8: steps now give the clicks for a Blend Space and an Aim Offset; proof is screenshots or a GIF. known.
- AQ3, AQ6, AQ35, AQ38: proof asked for a clip on a screenshot quest; now screenshots or a short GIF, with an optional video link. text.

### Cinematics
- CQ29, CQ55: Master Config is now Primary Config (old name mentioned once). known.
- CQ52: step 6 now tells you to create LS_Hair before you play it. text.
- CQ63: "Settings component" is now the Settings submenu of the Post Process Volume track. known.
- CQ44: app name is now Unreal VCam, like CQ30 and CQ46, with the older name mentioned. known; the docs page of the VCam component still says Live Link VCAM.
- CQ74: step 3 now explains Duration Type (Use Sound Duration, Use Duration Property), which the proof asks about. docs: Subtitles and Closed Captions plugin.
- CQ4, CQ5, CQ42: all three now say "the Camera button in the Sequencer toolbar". docs: Camera Cut Track.
- CQ48: its sequence is now LS_Outro, so it no longer shares the name LS_Intro with CQ42. text.
- CQ43: plugin path is now Edit > Plugins like the other quests; "Revert Axis Y" is correct and is now explained. docs: Gameplay Camera System Quick Start.
- CQ72: step 3 now lists every node and connection of the bomb sound; step 4 says how the Explode input is made. docs: MetaSounds Quick Start.
- CQ21: the extra step now gives the full click path for Resolve to Player Pawn. docs: Dynamic Binding in Sequencer.

### Gameplay design
- GDQ35: damage to an enemy now uses Apply Gameplay Effect to Target with Ability Target Data from Actor, and says the enemy needs an Ability System Component. known.
- GDQ39: step 4 no longer puts a streaming volume on a level that is also loaded by Blueprint; the key now unlocks the Blueprint streamer. text; the rule is on the Level Streaming Volumes page (it is in the quiz).
- GDQ40: "instance generator" is now Spawn Data Generators with an EQS SpawnPoints Generator. known.
- GDQ44: Can Crouch is now found under Nav Movement, then Movement Capabilities. known.
- GDQ47: the homing target is now set on BeginPlay with Set Homing Target Component. known.
- GDQ56: step 5 now gives the console command r.DebugSafeZone.TitleRatio. known; the current Safe Zones page does not list it.
- GDQ64: Gameplay Debugger key is now the apostrophe. docs: Using the Gameplay Debugger.
- GDQ79: the dynamic material instance is now put on the camera with Add or Update Blendable. known.
- GDQ85: the test now runs as Standalone Game with two players, because seamless travel does not work in a normal Play In Editor session. known.
- GDQ88: the character now registers itself with Add Game Framework Component Receiver. docs: Game Features and Modular Gameplay (the page shows the C++ call AddReceiver in BeginPlay; the Blueprint node name is known).
- GDQ9: step 2 now includes watching the AI use the Smart Object; proof is screenshots or a GIF. text.
- GDQ2: step 1 now explains the BoxSize variable and Set Box Extent. known.
- GDQ3, GDQ4, GDQ5, GDQ10: proof no longer needs a clip. text.
- GDQ77: Niagara system renamed to FXS_HitBurst. docs: Recommended Asset Naming Conventions.

### Level design
- LDQ62, LDQ111 (quiz explanation): Plugins window is now Edit > Plugins. text.
- LDQ63: no longer says to enable EQS in Project Settings; says it is on, and to enable Environment Query Editor only if the asset type is missing. docs: EQS Quick Start.
- LDQ68: Viewport Options described as the menu button at the top left (an arrow in older versions). docs: Taking Screenshots.
- LDQ74: the debug key is now in the character or Player Controller, which calls the Game Mode. known.
- LDQ76: the save is now loaded inside FindPlayerStart, because the Game Mode picks the start before BeginPlay. known.
- LDQ79: step 5 rewritten as an emergency stop with clear Timeline inputs. known.
- LDQ89, LDQ94: the steps now name the linked page to read. text.
- LDQ102: step 5 now names Create New Static Mesh Asset from Mesh and Copy Mesh to Static Mesh. known; the Lyra page does not name the nodes.
- LDQ34: the Behavior Tree option now points to the pages linked on the quest, not to a Discord channel; proof no longer needs a clip. text.
- LDQ23: steps now build a checkpoint and a kill zone that moves the player back, and explain why Kill Z alone is not enough; proof is screenshots. known.
- LDQ21, LDQ22, LDQ24, LDQ25, LDQ26: steps now give the Blueprint nodes and settings; clip proofs became screenshots or a GIF. known.
- LDQ29, LDQ37, LDQ38: proof no longer needs a clip. text.
- LDQ1, LDQ2, LDQ3, LDQ5, LDQ6, LDQ7, LDQ8, LDQ9, LDQ10: steps now say where to click. known.
- LDQ4: steps now give Create Level Instance, Edit and Commit Changes. docs: Level Instancing.
- LDQ18, LDQ19, LDQ20, LDQ29: old quest ids inside quiz text (LD-01, LD-02, LD-03, LD-08, WL-01, WL-03, BP-02 to BP-04) replaced with the current ids. text.

### Lookdev and lighting
- EAQ36: the shadow view is now Show, then Advanced, then Shadow Frustums. known. (Right Ctrl + L is correct. docs: Sky Atmosphere page.)
- EAQ57: each blend mode now gets its own copy of the material, so changing one no longer changes all four spheres. text.
- EAQ64: Build Texture Streaming is now in the Build menu of the main menu bar. known.
- EAQ68: menu name is now "Material", the same as EAQ71. docs: Using Material Parameter Collections.
- EAQ86, EAQ92: both now use the same option name (Fallback Relative Error, with a note that some versions show Relative Error). docs: Nanite Technical Details.
- EAQ113: window name is now Merge Actor Settings, the same as EAQ97. docs: Merging Actors.
- EAQ98: wall size is now 400 x 20 x 400, and the power-of-two option is tried and then turned off again, because the kit uses a grid of 100. text.
- EAQ99: step 4 now says what Stack and Transform do. docs: UVs category.
- EAQ101: step 5 now explains why the dirt texture should not be a power of two. docs: Bloom.
- EAQ105: the view is now named Temporal Upscaler I/O. docs: Temporal Super Resolution. (The labels TSR feed and TSR 1spp are correct.)
- EAQ14, EAQ17: "R1" replaced with "the earlier quests". text.
- EAQ30: step 2 now gives the full LUT workflow (neutral LUT image, ColorLookupTable texture group, Color Grading LUT). known.
- EAQ5, EAQ6, EAQ7, EAQ19, EAQ20, EAQ21, EAQ32, EAQ33: steps now say where to click and which nodes to use. known.
- EAQ34: steps now follow the Procedural Foliage page (enable it under Experimental, Static Mesh Foliage, Procedural Foliage Spawner, Resimulate). docs: Procedural Foliage Tool.
- EAQ89: Niagara system renamed to FXS_LowFog. docs: Recommended Asset Naming Conventions.

### Programming
- PQ46: step 2 now says how to repeat the shot with a timer; step 5 now says exactly how the bullet returns to the pool. known.
- PQ49: "New Plugin" is now the Add button that opens the New Plugin window; "Plugin Content" is now Show Plugin Content (also in the quiz). docs: Game Features page for the Add button; the setting name is known.
- PQ50: the page now says Revision Control with the old name next to it, and the button is in the bottom right corner. known; the docs page still says Source Control everywhere.
- PQ53: step 5 now gives a concrete example (a cast that is not needed). known.
- PQ55, PQ105: Visual Logger is now under Tools > Debug (also in the PQ55 quiz). known; GDQ64 already used this path.
- PQ57, PQ59: Blueprint Debugger is now opened from the Debug menu of the Blueprint Editor, or Tools > Debug. docs: Blueprint Debugger.
- PQ62: the crash is now caused with the console command debug crash, and the step says that a Blueprint mistake only gives Accessed None. known.
- PQ63: no longer asks for a default value on an Actor reference input. known.
- PQ43, PQ44, PQ65: key events in Actors now say to set Auto Receive Input to Player 0. known.
- PQ75: the pause setting is now Trigger When Paused on the Input Action asset, with the old node setting mentioned. known.
- PQ76: step 4 rewritten (where the portal is, what Options are, where to print them). known.
- PQ79: node names are now Make ItemRow and Break ItemRow. known.
- PQ87: the class is typed as WeaponDefinition and the step says Unreal adds the U. known.
- PQ92, TAQ6: Execute Python Script is now under Tools (also in the TAQ6 quiz). known; the docs page lists it under File.
- PQ107: step 3 now gives the argument -trace=default,memory. docs: Memory Insights.
- PQ5: steps now say where each setting is, and the proof now matches the steps. known.
- PQ6: steps now say where to start, stop and open a trace. known.
- PQ9, PQ14, PQ15, PQ16: goals rewritten as instructions; clip proofs became screenshots or a GIF. known.
- PQ20, PQ26, PQ27, PQ28: the steps now name the page (Coder 01, Coder 03, Coder 05, Blueprint vs. C++) that is linked on the quest. text.

### Tech art
- TAQ47: Sampler Type is now Masks. known.
- TAQ43: step 4 rewritten. known.
- TAQ18: names the linked page that has the blur code. text.
- TAQ1: proof now lists 7 views, with Lighting Only. text.
- TAQ99: step 3 now reads Tangent X and Tangent Z from the Skinned Mesh node. docs: How to Create a Custom Deformer Graph.
- TAQ82: menu is now Scripted Actor Actions, the same as TAQ88 and PQ52, with the docs name mentioned. known.
- TAQ97: plugin path is now Edit > Plugins; the sample is described with both Launcher tab names (Learn in the docs, Samples in newer Launchers). docs for Learn; Samples is known.
- TAQ95: Editing Tools is now opened in the Skeletal Mesh Editor. known.
- TAQ104: step 7 now also measures Epic (3), which the proof asks for. text.
- TAQ107: the comparison now switches between TSR and FXAA with r.AntiAliasingMethod; r.TemporalAA.Upsampling is only mentioned as the old command. known.
- TAQ103: step 5 now says to click the clock button to show durations. known.
- TAQ72: says Medium and Epic can stay empty and then use Default; gives the older menu location too. known.
- TAQ63: the category now comes from a Niagara Asset Tag Definitions asset and Manage Tags, which is what its own quiz says. docs (through the quiz facts from the Niagara Overview page).
- TAQ12, TAQ15, TAQ16, TAQ17, TAQ20, TAQ63, TAQ64, TAQ65, TAQ66, TAQ67, TAQ68, TAQ69: Niagara systems renamed from NS_ to FXS_, and the emitter asset in TAQ63 from NE_ to FXE_. docs: Recommended Asset Naming Conventions.

### Done by hand after the second pass
- SQ16, SQ17: the step check is now a text length check (`min_length: 120`), not a Discord link. text.
- Ten flavor lines no longer name another quest (AQ2, GDQ8, EAQ34, PQ93, PQ94, PQ25, PQ27, PQ28, SQ1, TAQ15). text.
- AQ12, AQ79, EAQ44, TAQ39: Epic's "Importing Assets Using Interchange" page added as extra reading. docs.
- Docs pages chosen for the 32 quests that had `discord://` or `TODO_URL` as their link (`update-0201.json`). Each page
  was fetched and exists. For quests about people skills (critique, review, help posts, playtests) no Epic page covers
  the topic, so the nearest useful page was chosen: Taking Screenshots, Playing and Simulating, Unreal Editor Interface.
  O1 to O5 are about this site and have no docs page on purpose. docs.

### Third pass (small fixes)
- 38 quests: steps over 100 words were split into shorter steps; nothing was removed. LDQ40 step 1 stays at 98 words
  because two of its steps carry a check, so the count could not change. text.
- LDQ20, LDQ28, LDQ30, LDQ32, LDQ40, SQ11, PQ17, GDQ6: quiz text no longer says "turn-in", uses rank numbers or names
  Discord. No answer moved. text.
- LDQ114, PQ52: now say Scripted Actor Actions, the name TAQ82 uses, with the older name mentioned once. text.
- PQ19: proof type changed from "package" to "screenshot" to match what the text asks for. text.

### Decided by the owner
- Similar quests in two specializations (LDQ115 and TAQ80, and the pairs noted above) are fine as they are.
- TAQ55 to TAQ60 keep the asset names of Epic's Niagara tutorial pages (FX_Smoke, SmokeSystem and so on), so a learner
  with the tutorial open sees the same names. Every other Niagara quest uses FXS_ and FXE_.
- Stand-ins for Starter Content stay as basic shapes and engine or template textures. No site asset pack.

## Checked, no change needed

- First pass only: the quest ids named on pages were checked and fitted. The second pass removed all quest ids from page and quiz text (see "Self-contained quests").
- O1 to O4, EAQ22, EAQ23, TAQ23, PQ18, LDQ27, PQ8, AQ23, AQ29, AQ36: the choices made in the rewording read correctly.
- CQ61: the console variables are right. docs: NFOR Denoiser.
- CQ30, CQ46: Unreal VCam is the current app name; only CQ44 was different.
- GDQ69: an Actor Blueprint reads its config values from the Engine ini files, so DefaultEngine.ini and WindowsEngine.ini are right. known.
- LDQ50: Lit > Visualizers > Layer Contribution is right. docs: Landscape Edit Layers.
- LDQ110: the quest says to enable Environment Query Editor "if it is not enabled yet", which is what the docs say. docs: EQS Quick Start.
- LDQ119: MPQ_ (Movie Pipeline Queue) is the same prefix CQ55 uses for a queue.
- EAQ53, EAQ91: the docs page itself uses Show > Visualize for HDR (Eye Adaptation) and Show > Visualization for Local Exposure. docs: Auto Exposure.
- EAQ58: the Refraction pin condition matches the docs. docs: Using Refraction.
- EAQ59: the steps already say "check whether" and "if Substrate is on", so they work with it on or off.
- EAQ71: the menu is "Material". docs: Using Material Parameter Collections.
- EAQ97: "Merge Actor Settings" is the name on the docs page. docs: Merging Actors.
- EAQ35: the reference now reads "quests EAQ25, EAQ26 and EAQ27", and those are the right quests.
- TAQ36: the two filter paths are two different features (show redirectors with other assets, or show only redirectors). docs: Asset Redirectors.
- TAQ60: the color R 0.1, G 0.3, B 50 is the value on the docs page. docs: particle lights how-to.
- TAQ88: already says Scripted Actor Actions.
- TAQ5, TAQ9: already use FXS_.
- PQ19: GDQ4 is also in the programming list, so the quest does not depend on another specialization. (Its proof is under "Needs an owner decision".)

## Still open

- Quests that still need something from outside a template, with the source named in the step: AQ4, AQ33, AQ36, AQ38, AQ68, CQ50, CQ51 (a free character from Fab, because the template has only one skeleton), AQ32 (Game Animation Sample), AQ77, CQ52, TAQ101, TAQ102 (a groom, from a MetaHuman or Fab), CQ49 (MetaHuman), CQ30, CQ44, CQ46, CQ77 (a phone or tablet), AQ54, TAQ98, TAQ100 (a 3D modeling program), TAQ103 (RenderDoc).
- GDQ37: the projectile Blueprint of the Arena Shooter variant (BP_ShooterProjectileBase) exists in 5.8, but its graph was not opened, so the step says to find its hit event or add Event Hit.
- TAQ17: the Niagara "new system" window differs between versions; the step still names New system from selected emitters.
- AQ28: could not confirm the exact menu label in the editor (Animation Layer Interface or Animation Interface). The page gives both.
- GDQ56: r.DebugSafeZone.TitleRatio comes from knowledge; the docs page does not list it any more.
- PQ50: the Revision Control menu names (Connect to Revision Control, Submit Content) come from knowledge; the Editor Preferences section name was not confirmed.
- PQ53: the cast example gives a warning or a note depending on the version; not confirmed which.
- PQ102, PQ104: where the Trace and Networking Insights menus sit in the editor (status bar, Unreal Insights window) comes from knowledge.
- TAQ99: the docs table names the kernel input "Tangent Y" while the graph reads Tangent Z. Step 4 still copies the docs table.
- TAQ58: the steps follow the docs page value for value, but they are still dense. Needs a pass in the engine.
- TAQ100: the steps are goals. The docs page (Panel Cloth Editor Overview) has no click paths or node names either.
- LDQ114, PQ52: these still say "Scripted Actions" in titles and intros. Only the menu name in TAQ82 was aligned.
- O1 (rules quiz) and one wrong choice in GDQ6 still name Discord channels. O1 is the quiz about the server rules, so this was left.

## Needs an owner decision


## Self-contained quests

Rule applied: a quest may need knowledge that is taught elsewhere, but no step may need an asset, a level, a Blueprint
or a project that only another quest creates. Every quest starts from a named Epic template (Blank, Third Person,
First Person, Top Down, Vehicle, or a named variant), from engine content, or from assets that the quest itself makes.
Where a step needed something built before, the quest now says "use your own, or make it like this" with the smallest
setup that works. Quest ids and phrases such as "as you did in" are gone from page and quiz text. Capstone quests list
what to build. Quiz questions that only made sense through another quest were replaced, with the right answer in the
same position.

- 718 of the 729 quests changed in the second pass. Almost all of them changed for this rule.
- 634 quests got a start line that names the template to open or create.
- 54 quests named another quest id in page or quiz text. Now none does.
- `quest_wording.py refs` listed 85 quests at the start. It now lists 10, all of them flavor lines (see "Still open").
- Quests where the setup is long, because the thing that was needed is large (an asset setup, not a lesson): AQ6, AQ8, AQ21, AQ27, AQ40, AQ71, AQ76, GDQ87, PQ8, EAQ20, EAQ76, EAQ80, and the capstones LDQ20, LDQ32, LDQ40, EAQ12, EAQ24, EAQ35, GDQ19, PQ19, TAQ9. GDQ57 and GDQ61 point to Epic's Behavior Tree Quick Start for the setup.
