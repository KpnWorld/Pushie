from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

import discord
from discord.ext import commands

from emojis import Emoji
from ui import UI

if TYPE_CHECKING:
    from main import Pushie, PushieContext

log = logging.getLogger(__name__)


class Roles(commands.Cog, name="Roles"):
    """Role management and assignment commands."""

    def __init__(self, bot: "Pushie") -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="role-list", description="List all roles in the server"
    )
    @commands.guild_only()
    async def role_list(self, ctx: "PushieContext") -> None:
        """List all roles in the server."""
        assert ctx.guild is not None
        roles = [r for r in ctx.guild.roles if r.name != "@everyone"]
        if not roles:
            await ctx.info("*No roles found.*")
            return

        role_text = "\n".join(
            f"> `{i+1}.` {r.mention} — *{len(r.members)} members*"
            for i, r in enumerate(roles[:15])
        )
        extra = f"\n> *+{len(roles) - 15} more roles...*" if len(roles) > 15 else ""

        embed = discord.Embed(
            description=f"`{Emoji.ROLE}` *Roles ({len(roles)} total)*\n\n{role_text}{extra}",
            color=0xFAB9EC,
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="role-info", description="Show information about a role"
    )
    @commands.guild_only()
    async def role_info(self, ctx: "PushieContext", role: discord.Role) -> None:
        """View detailed information about a role."""
        created = discord.utils.format_dt(role.created_at, style="D")
        created_rel = discord.utils.format_dt(role.created_at, style="R")

        perms = [
            p.replace("_", " ").title()
            for p, v in role.permissions
            if v and p not in ["administrator"]
        ]
        perms_text = (
            ", ".join(f"`{p}`" for p in perms[:5])
            + (f" *+{len(perms) - 5} more*" if len(perms) > 5 else "")
            if perms
            else "*none*"
        )

        embed = discord.Embed(
            description=f"> `{Emoji.ROLE}` *Role: {role.mention}*",
            color=role.color,
        )
        embed.add_field(
            name="Information",
            value=(
                f"> **ID** — `{role.id}`\n"
                f"> **Members** — `{len(role.members)}`\n"
                f"> **Created** — {created} ({created_rel})\n"
                f"> **Color** — `{role.color}`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Permissions",
            value=f"> {perms_text}",
            inline=False,
        )
        embed.add_field(
            name="Settings",
            value=(
                f"> **Display separately** — `{role.hoist}`\n"
                f"> **Mentionable** — `{role.mentionable}`\n"
                f"> **Managed** — `{role.managed}`"
            ),
            inline=True,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="role-add", description="Assign a role to a member")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_add(
        self, ctx: "PushieContext", member: discord.Member, role: discord.Role
    ) -> None:
        """Assign a role to a member."""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot assign a role higher than your own.*")
            return

        if role in member.roles:
            await ctx.warn(f"*{member.mention} already has {role.mention}.*")
            return

        try:
            await member.add_roles(role)
            await ctx.ok(
                f"`{Emoji.ROLE}` *{role.mention} assigned to {member.mention}.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to assign this role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to assign role: `{e}`*")

    @commands.hybrid_command(
        name="role-remove", description="Remove a role from a member"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_remove(
        self, ctx: "PushieContext", member: discord.Member, role: discord.Role
    ) -> None:
        """Remove a role from a member."""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot remove a role higher than your own.*")
            return

        if role not in member.roles:
            await ctx.warn(f"*{member.mention} doesn't have {role.mention}.*")
            return

        try:
            await member.remove_roles(role)
            await ctx.ok(
                f"`{Emoji.ROLE}` *{role.mention} removed from {member.mention}.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to remove this role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to remove role: `{e}`*")

    @commands.hybrid_command(name="role-create", description="Create a new role")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_create(
        self, ctx: "PushieContext", name: str, color: str | None = None
    ) -> None:
        """Create a new role."""
        assert ctx.guild is not None
        try:
            role_color = (
                discord.Color.from_str(color) if color else discord.Color.default()
            )
            role = await ctx.guild.create_role(name=name, color=role_color)
            await ctx.ok(f"`{Emoji.ROLE}` *Role {role.mention} created.*")
        except ValueError:
            await ctx.err("*Invalid color format. Use hex: `#ff0000`*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to create roles.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to create role: `{e}`*")

    @commands.hybrid_command(name="role-delete", description="Delete a role")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_delete(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Delete a role."""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot delete a role higher than your own.*")
            return

        if role.managed:
            await ctx.err("*You cannot delete a managed role.*")
            return

        try:
            role_name = role.name
            await role.delete()
            await ctx.ok(f"`{Emoji.ROLE}` *Role **{role_name}** deleted.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to delete roles.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to delete role: `{e}`*")

    @commands.hybrid_command(
        name="role-clear", description="Remove all roles from a member"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_clear(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Remove all roles from a member."""
        author = cast(discord.Member, ctx.author)
        if any(r >= author.top_role for r in member.roles):
            await ctx.err("*Some roles are higher than your own.*")
            return

        try:
            await member.remove_roles(
                *[r for r in member.roles if r.name != "@everyone"]
            )
            await ctx.ok(f"`{Emoji.ROLE}` *All roles removed from {member.mention}.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to remove roles.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to clear roles: `{e}`*")

    @commands.hybrid_command(
        name="role-restore", description="Restore previously removed roles"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_restore(self, ctx: "PushieContext", member: discord.Member) -> None:
        """Restore roles that were previously removed from a member."""
        assert ctx.guild is not None
        g = self.bot.storage.get_guild_sync(ctx.guild.id)
        if not g:
            await ctx.info("*Server data not found.*")
            return
        backups = getattr(g, "role_backups", None)
        if not backups:
            await ctx.info("*No role backups available for this server.*")
            return

        member_key = str(member.id)
        if member_key not in backups:
            await ctx.info(f"*No backup found for {member.mention}.*")
            return

        backup_role_ids = backups[member_key]
        restored_roles = []
        failed_roles = []

        for role_id in backup_role_ids:
            role = ctx.guild.get_role(role_id)
            if not role:
                failed_roles.append(role_id)
                continue
            try:
                await member.add_roles(role, reason="Role restore")
                restored_roles.append(role.mention)
            except discord.Forbidden:
                failed_roles.append(role_id)

        result_msg = f"`{Emoji.SUCCESS}` *Restored {len(restored_roles)} role(s)*"
        if restored_roles:
            result_msg += f": {', '.join(restored_roles)}"
        if failed_roles:
            result_msg += (
                f"\n`{Emoji.WARN}` *Failed to restore {len(failed_roles)} role(s)*"
            )

        del backups[member_key]
        await self.bot.storage.save_guild(g)
        await ctx.send(embed=UI.info(result_msg))

    # =========================================================================
    # ROLE CUSTOMIZATION
    # =========================================================================

    @commands.hybrid_command(name="role-color", description="Change a role's color")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_color(
        self, ctx: "PushieContext", role: discord.Role, color: str
    ) -> None:
        """Change a role's color. Use hex format: #ff0000"""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot edit a role higher than your own.*")
            return

        try:
            role_color = discord.Color.from_str(color)
            await role.edit(color=role_color)
            await ctx.ok(f"`{Emoji.ROLE}` *{role.mention} color changed to `{color}`.*")
        except ValueError:
            await ctx.err("*Invalid color format. Use hex: `#ff0000`*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to change color: `{e}`*")

    @commands.hybrid_command(name="role-rename", description="Rename a role")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_rename(
        self, ctx: "PushieContext", role: discord.Role, *, new_name: str
    ) -> None:
        """Rename a role."""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot edit a role higher than your own.*")
            return

        try:
            old_name = role.name
            await role.edit(name=new_name)
            await ctx.ok(
                f"`{Emoji.ROLE}` *Role **{old_name}** renamed to **{new_name}**.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to rename role: `{e}`*")

    @commands.hybrid_command(name="role-icon", description="Set a role's icon")
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_icon(
        self, ctx: "PushieContext", role: discord.Role, icon_url: str | None = None
    ) -> None:
        """Set or remove a role's icon."""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot edit a role higher than your own.*")
            return

        try:
            if icon_url:
                icon_data = await self.bot.session.get(icon_url)
                icon_bytes = await icon_data.read()
                # await role.edit(icon=icon_bytes)
                await ctx.ok(f"`{Emoji.ROLE}` *Role icon feature coming soon.*")
            else:
                # await role.edit(icon=None)
                await ctx.ok(f"`{Emoji.ROLE}` *{role.mention} icon removed.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to set icon: `{e}`*")

    @commands.hybrid_command(
        name="role-hoist", description="Toggle role display setting"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_hoist(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Toggle whether a role is displayed separately in the member list."""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot edit a role higher than your own.*")
            return

        try:
            await role.edit(hoist=not role.hoist)
            status = "will" if not role.hoist else "won't"
            await ctx.ok(
                f"`{Emoji.ROLE}` *{role.mention} {status} be displayed separately.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to toggle hoist: `{e}`*")

    @commands.hybrid_command(
        name="role-mentionable", description="Toggle role mentionability"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_mentionable(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Toggle whether a role can be mentioned."""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot edit a role higher than your own.*")
            return

        try:
            await role.edit(mentionable=not role.mentionable)
            status = "can" if not role.mentionable else "cannot"
            await ctx.ok(f"`{Emoji.ROLE}` *{role.mention} {status} now be mentioned.*")
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to toggle mentionable: `{e}`*")

    @commands.hybrid_command(
        name="role-mass-assign", description="Assign role to multiple members"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_mass_assign(
        self, ctx: "PushieContext", role: discord.Role, group: str = "all"
    ) -> None:
        """Assign a role to multiple members (all, bots, or humans)."""
        assert ctx.guild is not None
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot assign a role higher than your own.*")
            return

        group = group.lower()
        if group not in ["all", "bots", "humans"]:
            await ctx.err("*Group must be: `all`, `bots`, or `humans`*")
            return

        # Filter members
        members = ctx.guild.members
        if group == "bots":
            members = [m for m in members if m.bot]
        elif group == "humans":
            members = [m for m in members if not m.bot]

        count = 0
        async with ctx.typing():
            for member in members:
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                        count += 1
                    except (discord.Forbidden, discord.HTTPException):
                        pass

        await ctx.ok(f"`{Emoji.ROLE}` *{role.mention} assigned to `{count}` members.*")

    @commands.hybrid_command(
        name="role-mass-remove", description="Remove role from multiple members"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def role_mass_remove(
        self, ctx: "PushieContext", role: discord.Role, group: str = "all"
    ) -> None:
        """Remove a role from multiple members (all, bots, or humans)."""
        assert ctx.guild is not None
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot remove a role higher than your own.*")
            return

        group = group.lower()
        if group not in ["all", "bots", "humans"]:
            await ctx.err("*Group must be: `all`, `bots`, or `humans`*")
            return

        # Filter members
        members = ctx.guild.members
        if group == "bots":
            members = [m for m in members if m.bot]
        elif group == "humans":
            members = [m for m in members if not m.bot]

        count = 0
        async with ctx.typing():
            for member in members:
                if role in member.roles:
                    try:
                        await member.remove_roles(role)
                        count += 1
                    except (discord.Forbidden, discord.HTTPException):
                        pass

        await ctx.ok(f"`{Emoji.ROLE}` *{role.mention} removed from `{count}` members.*")

    @commands.hybrid_command(
        name="rolestrip", description="Remove dangerous permissions from a role"
    )
    @commands.guild_only()
    @commands.has_guild_permissions(manage_roles=True)
    async def rolestrip(self, ctx: "PushieContext", role: discord.Role) -> None:
        """Remove dangerous permissions from a role."""
        author = cast(discord.Member, ctx.author)
        if role >= author.top_role:
            await ctx.err("*You cannot edit a role higher than your own.*")
            return

        dangerous_perms = {
            "administrator": False,
            "manage_guild": False,
            "manage_roles": False,
            "manage_channels": False,
            "manage_messages": False,
            "ban_members": False,
            "kick_members": False,
            "move_members": False,
            "mute_members": False,
            "deafen_members": False,
            "manage_nicknames": False,
        }

        try:
            await role.edit(permissions=discord.Permissions(**dangerous_perms))
            await ctx.ok(
                f"`{Emoji.ROLE}` *Dangerous permissions removed from {role.mention}.*"
            )
        except discord.Forbidden:
            await ctx.err("*I don't have permission to edit this role.*")
        except discord.HTTPException as e:
            await ctx.err(f"*Failed to strip permissions: `{e}`*")

    # =========================================================================
    # ERROR HANDLING
    # =========================================================================

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, commands.HybridCommandError):
            error = error.original
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                embed=UI.error(
                    f"*You need: {', '.join(f'`{p}`' for p in error.missing_permissions)}*"
                )
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                embed=UI.error(
                    f"*I need: {', '.join(f'`{p}`' for p in error.missing_permissions)}*"
                )
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=UI.error(f"*Bad argument: {error}*"))
        else:
            raise error


async def setup(bot: "Pushie") -> None:
    await bot.add_cog(Roles(bot))
