"""TK Tally Bot – Discord client and slash commands."""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

import discord
from discord import app_commands

from .db import TallyDB
from .ranks import ACHIEVEMENTS, RANK_NAMES, RANKS, check_achievements, next_rank, rank_for
from .roasts import STYLES, make_roast

log = logging.getLogger("tktally")

DUPLICATE_WINDOW_S = 15        # ignore the same killer→victim report twice within this window
UNDO_WINDOW_S = 15 * 60        # reporters can undo their own report for this long
DEFAULT_COLOR = 0xE53935

STYLE_CHOICES = [
    app_commands.Choice(name="Random", value="random"),
    app_commands.Choice(name="Kyle (OMG you killed…)", value="kyle"),
    app_commands.Choice(name="Obituary", value="obituary"),
    app_commands.Choice(name="Breaking news", value="headline"),
    app_commands.Choice(name="Pun", value="pun"),
]


class TKTallyBot(discord.Client):
    def __init__(self, db: TallyDB, dev_guild_id: Optional[int] = None):
        super().__init__(intents=discord.Intents.default())
        self.db = db
        self.dev_guild_id = dev_guild_id
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self) -> None:
        register_commands(self)
        if self.dev_guild_id:
            guild = discord.Object(id=self.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info("Commands synced to dev guild %s", self.dev_guild_id)
        else:
            await self.tree.sync()
            log.info("Commands synced globally (can take a few minutes to appear)")

    async def on_ready(self) -> None:
        log.info("Logged in as %s (%s) in %d servers", self.user, self.user.id, len(self.guilds))
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, name="for treason 👀"))


# ---- Role management ------------------------------------------------------

async def sync_rank_role(bot: TKTallyBot, member: discord.Member) -> Optional[str]:
    """Give the member the role for their current rank and strip other rank roles.
    Returns a warning string if permissions got in the way, else None."""
    guild = member.guild
    if not bot.db.roles_enabled(guild.id):
        return None

    count = bot.db.kill_count(guild.id, member.id)
    rank = rank_for(count)
    try:
        target_role = None
        if rank:
            target_role = discord.utils.get(guild.roles, name=rank.name)
            if target_role is None:
                target_role = await guild.create_role(
                    name=rank.name, colour=discord.Colour(rank.color),
                    reason="TK Tally Bot rank role")
        stale = [r for r in member.roles if r.name in RANK_NAMES and r != target_role]
        if stale:
            await member.remove_roles(*stale, reason="TK Tally rank change")
        if target_role and target_role not in member.roles:
            await member.add_roles(target_role, reason=f"TK Tally: {count} team kills")
    except discord.Forbidden:
        return ("⚠️ I couldn't update rank roles. Give me **Manage Roles** and drag my role "
                "above the TK rank roles in Server Settings → Roles.")
    except discord.HTTPException as e:
        log.warning("Role sync failed: %s", e)
    return None


# ---- Helpers --------------------------------------------------------------

def rank_line(count: int) -> str:
    rank = rank_for(count)
    nxt = next_rank(count)
    cur = f"**{rank.name}**" if rank else "*Unranked (for now)*"
    if nxt:
        return f"{cur} · {nxt.threshold - count} more to **{nxt.name}**"
    return f"{cur} · max rank. There is nowhere left to fall."


def is_mod(interaction: discord.Interaction) -> bool:
    perms = interaction.user.guild_permissions if isinstance(interaction.user, discord.Member) else None
    return bool(perms and perms.manage_guild)


