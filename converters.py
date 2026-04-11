"""Custom discord.py converters for flexible channel / role / user resolution."""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from main import PushieContext


class SmartTextChannel(commands.Converter[discord.TextChannel]):
    """Resolve a text-channel from a mention, numeric ID, or name (case-insensitive)."""

    async def convert(self, ctx: "PushieContext", argument: str) -> discord.TextChannel:
        argument = argument.strip().lstrip("#")
        try:
            return await commands.TextChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            pass
        if ctx.guild:
            lower = argument.lower()
            for ch in ctx.guild.text_channels:
                if ch.name.lower() == lower:
                    return ch
            for ch in ctx.guild.text_channels:
                if ch.name.lower().startswith(lower):
                    return ch
        raise commands.BadArgument(f'Text channel "{argument}" not found.')


class SmartVoiceChannel(commands.Converter[discord.VoiceChannel]):
    """Resolve a voice-channel from a mention, numeric ID, or name (case-insensitive)."""

    async def convert(self, ctx: "PushieContext", argument: str) -> discord.VoiceChannel:
        argument = argument.strip().lstrip("#")
        try:
            return await commands.VoiceChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            pass
        if ctx.guild:
            lower = argument.lower()
            for ch in ctx.guild.voice_channels:
                if ch.name.lower() == lower:
                    return ch
            for ch in ctx.guild.voice_channels:
                if ch.name.lower().startswith(lower):
                    return ch
        raise commands.BadArgument(f'Voice channel "{argument}" not found.')


class SmartCategory(commands.Converter[discord.CategoryChannel]):
    """Resolve a category from a mention, numeric ID, or name (case-insensitive)."""

    async def convert(
        self, ctx: "PushieContext", argument: str
    ) -> discord.CategoryChannel:
        argument = argument.strip()
        try:
            return await commands.CategoryChannelConverter().convert(ctx, argument)
        except commands.BadArgument:
            pass
        if ctx.guild:
            lower = argument.lower()
            for cat in ctx.guild.categories:
                if cat.name.lower() == lower:
                    return cat
            for cat in ctx.guild.categories:
                if cat.name.lower().startswith(lower):
                    return cat
        raise commands.BadArgument(f'Category "{argument}" not found.')
