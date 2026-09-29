"""Join-to-create voice rooms.

Joining ➕ Join to create in TOWN HALL makes a new room for you (with the hub's permissions)
and moves you in. You own it: rename it or set a user limit with the buttons in its chat, /room, or Discord's own
Edit Channel. A room with nobody in it for EMPTY_MINUTES is deleted. Rooms are remembered in kv so a restart
still cleans them up.
"""
from __future__ import annotations

import asyncio
import json
import logging

import discord
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("quartermaster.voice")

EMPTY_MINUTES = 5
# unlocks.yaml channel key → (hub name, room name prefix)
HUBS = {
    "studio_floor_voice": ("➕ Join to create", "🔊"),
}
OWNER_OW = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True, manage_channels=True,
                                       move_members=True)


class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._delete_tasks: dict[int, asyncio.Task] = {}
        self._locks: dict[int, asyncio.Lock] = {}

    # ------------------------------------------------------------------ state
    async def rooms(self) -> dict[int, int]:
        """room channel id → owner id"""
        raw = await self.bot.db.kv_get(0, "voice_rooms")
        return {int(k): int(v) for k, v in json.loads(raw or "{}").items()}

    async def _save(self, rooms: dict[int, int]) -> None:
        await self.bot.db.kv_set(0, "voice_rooms", json.dumps({str(k): v for k, v in rooms.items()}))

    def hub_for(self, channel_id: int) -> str | None:
        for key in HUBS:
            if channel_id and self.bot.unlocks.channel(key) == channel_id:
                return key
        return None

    # ------------------------------------------------------------------ create / delete
    async def create_room(self, member: discord.Member, hub: discord.VoiceChannel, key: str) -> None:
        lock = self._locks.setdefault(member.id, asyncio.Lock())
        async with lock:
            rooms = await self.rooms()
            # one room per person: send them back to the one they already own
            for cid, owner in rooms.items():
                if owner == member.id and (ch := member.guild.get_channel(cid)):
                    await member.move_to(ch)
                    return
            prefix = HUBS[key][1]
            overwrites = {**hub.overwrites, member: OWNER_OW}
            room = await member.guild.create_voice_channel(
                f"{prefix} {member.display_name}'s room"[:100], category=hub.category, overwrites=overwrites,
                position=hub.position + 1, reason=f"Voice room for {member}")
            rooms[room.id] = member.id
            await self._save(rooms)
            try:
                await member.move_to(room)
            except discord.HTTPException:
                pass                                   # they left before the move: the empty timer cleans up
            await self._post_controls(room, member)
            if not room.members:
                self._schedule_delete(room)

    async def _post_controls(self, room: discord.VoiceChannel, owner: discord.Member) -> None:
        e = discord.Embed(title="🔊 Your voice room", color=discord.Color.from_str("#3D7DD8"), description=(
            f"{owner.mention}, this room is yours.\n"
            "• **Rename** or set a **User limit** with the buttons below (or type `/room`).\n"
            f"• It is deleted when it has been empty for {EMPTY_MINUTES} minutes.\n"
            "• If you leave, the room passes to someone still inside."))
        v = discord.ui.View(timeout=None)
        v.add_item(RenameRoomButton())
        v.add_item(LimitRoomButton())
        try:
            await room.send(embed=e, view=v)
        except discord.HTTPException:
            log.warning("could not post controls in %s", room.id)

    def _schedule_delete(self, room: discord.VoiceChannel) -> None:
        if room.id in self._delete_tasks:
            return

        async def later():
            try:
                await asyncio.sleep(EMPTY_MINUTES * 60)
                ch = room.guild.get_channel(room.id)
                if ch and not ch.members:
                    await ch.delete(reason=f"Voice room empty for {EMPTY_MINUTES} minutes")
                    await self.forget(room.id)
            except discord.NotFound:
                await self.forget(room.id)
            except Exception:
                log.exception("voice room cleanup failed")
            finally:
                self._delete_tasks.pop(room.id, None)
        self._delete_tasks[room.id] = asyncio.create_task(later())

    def _cancel_delete(self, room_id: int) -> None:
        if (t := self._delete_tasks.pop(room_id, None)):
            t.cancel()

    async def forget(self, room_id: int) -> None:
        rooms = await self.rooms()
        if rooms.pop(room_id, None) is not None:
            await self._save(rooms)

    async def sweep(self, guild: discord.Guild) -> None:
        """After a restart: forget rooms that are gone, start the empty timer on empty ones."""
        rooms = await self.rooms()
        for cid in list(rooms):
            ch = guild.get_channel(cid)
            if ch is None:
                rooms.pop(cid)
            elif not ch.members:
                self._schedule_delete(ch)
        await self._save(rooms)

    # ------------------------------------------------------------------ events
    @commands.Cog.listener()
    async def on_ready(self):
        if (g := self.bot.get_guild(self.bot.settings.guild_id)):
            await self.sweep(g)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before, after):
        if before.channel == after.channel:
            return
        try:
            rooms = await self.rooms()
            if after.channel and not member.bot:
                if after.channel.id in rooms:
                    self._cancel_delete(after.channel.id)
                elif (key := self.hub_for(after.channel.id)):
                    await self.create_room(member, after.channel, key)
            if before.channel and before.channel.id in rooms:
                room = before.channel
                if not room.members:
                    self._schedule_delete(room)
                elif rooms[room.id] == member.id:
                    await self._hand_over(room, member, rooms)
        except Exception:
            log.exception("voice state update failed")

    async def _hand_over(self, room: discord.VoiceChannel, old: discord.Member, rooms: dict[int, int]) -> None:
        new = next((m for m in room.members if not m.bot), None)
        if not new:
            return
        await room.set_permissions(old, overwrite=None)
        await room.set_permissions(new, overwrite=OWNER_OW)
        rooms[room.id] = new.id
        await self._save(rooms)
        try:
            await room.send(f"👑 {new.mention} owns this room now.")
        except discord.HTTPException:
            pass

    # ------------------------------------------------------------------ owner actions
    async def owned_room(self, itx: discord.Interaction) -> discord.VoiceChannel | None:
        rooms = await self.rooms()
        ch = itx.channel if isinstance(itx.channel, discord.VoiceChannel) and itx.channel.id in rooms else None
        if ch is None:
            v = itx.user.voice.channel if isinstance(itx.user, discord.Member) and itx.user.voice else None
            ch = v if v and v.id in rooms else None
        if ch is None:
            await itx.response.send_message("Join a voice room first. Join ➕ Join to create in TOWN HALL "
                                            "to make one.", ephemeral=True)
            return None
        if rooms[ch.id] != itx.user.id and not itx.user.guild_permissions.manage_channels:
            await itx.response.send_message(f"Only <@{rooms[ch.id]}> can change this room.", ephemeral=True)
            return None
        return ch

    async def rename(self, itx: discord.Interaction, room: discord.VoiceChannel, name: str) -> None:
        name = name.strip()[:100]
        if not name:
            await itx.response.send_message("The name can't be empty.", ephemeral=True)
            return
        await itx.response.send_message(f"Renaming to **{name}**…\nDiscord allows 2 renames every 10 minutes, "
                                        "so it may take a moment.", ephemeral=True)
        await room.edit(name=name, reason=f"Renamed by {itx.user}")
        await itx.edit_original_response(content=f"✅ Renamed to **{name}**.")

    async def set_limit(self, itx: discord.Interaction, room: discord.VoiceChannel, limit: int) -> None:
        limit = max(0, min(99, limit))
        await room.edit(user_limit=limit, reason=f"Limit set by {itx.user}")
        await itx.response.send_message(f"✅ User limit: **{limit or 'none'}**.", ephemeral=True)

    room = app_commands.Group(name="room", description="Change the voice room you own.")

    @room.command(name="rename", description="Rename your voice room.")
    async def room_rename(self, itx: discord.Interaction, name: app_commands.Range[str, 1, 100]):
        if (ch := await self.owned_room(itx)):
            await self.rename(itx, ch, name)

    @room.command(name="limit", description="Set how many people can join your voice room (0 = no limit).")
    async def room_limit(self, itx: discord.Interaction, limit: app_commands.Range[int, 0, 99]):
        if (ch := await self.owned_room(itx)):
            await self.set_limit(itx, ch, limit)