async def record_tk(bot: TKTallyBot, interaction: discord.Interaction,
                    killer: discord.Member, victim: discord.Member,
                    weapon: Optional[str] = None, game: Optional[str] = None,
                    style: Optional[str] = None) -> None:
    guild = interaction.guild
    if killer.bot or victim.bot:
        await interaction.response.send_message(
            "Bots don't do treason. We're programmed for loyalty. Mostly.", ephemeral=True)
        return
    if bot.db.recent_duplicate(guild.id, killer.id, victim.id, DUPLICATE_WINDOW_S):
        await interaction.response.send_message(
            "Someone already reported that one. It only counts once, even if it hurt twice.",
            ephemeral=True)
        return

    weapon = (weapon or "").strip()[:60] or None
    game = (game or "").strip()[:60] or None
    self_kill = killer.id == victim.id
    before = bot.db.kill_count(guild.id, killer.id)
    bot.db.add_tk(guild.id, killer.id, victim.id, interaction.user.id, weapon, game)
    count = bot.db.kill_count(guild.id, killer.id)
    pair = bot.db.pair_count(guild.id, killer.id, victim.id)

    roast = make_roast(killer.mention, victim.mention, weapon=weapon, game=game,
                       count=max(count, 1), pair=pair, self_kill=self_kill,
                       style=None if style in (None, "random") else style,
                       victim_name=victim.display_name)

    rank = rank_for(count)
    embed = discord.Embed(title=roast.title or "☠️ TEAM KILL CONFIRMED",
                          description=roast.text,
                          color=rank.color if rank else DEFAULT_COLOR)
    if self_kill:
        embed.add_field(name="Self-inflicted", value=str(bot.db.self_kill_count(guild.id, killer.id)))
    else:
        embed.add_field(name=f"{killer.display_name}'s TKs", value=str(count))
        embed.add_field(name=f"{victim.display_name}'s deaths by teammate",
                        value=str(bot.db.death_count(guild.id, victim.id)))
        embed.add_field(name="Rank", value=rank_line(count), inline=False)
    if game:
        embed.set_footer(text=f"Game: {game}")

    # Promotion
    old_rank, new_rank = rank_for(before), rank
    messages: list[str] = []
    if new_rank and new_rank != old_rank:
        messages.append("🎖️ **PROMOTION!** " + new_rank.promo.format(user=killer.mention))

    for user_id, ach in check_achievements(bot.db, guild.id, killer.id, victim.id):
        who = killer if user_id == killer.id else victim
        messages.append(f"{ach.emoji} **Achievement unlocked:** {who.mention} earned *{ach.name}* ({ach.desc})")

    if messages:
        embed.add_field(name="​", value="\n".join(messages)[:1024], inline=False)

    await interaction.response.send_message(embed=embed,
                                            allowed_mentions=discord.AllowedMentions(users=True))

    if not self_kill:
        warning = await sync_rank_role(bot, killer)
        if warning:
            await interaction.followup.send(warning, ephemeral=True)


# ---- Commands -------------------------------------------------------------

