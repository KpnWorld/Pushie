from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable

import discord
from discord import app_commands
from discord.ext import commands

from emojis import Emoji
from storage import GuildData
from ui import UI, BaseView

if TYPE_CHECKING:
    from main import Pushie

log = logging.getLogger(__name__)

MUTE_DENY = discord.PermissionOverwrite(send_messages=False)
IMUTE_DENY = discord.PermissionOverwrite(attach_files=False, embed_links=False)
RMUTE_DENY = discord.PermissionOverwrite(add_reactions=False, use_external_emojis=False)
JAIL_ALLOW = discord.PermissionOverwrite(read_messages=True, send_messages=True)
JAIL_DENY = discord.PermissionOverwrite(read_messages=False)


def _fmt_channel(channel_id: int | None) -> str:
    return f"<#{channel_id}>" if channel_id else "*not set*"


def _fmt_role(role_id: int | None, guild: discord.Guild) -> str:
    if not role_id:
        return "*not set*"
    role = guild.get_role(role_id)
    return role.mention if role else f"*deleted role {role_id}*"


def _status(value: bool) -> str:
    return f"`{Emoji.SUCCESS}` enabled" if value else f"`{Emoji.CANCEL}` disabled"


def _build_summary(g_data: GuildData, guild: discord.Guild) -> discord.Embed:
    lines = [
        f"> `{Emoji.WELCOME}` **Welcome**",
        f"> channel — {_fmt_channel(g_data.welcome_channel)}",
        f"> member role — {_fmt_role(g_data.welcome_role, guild)}",
        f"> bot role — {_fmt_role(g_data.welcome_role_bot, guild)}",
        "",
        f"> `{Emoji.JAIL}` **Jail**",
        f"> channel — {_fmt_channel(g_data.jail_channel)}",
        f"> role — {_fmt_role(g_data.jail_role, guild)}",
        "",
        f"> `{Emoji.LOCK}` **Bot protection** — {_status(g_data.bot_lock)}",
        "",
        f"> `{Emoji.MUTE}` **Mute roles**",
        f"> mute (msg) — {_fmt_role(g_data.mute_role, guild)}",
        f"> imute (img) — {_fmt_role(g_data.imute_role, guild)}",
        f"> rmute (react) — {_fmt_role(g_data.rmute_role, guild)}",
    ]
    return discord.Embed(
        title=f"{Emoji.SETUP} Server Setup",
        description="\n".join(lines),
        color=0xFAB9EC,
    ).set_footer(text="Use the buttons below to configure each section.")


class _DisableModal(discord.ui.Modal, title="Disable"):
    confirm = discord.ui.TextInput(
        label='Type "disable" to confirm',
        placeholder="disable",
        max_length=10,
    )

    def __init__(self, field: str, label: str) -> None:
        super().__init__(title=f"Disable {label}")
        self._field = field
        self.confirmed = False

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if self.confirm.value.strip().lower() == "disable":
            self.confirmed = True
        await interaction.response.defer()
        self.stop()


@runtime_checkable
class _SubView(Protocol):
    parent: "SetupView"
    invoker: discord.Member

    def _embed(self) -> discord.Embed: ...


