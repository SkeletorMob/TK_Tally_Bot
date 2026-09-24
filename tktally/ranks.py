"""Rank ladder (auto-assigned Discord roles) and achievements.

Edit RANKS freely: thresholds must be ascending. Role names are what the bot
creates / looks for in your server. Colors are hex ints.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from .db import TallyDB


@dataclass(frozen=True)
class Rank:
    threshold: int
    name: str
    color: int
    promo: str  # announced on promotion; {user} is the new rank-holder


RANKS: list[Rank] = [
    Rank(1,   "Friendly Fire Enthusiast", 0x9CCC65,
         "{user} has drawn first blood. Unfortunately it was *our* blood."),
    Rank(3,   "Blue on Blue",             0x42A5F5,
         "{user} is showing real commitment to the wrong team."),
    Rank(5,   "Spawn Camper (Own Spawn)", 0xFFCA28,
         "{user} now camps the one spawn nobody expected: ours."),
    Rank(10,  "Benedict Arnold",          0xFFA726,
         "{user} has been promoted to Benedict Arnold. The paperwork was signed in teammate blood."),
    Rank(15,  "Et Tu, Brute?",            0xEF5350,
         "{user} has earned the Et Tu, Brute? role. Caesar would like a word. Several, actually."),
    Rank(25,  "Certified War Criminal",   0xAB47BC,
         "{user} is now a Certified War Criminal. The Hague has been notified and is not amused."),
    Rank(50,  "Double Agent",             0x5C6BC0,
         "{user} is so good at this the enemy team is sending them a paycheck."),
    Rank(100, "The Traitor King",         0x212121,
         "ALL HAIL {user}, THE TRAITOR KING. Long may they reign. Short may we live."),
]

RANK_NAMES = {r.name for r in RANKS}


def rank_for(count: int) -> Optional[Rank]:
    current = None
    for r in RANKS:
        if count >= r.threshold:
            current = r
    return current


def next_rank(count: int) -> Optional[Rank]:
    for r in RANKS:
        if count < r.threshold:
            return r
    return None


# ---- Achievements ("rewards") -------------------------------------------

@dataclass(frozen=True)
class Achievement:
    key: str
    name: str
    emoji: str
    desc: str


ACHIEVEMENTS: dict[str, Achievement] = {a.key: a for a in [
    Achievement("first_blood",  "First Blood (Wrong Kind)", "🩸", "Commit your first team kill."),
    Achievement("repeat",       "Repeat Customer",          "🔁", "TK the same teammate 5 times."),
    Achievement("spree",        "Killing Spree (Of Friends)", "🔥", "3 team kills within an hour."),
    Achievement("equal_opp",    "Equal Opportunity Traitor", "⚖️", "TK 5 different teammates."),
    Achievement("vendetta",     "Vendetta",                 "🗡️", "TK someone within 10 minutes of them TKing you."),
    Achievement("self_own",     "The Call Is Coming From Inside the House", "🪞", "Team kill yourself."),
    Achievement("human_shield", "Human Shield",             "🛡️", "Get team killed 10 times."),
    Achievement("pincushion",   "Professional Pincushion",  "🎯", "Get team killed 25 times."),
]}


def check_achievements(db: TallyDB, guild_id: int, killer_id: int, victim_id: int,
                       now: Optional[float] = None) -> list[tuple[int, Achievement]]:
    """Evaluate achievements after a TK is recorded. Returns newly earned (user_id, achievement)."""
    now = now or time.time()
    earned: list[tuple[int, Achievement]] = []

    def grant(user_id: int, key: str) -> None:
        if db.award(guild_id, user_id, key):
            earned.append((user_id, ACHIEVEMENTS[key]))

    if killer_id == victim_id:
        grant(killer_id, "self_own")
        return earned

    kills = db.kill_count(guild_id, killer_id)
    if kills >= 1:
        grant(killer_id, "first_blood")
    if db.pair_count(guild_id, killer_id, victim_id) >= 5:
        grant(killer_id, "repeat")
    if db.kills_since(guild_id, killer_id, now - 3600) >= 3:
        grant(killer_id, "spree")
    if db.distinct_victims(guild_id, killer_id) >= 5:
        grant(killer_id, "equal_opp")

    revenge = db.last_tk_between(guild_id, victim_id, killer_id)
    if revenge and now - revenge.created_at <= 600:
        grant(killer_id, "vendetta")

    deaths = db.death_count(guild_id, victim_id)
    if deaths >= 10:
        grant(victim_id, "human_shield")
    if deaths >= 25:
        grant(victim_id, "pincushion")

    return earned