def register_commands(bot: TKTallyBot) -> None:
    tree = bot.tree
    db = bot.db

    @tree.command(name="tk", description="Report a treasonous team kill")
    @app_commands.guild_only()
    @app_commands.describe(killer="The traitor", victim="The betrayed (defaults to you)",
                           weapon="Instrument of betrayal", game="Which game it happened in",
                           style="Flavor of roast")
    @app_commands.choices(style=STYLE_CHOICES)
    async def tk(interaction: discord.Interaction, killer: discord.Member,
                 victim: Optional[discord.Member] = None, weapon: Optional[str] = None,
                 game: Optional[str] = None, style: Optional[app_commands.Choice[str]] = None):
        await record_tk(bot, interaction, killer, victim or interaction.user, weapon, game,
                        style.value if style else None)

    @tree.context_menu(name="They TK'd me!")
    @app_commands.guild_only()
    async def tk_menu(interaction: discord.Interaction, member: discord.Member):
        await record_tk(bot, interaction, member, interaction.user)

    @tree.command(name="tally", description="Show someone's rap sheet")
    @app_commands.guild_only()
    async def tally(interaction: discord.Interaction, member: Optional[discord.Member] = None):
        member = member or interaction.user
        gid = interaction.guild.id
        kills = db.kill_count(gid, member.id)
        deaths = db.death_count(gid, member.id)
        selfk = db.self_kill_count(gid, member.id)
        rank = rank_for(kills)
        embed = discord.Embed(title=f"📋 Rap sheet: {member.display_name}",
                              color=rank.color if rank else DEFAULT_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Team kills", value=str(kills))
        embed.add_field(name="Times betrayed", value=str(deaths))
        embed.add_field(name="Self-inflicted", value=str(selfk))
        embed.add_field(name="Rank", value=rank_line(kills), inline=False)
        fav = db.favorite_victim(gid, member.id)
        if fav:
            embed.add_field(name="Favorite victim", value=f"<@{fav[0]}> ({fav[1]}×)")
        nem = db.nemesis(gid, member.id)
        if nem:
            embed.add_field(name="Nemesis", value=f"<@{nem[0]}> ({nem[1]}×)")
        achs = db.achievements(gid, member.id)
        if achs:
            embed.add_field(name="Achievements",
                            value="\n".join(f"{ACHIEVEMENTS[k].emoji} {ACHIEVEMENTS[k].name}"
                                            for k in achs if k in ACHIEVEMENTS),
                            inline=False)
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @tree.command(name="leaderboard", description="The Hall of Shame: top team killers")
    @app_commands.guild_only()
    async def leaderboard(interaction: discord.Interaction):
        rows = db.leaderboard(interaction.guild.id)
        if not rows:
            await interaction.response.send_message("No team kills yet. Suspiciously wholesome server.")
            return
        medals = ["🥇", "🥈", "🥉"]
        lines = []
        for i, (uid, n) in enumerate(rows):
            r = rank_for(n)
            lines.append(f"{medals[i] if i < 3 else f'`#{i+1}`'} <@{uid}>: **{n}** TKs · {r.name if r else ''}")
        embed = discord.Embed(title="🏛️ Hall of Shame", description="\n".join(lines), color=DEFAULT_COLOR)
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @tree.command(name="victims", description="The most betrayed players on the server")
    @app_commands.guild_only()
    async def victims(interaction: discord.Interaction):
        rows = db.victim_board(interaction.guild.id)
        if not rows:
            await interaction.response.send_message("Nobody's been betrayed yet. Give it time.")
            return
        lines = [f"`#{i+1}` <@{uid}>: killed by teammates **{n}** times" for i, (uid, n) in enumerate(rows)]
        embed = discord.Embed(title="🪦 Most Betrayed", description="\n".join(lines), color=0x607D8B)
        embed.set_footer(text="Thoughts and prayers.")
        await interaction.response.send_message(embed=embed, allowed_mentions=discord.AllowedMentions.none())

    @tree.command(name="undo", description="Take back your most recent TK report (within 15 minutes)")
    @app_commands.guild_only()
    async def undo(interaction: discord.Interaction):
        gid = interaction.guild.id
        last = db.last_report_by(gid, interaction.user.id)
        if not last or time.time() - last.created_at > UNDO_WINDOW_S:
            await interaction.response.send_message("Nothing recent to undo. What's reported is reported.",
                                                    ephemeral=True)
            return
        db.remove_tk(last.id)
        await interaction.response.send_message(
            f"↩️ Report struck from the record: <@{last.killer_id}> → <@{last.victim_id}>. "
            "The court apologizes for the confusion.",
            allowed_mentions=discord.AllowedMentions.none())
        killer = interaction.guild.get_member(last.killer_id)
        if killer:
            await sync_rank_role(bot, killer)

    @tree.command(name="forgive", description="Forgive the last team kill someone did on you")
    @app_commands.guild_only()
    async def forgive(interaction: discord.Interaction, killer: discord.Member):
        gid = interaction.guild.id
        last = db.last_tk_between(gid, killer.id, interaction.user.id)
        if not last or killer.id == interaction.user.id:
            await interaction.response.send_message(
                f"{killer.display_name} has never TK'd you. Save your mercy for when they do.", ephemeral=True)
            return
        db.remove_tk(last.id)
        await interaction.response.send_message(
            f"🕊️ {interaction.user.mention} has forgiven {killer.mention}. One TK wiped from the record. "
            "Forgiven, but *not* forgotten.")
        await sync_rank_role(bot, killer)

    @tree.command(name="roast", description="Roast someone based on their TK record")
    @app_commands.guild_only()
    async def roast(interaction: discord.Interaction, member: discord.Member):
        gid = interaction.guild.id
        kills = db.kill_count(gid, member.id)
        if kills == 0:
            await interaction.response.send_message(
                f"{member.mention} has a clean record. Either a saint, or they haven't been caught yet.")
            return
        fav = db.favorite_victim(gid, member.id)
        victim_mention = f"<@{fav[0]}>" if fav else "a teammate"
        r = make_roast(member.mention, victim_mention, count=kills, pair=fav[1] if fav else 1, style="pun")
        await interaction.response.send_message(f"{r.text}\n*Career TKs: {kills}.*",
                                                allowed_mentions=discord.AllowedMentions(users=[member]))

    @tree.command(name="ranks", description="Show the ladder of shame")
    async def ranks(interaction: discord.Interaction):
        lines = [f"`{r.threshold:>3}+` **{r.name}**" for r in RANKS]
        achs = [f"{a.emoji} **{a.name}**: {a.desc}" for a in ACHIEVEMENTS.values()]
        embed = discord.Embed(title="🎖️ Ranks of Dishonor", description="\n".join(lines), color=DEFAULT_COLOR)
        embed.add_field(name="Achievements", value="\n".join(achs), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ---- Admin group ----
    admin = app_commands.Group(name="tkadmin", description="TK Tally admin tools",
                               default_permissions=discord.Permissions(manage_guild=True),
                               guild_only=True)

    @admin.command(name="reset", description="Wipe a member's TK history and achievements")
    async def reset(interaction: discord.Interaction, member: discord.Member):
        n = db.reset_user(interaction.guild.id, member.id)
        await interaction.response.send_message(
            f"🧹 Wiped {n} records involving {member.mention}. A clean slate. Don't waste it.",
            allowed_mentions=discord.AllowedMentions.none())
        await sync_rank_role(bot, member)

    @admin.command(name="roles", description="Turn automatic rank roles on or off")
    async def roles(interaction: discord.Interaction, enabled: bool):
        db.set_roles_enabled(interaction.guild.id, enabled)
        await interaction.response.send_message(
            f"Automatic rank roles are now **{'on' if enabled else 'off'}**.", ephemeral=True)

    @admin.command(name="syncroles", description="Re-apply the correct rank role to a member")
    async def syncroles(interaction: discord.Interaction, member: discord.Member):
        warning = await sync_rank_role(bot, member)
        await interaction.response.send_message(warning or f"Synced {member.display_name}'s rank role.",
                                                ephemeral=True)

    @admin.command(name="add", description="Manually log a TK without a roast (for back-filling history)")
    async def add(interaction: discord.Interaction, killer: discord.Member, victim: discord.Member,
                  times: app_commands.Range[int, 1, 100] = 1):
        for _ in range(times):
            db.add_tk(interaction.guild.id, killer.id, victim.id, interaction.user.id)
        await interaction.response.send_message(
            f"Logged {times} TK(s): {killer.mention} → {victim.mention}.",
            allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
        await sync_rank_role(bot, killer)

    tree.add_command(admin)


def main() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in.")
    dev_guild = os.environ.get("DEV_GUILD_ID")
    db = TallyDB(os.environ.get("TK_DB_PATH", "tktally.db"))
    bot = TKTallyBot(db, int(dev_guild) if dev_guild else None)
    bot.run(token, log_handler=None)


if __name__ == "__main__":
    main()
