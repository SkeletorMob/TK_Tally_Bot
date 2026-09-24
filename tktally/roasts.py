"""The insult factory. Add your own lines to any list below.

Placeholders available in every template:
  {killer} {victim}   – Discord mentions
  {weapon}            – " with their <weapon>" or "" if none given
  {weapon_bare}       – the weapon name, or a random default
  {game}              – game name or "the game"
  {count}             – killer's total TKs (including this one)
  {pair}              – times killer has TK'd this specific victim
  {nth}               – ordinal of {count}, e.g. "3rd"
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

STYLES = ("kyle", "obituary", "headline", "pun")

# ---- Kyle-style outrage -------------------------------------------------
KYLE = [
    "OH MY GOD! {killer} KILLED {victim}! **YOU BASTARD!**",
    "Oh my God, they killed {victim}! {killer}, you *bastard!*",
    "OMG, {killer} killed {victim}!! YOU BASTARD! ...that's TK number {count}, by the way.",
    "OH MY GOD, {killer} KILLED {victim}{weapon}! You... you ***teammate!***",
    "{victim} is dead! And {killer} did it! AGAIN! That's {pair} times! YOU BASTARD!",
    "Oh my God! {killer} killed {victim}! You bastard! Somebody check {killer}'s jersey, I think they're on the other team!",
]

# ---- Obituary pieces ----------------------------------------------------
OBIT_CAUSE = [
    "was tragically deleted by {killer}{weapon}",
    "passed away suddenly, and very much on purpose, at the hands of {killer}{weapon}",
    "was called home early by {killer}{weapon}",
    "died doing what they loved: trusting {killer}",
    "was reassigned to the spectator camera by {killer}{weapon}",
]
OBIT_SURVIVED = [
    "a fully loaded ult they never got to use",
    "a half-finished reload",
    "three unspent grenades and a single unspent grudge",
    "a loadout they spent 20 minutes customizing",
    "a K/D ratio that deserved better",
    "trust issues, now permanent",
    "a squad that saw the whole thing and did nothing",
]
OBIT_LIEU = [
    "In lieu of flowers, the family asks that {killer} check their crosshair.",
    "In lieu of flowers, please send {killer} a copy of the rules. Highlight the part about teams.",
    "In lieu of flowers, donations may be made to the {killer} Remedial Aim Fund.",
    "In lieu of flowers, the family requests {killer} be benched. Permanently.",
    "In lieu of flowers, please tell {killer} which color the enemies are.",
]
OBIT_SERVICE = [
    "Services will be held at respawn.",
    "A moment of silence will be observed during the next loading screen.",
    "Visitation will be held in the kill cam, which {killer} is advised not to watch.",
    "Burial at sea is not possible; the body clipped through the map.",
]

# ---- Breaking news ------------------------------------------------------
HEADLINE = [
    "📰 **BREAKING:** Local {game} player {killer} \"didn't see\" {victim}. Witnesses report {killer} saw everything.",
    "📰 **BREAKING:** {victim} found dead; sole suspect {killer} last seen holding a smoking{weapon_sp} and a guilty look.",
    "📰 **BREAKING:** {killer} commits {nth} act of treason. Enemy team issues statement of thanks.",
    "📰 **EXCLUSIVE:** Sources close to {victim} say they \"never saw it coming,\" mostly because it came from behind.",
    "📰 **DEVELOPING:** {killer} claims TK on {victim} was \"lag.\" Ping records show 12ms. Investigation ongoing.",
    "📰 **POLL:** 100% of {victim}s agree that {killer} is a menace. Margin of error: none.",
]

# ---- Puns and assorted burns -------------------------------------------
PUN = [
    "{killer} really put the *friend* in friendly fire. Actually, no. The opposite.",
    "{killer} takes \"team player\" very literally: they play *against* the team.",
    "{killer}, the enemy is the *other* color. Colorblind mode is in the settings.",
    "{killer} just did the enemy's job for free. Unpaid internship at the opposing team.",
    "That's not a kill feed, {killer}. That's a confession.",
    "{killer} misread \"leave no man behind\" as \"leave no man.\"",
    "Betrayal speedrun, any%: {killer} sets a new PB on {victim}.",
    "{killer} has been awarded the Medal of Dishonor. It will be pinned to their back, where it belongs.",
    "{victim} was shot in the back. {killer} calls it \"rear support.\"",
    "{killer} treats the squad like a buffet. Nobody's safe and everybody's on the menu.",
    "{killer} said they'd cover {victim}. Didn't say with what. Apparently{weapon_sp} fire.",
    "Friendly reminder that \"friendly fire\" is not a compliment, {killer}.",
    "{killer} has entered their villain era. Unfortunately it's a co-op game.",
    "If betrayal were a sport, {killer} would be MVP. Of the other team.",
]

# ---- Self-inflicted -----------------------------------------------------
SELF = [
    "🪞 {killer} has team killed... themselves. The call is coming from inside the house.",
    "🪞 {killer} was their own worst enemy. Literally. Just now. On camera.",
    "🪞 OH MY GOD, {killer} KILLED {killer}! YOU BASTARD! ...wait.",
    "🪞 {killer} has been nominated for a Darwin Award (Gaming Division).",
    "🪞 Breaking: {killer} betrays the one teammate who always trusted them: {killer}.",
]

DEFAULT_WEAPONS = ["rifle", "grenade", "shotgun", "rocket", "knife", "car", "C4 charge"]


@dataclass
class Roast:
    style: str
    text: str
    title: Optional[str] = None  # set for obituary-style embeds


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suf = "th"
    else:
        suf = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def _fields(killer: str, victim: str, weapon: Optional[str], game: Optional[str],
            count: int, pair: int, rng: random.Random) -> dict:
    w = (weapon or "").strip()
    return {
        "killer": killer,
        "victim": victim,
        "weapon": f" with their {w}" if w else "",
        "weapon_sp": f" {w}" if w else f" {rng.choice(DEFAULT_WEAPONS)}",
        "weapon_bare": w or rng.choice(DEFAULT_WEAPONS),
        "game": (game or "").strip() or "the game",
        "count": count,
        "pair": pair,
        "nth": ordinal(count),
    }


def make_roast(killer: str, victim: str, *, weapon: Optional[str] = None,
               game: Optional[str] = None, count: int = 1, pair: int = 1,
               style: Optional[str] = None, self_kill: bool = False,
               victim_name: Optional[str] = None,
               rng: Optional[random.Random] = None) -> Roast:
    """Build a roast. `victim_name` is the plain display name, used in the obituary title."""
    rng = rng or random.Random()
    f = _fields(killer, victim, weapon, game, count, pair, rng)

    if self_kill:
        return Roast("self", rng.choice(SELF).format(**f))

    if style not in STYLES:
        style = rng.choice(STYLES)

    if style == "kyle":
        return Roast(style, rng.choice(KYLE).format(**f))
    if style == "headline":
        return Roast(style, rng.choice(HEADLINE).format(**f))
    if style == "pun":
        return Roast(style, rng.choice(PUN).format(**f))

    # obituary
    survived = rng.sample(OBIT_SURVIVED, 2)
    body = "\n".join([
        f"{victim} {rng.choice(OBIT_CAUSE)}.".format(**f),
        f"They are survived by {survived[0]} and {survived[1]}.",
        rng.choice(OBIT_LIEU).format(**f),
        rng.choice(OBIT_SERVICE).format(**f),
        "",
        f"*Cause of death: teammate. This was {killer}'s {ordinal(count)} offense.*",
    ])
    title = f"🪦 In Memoriam: {victim_name}" if victim_name else "🪦 In Memoriam"
    return Roast("obituary", body, title=title)