class _WelcomeView(BaseView):
    def __init__(self, parent: SetupView) -> None:
        super().__init__(parent.invoker, timeout=120)
        self.parent = parent
        self.invoker = parent.invoker

    def _embed(self) -> discord.Embed:
        g = self.parent.gdata
        guild = self.parent.guild
        return discord.Embed(
            title=f"{Emoji.WELCOME} Welcome Setup",
            description=(
                f"> channel — {_fmt_channel(g.welcome_channel)}\n"
                f"> member role — {_fmt_role(g.welcome_role, guild)}\n"
                f"> bot role — {_fmt_role(g.welcome_role_bot, guild)}"
            ),
            color=0xFAB9EC,
        )

    @discord.ui.button(
        label="Set Channel",
        emoji=Emoji.CHANNEL,
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def set_channel(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        view = _ChannelSelectView(self, "welcome_channel", "Welcome Channel")
        await inter.response.edit_message(embed=view._embed(), view=view)

    @discord.ui.button(
        label=Emoji.CANCEL + " Disable Welcome",
        style=discord.ButtonStyle.danger,
        row=0,
    )
    async def disable_welcome(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        modal = _DisableModal("welcome_channel", "Welcome")
        await inter.response.send_modal(modal)
        await modal.wait()
        if modal.confirmed:
            await self.parent.bot.storage.update_setup(
                self.parent.guild.id, welcome_channel=None
            )
            await self.parent._reload_gdata()
        await self.parent._redraw()

    @discord.ui.button(
        label="Member Autorole",
        emoji=Emoji.ROLE,
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def set_member_role(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        view = _RoleSelectView(self, "welcome_role", "Member Autorole")
        await inter.response.edit_message(embed=view._embed(), view=view)

    @discord.ui.button(
        label="Bot Autorole",
        emoji=Emoji.ROLE,
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def set_bot_role(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        view = _RoleSelectView(self, "welcome_role_bot", "Bot Autorole")
        await inter.response.edit_message(embed=view._embed(), view=view)

    @discord.ui.button(
        label=Emoji.PREV + " Back", style=discord.ButtonStyle.grey, row=2
    )
    async def go_back(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        await self.parent._redraw(inter)


class _JailView(BaseView):
    def __init__(self, parent: SetupView) -> None:
        super().__init__(parent.invoker, timeout=120)
        self.parent = parent
        self.invoker = parent.invoker

    def _embed(self) -> discord.Embed:
        g = self.parent.gdata
        guild = self.parent.guild
        return discord.Embed(
            title=f"{Emoji.JAIL} Jail Setup",
            description=(
                f"> channel — {_fmt_channel(g.jail_channel)}\n"
                f"> role — {_fmt_role(g.jail_role, guild)}"
            ),
            color=0xFAB9EC,
        )

    @discord.ui.button(
        label="Set Channel",
        emoji=Emoji.CHANNEL,
        style=discord.ButtonStyle.primary,
        row=0,
    )
    async def set_channel(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        view = _ChannelSelectView(self, "jail_channel", "Jail Channel")
        await inter.response.edit_message(embed=view._embed(), view=view)

    @discord.ui.button(
        label="Create Jail Channel",
        emoji=Emoji.JAIL,
        style=discord.ButtonStyle.success,
        row=0,
    )
    async def create_jail(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await inter.response.defer()
        guild = self.parent.guild
        g = self.parent.gdata

        overwrites: dict[
            discord.Role | discord.Member | discord.Object, discord.PermissionOverwrite
        ] = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        jail_role = guild.get_role(g.jail_role) if g.jail_role else None
        if jail_role:
            overwrites[jail_role] = JAIL_ALLOW

        jail_ch = await guild.create_text_channel(
            "jail",
            overwrites=overwrites,
            topic="Jailed members are sent here.",
            reason="Pushie setup — jail channel created",
        )
        await self.parent.bot.storage.update_setup(guild.id, jail_channel=jail_ch.id)
        await self.parent._reload_gdata()
        await inter.edit_original_response(embed=self._embed(), view=self)

    @discord.ui.button(
        label="Create Jail Role",
        emoji=Emoji.ROLE,
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def create_jail_role(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await inter.response.defer()
        guild = self.parent.guild
        role = await guild.create_role(
            name="Jailed",
            color=discord.Color.dark_gray(),
            reason="Pushie setup — jail role created",
        )
        await self.parent.bot.storage.update_setup(guild.id, jail_role=role.id)
        await self.parent._reload_gdata()
        await inter.edit_original_response(embed=self._embed(), view=self)

    @discord.ui.button(
        label="Set Jail Role",
        emoji=Emoji.ROLE,
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def set_jail_role(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        view = _RoleSelectView(self, "jail_role", "Jail Role")
        await inter.response.edit_message(embed=view._embed(), view=view)

    @discord.ui.button(
        label=Emoji.CANCEL + " Disable Jail",
        style=discord.ButtonStyle.danger,
        row=2,
    )
    async def disable_jail(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        modal = _DisableModal("jail_channel", "Jail")
        await inter.response.send_modal(modal)
        await modal.wait()
        if modal.confirmed:
            await self.parent.bot.storage.update_setup(
                self.parent.guild.id, jail_channel=None
            )
            await self.parent._reload_gdata()
        await self.parent._redraw()

    @discord.ui.button(
        label=Emoji.PREV + " Back", style=discord.ButtonStyle.grey, row=2
    )
    async def go_back(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        await self.parent._redraw(inter)


class _MuteView(BaseView):
    def __init__(self, parent: SetupView) -> None:
        super().__init__(parent.invoker, timeout=120)
        self.parent = parent
        self.invoker = parent.invoker

    def _embed(self) -> discord.Embed:
        g = self.parent.gdata
        guild = self.parent.guild
        return discord.Embed(
            title=f"{Emoji.MUTE} Mute Roles Setup",
            description=(
                f"> `{Emoji.MUTE}` mute (msg) — {_fmt_role(g.mute_role, guild)}\n"
                f"> `{Emoji.IMUTE}` imute (img) — {_fmt_role(g.imute_role, guild)}\n"
                f"> `{Emoji.RMUTE}` rmute (react) — {_fmt_role(g.rmute_role, guild)}\n\n"
                f"*Creating roles will override channel perms in every category.*"
            ),
            color=0xFAB9EC,
        )

    async def _create_mute_role(
        self,
        inter: discord.Interaction,
        field: str,
        name: str,
        overwrite: discord.PermissionOverwrite,
    ) -> None:
        await inter.response.defer()
        guild = self.parent.guild
        role = await guild.create_role(
            name=name,
            color=discord.Color.dark_gray(),
            reason=f"Pushie setup — {name} role created",
        )
        await self.parent.bot.storage.update_setup(guild.id, **{field: role.id})
        await _apply_role_overwrite(guild, role, overwrite)
        await self.parent._reload_gdata()
        await inter.edit_original_response(embed=self._embed(), view=self)

    @discord.ui.button(
        label="Create Mute Role",
        emoji=Emoji.MUTE,
        style=discord.ButtonStyle.success,
        row=0,
    )
    async def create_mute(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await self._create_mute_role(inter, "mute_role", "Muted", MUTE_DENY)

    @discord.ui.button(
        label="Set Mute Role",
        emoji=Emoji.ROLE,
        style=discord.ButtonStyle.secondary,
        row=0,
    )
    async def set_mute(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        view = _RoleSelectView(self, "mute_role", "Mute Role")
        await inter.response.edit_message(embed=view._embed(), view=view)

    @discord.ui.button(
        label="Create iMute Role",
        emoji=Emoji.IMUTE,
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def create_imute(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await self._create_mute_role(inter, "imute_role", "iMuted", IMUTE_DENY)

    @discord.ui.button(
        label="Set iMute Role",
        emoji=Emoji.ROLE,
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def set_imute(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        view = _RoleSelectView(self, "imute_role", "Image Mute Role")
        await inter.response.edit_message(embed=view._embed(), view=view)

    @discord.ui.button(
        label="Create rMute Role",
        emoji=Emoji.RMUTE,
        style=discord.ButtonStyle.success,
        row=2,
    )
    async def create_rmute(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        await self._create_mute_role(inter, "rmute_role", "rMuted", RMUTE_DENY)

    @discord.ui.button(
        label="Set rMute Role",
        emoji=Emoji.ROLE,
        style=discord.ButtonStyle.secondary,
        row=2,
    )
    async def set_rmute(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        view = _RoleSelectView(self, "rmute_role", "Reaction Mute Role")
        await inter.response.edit_message(embed=view._embed(), view=view)

    @discord.ui.button(
        label=Emoji.PREV + " Back", style=discord.ButtonStyle.grey, row=3
    )
    async def go_back(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        await self.parent._redraw(inter)


class _ChannelSelectView(BaseView):
    def __init__(self, parent_view: _SubView, field: str, label: str) -> None:
        super().__init__(parent_view.invoker, timeout=60)
        self._parent: _SubView = parent_view
        self._field = field
        self._label = label
        select: discord.ui.ChannelSelect[_ChannelSelectView] = discord.ui.ChannelSelect(
            placeholder=f"Pick the {label}...",
            channel_types=[discord.ChannelType.text],
        )
        select.callback = self._on_select
        self.add_item(select)
        self._select = select

    def _embed(self) -> discord.Embed:
        return discord.Embed(
            description=f"> `{Emoji.CHANNEL}` *Select a channel for **{self._label}**.*",
            color=0xFAB9EC,
        )

    async def _on_select(self, interaction: discord.Interaction) -> None:
        channel = self._select.values[0]
        setup_view = self._parent.parent
        await interaction.response.defer()
        await setup_view.bot.storage.update_setup(
            setup_view.guild.id, **{self._field: channel.id}
        )
        await setup_view._reload_gdata()
        await interaction.edit_original_response(
            embed=self._parent._embed(), view=cast(BaseView, self._parent)
        )

    @discord.ui.button(
        label=Emoji.CANCEL + " Cancel", style=discord.ButtonStyle.grey
    )
    async def cancel(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        await inter.response.edit_message(
            embed=self._parent._embed(), view=cast(BaseView, self._parent)
        )


class _RoleSelectView(BaseView):
    def __init__(self, parent_view: _SubView, field: str, label: str) -> None:
        super().__init__(parent_view.invoker, timeout=60)
        self._parent: _SubView = parent_view
        self._field = field
        self._label = label
        select: discord.ui.RoleSelect[_RoleSelectView] = discord.ui.RoleSelect(
            placeholder=f"Pick the {label}..."
        )
        select.callback = self._on_select
        self.add_item(select)
        self._select = select

    def _embed(self) -> discord.Embed:
        return discord.Embed(
            description=f"> `{Emoji.ROLE}` *Select a role for **{self._label}**.*",
            color=0xFAB9EC,
        )

    async def _on_select(self, interaction: discord.Interaction) -> None:
        role = self._select.values[0]
        setup_view = self._parent.parent
        await interaction.response.defer()
        await setup_view.bot.storage.update_setup(
            setup_view.guild.id, **{self._field: role.id}
        )
        await setup_view._reload_gdata()
        await interaction.edit_original_response(
            embed=self._parent._embed(), view=cast(BaseView, self._parent)
        )

    @discord.ui.button(
        label=Emoji.CANCEL + " Cancel", style=discord.ButtonStyle.grey
    )
    async def cancel(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        await inter.response.edit_message(
            embed=self._parent._embed(), view=cast(BaseView, self._parent)
        )


class SetupView(BaseView):
    def __init__(
        self,
        bot: "Pushie",
        invoker: discord.Member,
        guild: discord.Guild,
        gdata: GuildData,
    ) -> None:
        super().__init__(invoker, timeout=300)
        self.bot = bot
        self.invoker = invoker
        self.guild = guild
        self.gdata: GuildData = gdata

    async def _reload_gdata(self) -> None:
        self.gdata = await self.bot.storage.get_guild(self.guild.id)

    async def _redraw(self, inter: discord.Interaction | None = None) -> None:
        await self._reload_gdata()
        embed = _build_summary(self.gdata, self.guild)
        # Prefer using the stored message to avoid stale interactions
        if self.message:
            await self.message.edit(embed=embed, view=self)
        elif inter:
            await inter.edit_original_response(embed=embed, view=self)

    @discord.ui.button(
        label="Welcome", emoji=Emoji.WELCOME, style=discord.ButtonStyle.primary, row=0
    )
    async def btn_welcome(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        sub = _WelcomeView(self)
        await inter.response.edit_message(embed=sub._embed(), view=sub)

    @discord.ui.button(
        label="Jail", emoji=Emoji.JAIL, style=discord.ButtonStyle.primary, row=0
    )
    async def btn_jail(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        sub = _JailView(self)
        await inter.response.edit_message(embed=sub._embed(), view=sub)

    @discord.ui.button(
        label="Mute Roles", emoji=Emoji.MUTE, style=discord.ButtonStyle.primary, row=0
    )
    async def btn_mute(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        sub = _MuteView(self)
        await inter.response.edit_message(embed=sub._embed(), view=sub)

    @discord.ui.button(
        label="Bot Protection",
        emoji=Emoji.LOCK,
        style=discord.ButtonStyle.secondary,
        row=1,
    )
    async def btn_bot_protection(
        self, inter: discord.Interaction, _: discord.ui.Button
    ) -> None:
        new_val = not self.gdata.bot_lock
        await inter.response.defer()
        await self.bot.storage.update_setup(self.guild.id, bot_lock=new_val)
        await self._reload_gdata()
        await inter.edit_original_response(
            embed=_build_summary(self.gdata, self.guild), view=self
        )

    @discord.ui.button(
        label="Done", emoji=Emoji.SUCCESS, style=discord.ButtonStyle.success, row=2
    )
    async def btn_done(self, inter: discord.Interaction, _: discord.ui.Button) -> None:
        self._disable_all()
        await inter.response.edit_message(
            embed=UI.success("Setup saved! Use `/setup sync` to apply perm overrides."),
            view=self,
        )
        self.stop()


async def _apply_role_overwrite(
    guild: discord.Guild,
    role: discord.Role,
    overwrite: discord.PermissionOverwrite,
) -> None:
    tasks = []
    for channel in guild.channels:
        if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
            tasks.append(
                channel.set_permissions(
                    role, overwrite=overwrite, reason="Pushie /setup sync"
                )
            )
    for i in range(0, len(tasks), 5):
        await asyncio.gather(*tasks[i : i + 5])
        await asyncio.sleep(0.5)


async def _sync_all(guild: discord.Guild, gdata: GuildData) -> dict[str, int]:
    counts: dict[str, int] = {}

    role_map = {
        "mute_role": ("Muted", MUTE_DENY),
        "imute_role": ("iMuted", IMUTE_DENY),
        "rmute_role": ("rMuted", RMUTE_DENY),
    }

    for field, (name, overwrite) in role_map.items():
        role_id: int | None = getattr(gdata, field)
        if not role_id:
            continue
        role = guild.get_role(role_id)
        if not role:
            continue
        await _apply_role_overwrite(guild, role, overwrite)
        counts[name] = len(guild.channels)

    if gdata.jail_channel:
        jail_ch = guild.get_channel(gdata.jail_channel)
        if isinstance(jail_ch, discord.TextChannel):
            await jail_ch.set_permissions(
                guild.default_role, read_messages=False, reason="Pushie /setup sync"
            )
            if gdata.jail_role:
                jail_role = guild.get_role(gdata.jail_role)
                if jail_role:
                    await jail_ch.set_permissions(
                        jail_role, overwrite=JAIL_ALLOW, reason="Pushie /setup sync"
                    )
            counts["jail"] = 1

    return counts


class Setup(commands.Cog):
    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    async def _can_setup(self, inter: discord.Interaction) -> bool:
        if not inter.guild or not isinstance(inter.user, discord.Member):
            await inter.response.send_message(
                embed=UI.error("This command can only be used in a server."),
                ephemeral=True,
            )
            return False
        if inter.user.guild_permissions.manage_guild or self.bot.storage.is_sudo(
            inter.user.id
        ):
            return True
        await inter.response.send_message(
            embed=UI.error("You need **Manage Server** permission."), ephemeral=True
        )
        return False

    @app_commands.command(
        name="setup", description="Open the interactive server setup wizard"
    )
    @app_commands.guild_only()
    async def setup_cmd(self, inter: discord.Interaction) -> None:
        if not await self._can_setup(inter):
            return
        # Defer immediately before any async operations
        await inter.response.defer(ephemeral=True)
        gdata = await self.bot.storage.get_guild(inter.guild.id)  # type: ignore[union-attr]
        view = SetupView(self.bot, inter.user, inter.guild, gdata)  # type: ignore[arg-type]
        await inter.edit_original_response(
            embed=_build_summary(gdata, inter.guild),  # type: ignore[arg-type]
            view=view,
        )
        view.message = await inter.original_response()

    @app_commands.command(
        name="setup-sync",
        description="Re-apply all mute/jail permission overrides to every channel",
    )
    @app_commands.guild_only()
    async def setup_sync(self, inter: discord.Interaction) -> None:
        if not await self._can_setup(inter):
            return
        await inter.response.defer(ephemeral=True)
        gdata = await self.bot.storage.get_guild(inter.guild.id)  # type: ignore[union-attr]
        counts = await _sync_all(inter.guild, gdata)  # type: ignore[arg-type]

        if not counts:
            await inter.followup.send(
                embed=UI.warning(
                    "*No mute or jail roles are configured. Nothing to sync.*"
                ),
                ephemeral=True,
            )
            return

        lines = "\n".join(
            f"> `{Emoji.SYNC}` *{name}* — {n} channel(s)" for name, n in counts.items()
        )
        await inter.followup.send(
            embed=UI.success(f"Sync complete!\n{lines}"),
            ephemeral=True,
        )


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Setup(bot))
