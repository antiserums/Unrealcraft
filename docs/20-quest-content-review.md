# Quest content review

Checked on 2026-10-01 against Epic's documentation for Unreal Engine 5.8 (dev.epicgames.com).
The first version of this file was a list of suspicions. Each one has now been checked and sorted into one of four lists.

All fixes are in `tools/quest_wording/update-0001.json` to `update-0008.json` and were put into the curriculum with
`tools/quest_wording.py apply`. Only page text changed (intro, steps, "done when", and a few names inside quiz text).
Nothing was tested inside the engine.

How to read the source of a fix:

- **docs** = confirmed on the named Epic documentation page for 5.8.
- **known** = changed from knowledge of UE5, with no docs page that confirms it. Where the docs page still shows an
  older name, the quest now gives both names.
- **text** = a fix inside the quest set (names that did not match, proof that could not be sent, a missing step).

## Fixed

### Starter Quests
- SQ13: says where High Resolution Screenshot is (Viewport Options menu, top left of the viewport). docs: Taking Screenshots.
- SQ15: still points to the pinned example, but gives a fallback bad post to rewrite if it is missing. text.

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
- GDQ7, LDQ40: both now say "Critique-wanted post in #showcase"; "/critique" is gone. LDQ40 also says "A mentor reviews your work" and asks for a video link plus screenshots. text.
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
- LDQ28: now uses L_MetricsGym from LDQ11. text.
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
- TAQ55, TAQ57: "the sprite smoke quest" is now quest TAQ56; TAQ55 says the two materials are in the Starter Content. text; the material location is known.
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

## Checked, no change needed

- Choices made during the rewording: the id mapping fits. LDQ13 points to LDQ11 (metrics gym). LDQ18 points to EAQ10 (locked exposure) and LDQ17 (bookmarks). LDQ20 points to LDQ11, LDQ14, LDQ15, LDQ16, LDQ17, LDQ18 and EAQ10. LDQ27 and LDQ32 point to GDQ2 to GDQ4, LDQ27, LDQ28, LDQ29 and LDQ31. LDQ29 and GDQ3 point to GDQ2 and GDQ3. Every quest id named on a page exists.
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

- AQ79, EAQ44, TAQ39: the 5.8 docs pages still describe the FBX Import Options dialog. Newer engine versions import FBX through Interchange, which shows a different dialog with other option names. Not confirmed which dialog a learner sees in 5.8.
- AQ28: could not confirm the exact menu label in the editor (Animation Layer Interface or Animation Interface). The page now gives both.
- GDQ61: the steps match the 5.8 docs page (Debug AI show flag, GameplayDebuggingReplicator), but that page looks like old content. Needs a test in the engine.
- GDQ56: r.DebugSafeZone.TitleRatio comes from knowledge; the docs page does not list it any more.
- LDQ120: the Collab Viewer template still has docs pages for 5.8, but it was not confirmed that the template ships with the current engine.
- PQ102: the docs page for the standalone Network Profiler still exists, but it was not confirmed that NetworkProfiler.exe ships with the current engine. Networking Insights is the newer tool.
- PQ50: the Revision Control menu names (Connect to Revision Control, Submit Content) come from knowledge; the Editor Preferences section name was not confirmed.
- PQ53: the cast example gives a warning or a note depending on the version; not confirmed which.
- TAQ99: the docs table names the kernel input "Tangent Y" while the graph reads Tangent Z. Step 4 still copies the docs table.
- TAQ58: the steps follow the docs page value for value, but they are still dense. Needs a pass in the engine.
- TAQ100: the steps are goals. The docs page (Panel Cloth Editor Overview) has no click paths or node names either, so they could not be written out.
- TAQ97: where the Vehicle Game sample is today (Launcher Samples tab or Fab) was not confirmed.
- LDQ114, PQ52: these still say "Scripted Actions" in titles and intros. Only the menu name in TAQ82 was aligned.
- Quiz text that still uses ranks or "turn-in": LDQ20, LDQ28, LDQ30, LDQ32, LDQ40, SQ11, PQ17. Quiz wording was not restyled.
- Screenshot quests whose proof says "a short clip or screenshots": AQ15, AQ20, AQ24, AQ27, AQ65, AQ76, CQ8, CQ30, CQ66, GDQ52, LDQ53, LDQ79, LDQ109, SQ9. They can be done with screenshots, so they were left as they are.

## Needs an owner decision

- AQ84 and AQ45: almost the same quest (thread safe Animation Blueprint and Fast Path). Keep both, merge, or change one?
- SQ16, SQ17: the proof is a Discord link, but work is reviewed on the site. Is that intended?
- SQ14: asks for a video file (its step has a video check), but uploads accept images only. Allow video for this quest, or change the quest?
- PQ19: proof type is "package" and asks for a zip file or a clip. How should a build be sent?
- Mentor and writeup quests that ask for a video or a zip file (AQ17, AQ23, AQ29, AQ32, AQ36, CQ15, CQ23, CQ48, GDQ19, GDQ25, GDQ32, GDQ38, LDQ32, TAQ23, TAQ29): should these become "paste a link to a video"?
- PQ104: built on the Session Frontend Profiler and .uestats files, which Unreal Insights replaced. The correct quiz answer is the old tool. Rewrite the quest and quiz around Unreal Insights, or retire it?
- PQ106: built on the UE4 way to extend the Gameplay Debugger (component and HUD component classes registered in the ini file). UE5 uses a different system (a category class registered in code). Rewrite the quest and quiz, or retire it?
- GDQ7, LDQ40, SQ15: they depend on things in Discord (a Critique-wanted tag in #showcase, a template and a pinned bad example in #help-desk). Do these exist on the server?
- TAQ55 needs the emitter from TAQ56, which has a higher number. Swap the order, or add a prerequisite?
- TAQ55 to TAQ60: emitter and system names (FX_Smoke, SmokeSystem, BeamSystem and so on) follow Epic's tutorial pages word for word and not the FXS_ / FXE_ convention. Rename them, or keep them the same as the tutorials?
- AQ79, EAQ44, TAQ39: if the site should teach the Interchange import dialog and not the FBX Import Options dialog, these three quests and their quizzes need a rewrite.