class RenameModal(discord.ui.Modal, title="Rename your room"):
    name = discord.ui.TextInput(label="New name", max_length=100, placeholder="e.g. Blockout jam")

    def __init__(self, room: discord.VoiceChannel):
        super().__init__()
        self.room = room

    async def on_submit(self, itx: discord.Interaction):
        await itx.client.get_cog("Voice").rename(itx, self.room, str(self.name.value))


class LimitModal(discord.ui.Modal, title="User limit"):
    limit = discord.ui.TextInput(label="How many people? (0 = no limit)", max_length=2, placeholder="4")

    def __init__(self, room: discord.VoiceChannel):
        super().__init__()
        self.room = room

    async def on_submit(self, itx: discord.Interaction):
        v = str(self.limit.value).strip()
        if not v.isdigit():
            await itx.response.send_message("Type a number from 0 to 99.", ephemeral=True)
            return
        await itx.client.get_cog("Voice").set_limit(itx, self.room, int(v))


class RenameRoomButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uc:vroom:rename"):
    def __init__(self):
        super().__init__(discord.ui.Button(label="Rename", emoji="✏️", style=discord.ButtonStyle.primary,
                                           custom_id="uc:vroom:rename"))

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls()

    async def callback(self, itx: discord.Interaction):
        if (ch := await itx.client.get_cog("Voice").owned_room(itx)):
            await itx.response.send_modal(RenameModal(ch))


class LimitRoomButton(discord.ui.DynamicItem[discord.ui.Button], template=r"uc:vroom:limit"):
    def __init__(self):
        super().__init__(discord.ui.Button(label="User limit", emoji="👥", style=discord.ButtonStyle.secondary,
                                           custom_id="uc:vroom:limit"))

    @classmethod
    async def from_custom_id(cls, itx, item, match):
        return cls()

    async def callback(self, itx: discord.Interaction):
        if (ch := await itx.client.get_cog("Voice").owned_room(itx)):
            await itx.response.send_modal(LimitModal(ch))


async def setup(bot):
    bot.add_dynamic_items(RenameRoomButton, LimitRoomButton)
    await bot.add_cog(Voice(bot))
