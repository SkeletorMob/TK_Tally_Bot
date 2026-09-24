import random
import time

import pytest

from tktally.db import TallyDB
from tktally.ranks import RANKS, check_achievements, next_rank, rank_for
from tktally.roasts import STYLES, make_roast, ordinal

G = 1
A, B, C = 100, 200, 300


@pytest.fixture
def db():
    d = TallyDB(":memory:")
    yield d
    d.close()


def test_counts_exclude_self_kills(db):
    db.add_tk(G, A, B, A)
    db.add_tk(G, A, A, A)
    assert db.kill_count(G, A) == 1
    assert db.self_kill_count(G, A) == 1
    assert db.death_count(G, B) == 1
    assert db.death_count(G, A) == 0


def test_guilds_are_isolated(db):
    db.add_tk(1, A, B, A)
    db.add_tk(2, A, B, A)
    assert db.kill_count(1, A) == 1


def test_duplicate_window(db):
    now = time.time()
    db.add_tk(G, A, B, A, now=now - 5)
    assert db.recent_duplicate(G, A, B, 15, now=now)
    assert not db.recent_duplicate(G, A, B, 3, now=now)


def test_leaderboard_nemesis_and_reset(db):
    for _ in range(3):
        db.add_tk(G, A, B, B)
    db.add_tk(G, C, B, B)
    assert db.leaderboard(G)[0] == (A, 3)
    assert db.nemesis(G, B) == (A, 3)
    assert db.favorite_victim(G, A) == (B, 3)
    db.reset_user(G, A)
    assert db.kill_count(G, A) == 0
    assert db.kill_count(G, C) == 1


def test_undo_and_forgive_helpers(db):
    tid = db.add_tk(G, A, B, C)
    assert db.last_report_by(G, C).id == tid
    assert db.last_tk_between(G, A, B).id == tid
    assert db.remove_tk(tid)
    assert db.kill_count(G, A) == 0


def test_rank_ladder():
    assert rank_for(0) is None
    assert rank_for(1).name == RANKS[0].name
    assert rank_for(12).threshold == 10
    assert next_rank(0).threshold == 1
    assert next_rank(10_000) is None
    assert [r.threshold for r in RANKS] == sorted(r.threshold for r in RANKS)


def test_achievements(db):
    now = time.time()
    db.add_tk(G, B, A, B, now=now - 60)   # B kills A first
    for _ in range(3):
        db.add_tk(G, A, B, A, now=now)
    earned = {a.key for _, a in check_achievements(db, G, A, B, now=now)}
    assert {"first_blood", "spree", "vendetta"} <= earned
    # Only awarded once
    assert check_achievements(db, G, A, B, now=now) == []
    db.add_tk(G, A, A, A)
    assert [a.key for _, a in check_achievements(db, G, A, A)] == ["self_own"]


def test_every_template_renders():
    for seed in range(300):
        rng = random.Random(seed)
        for style in STYLES:
            r = make_roast("<@1>", "<@2>", weapon=rng.choice([None, "AWP"]), game=None,
                           count=seed + 1, pair=2, style=style, victim_name="Bob", rng=rng)
            assert "{" not in r.text and r.text
        r = make_roast("<@1>", "<@1>", self_kill=True, rng=rng)
        assert "{" not in r.text


def test_weapon_with_braces_is_safe():
    r = make_roast("<@1>", "<@2>", weapon="{killer}{0}", style="kyle", rng=random.Random(3))
    assert r.text


def test_ordinal():
    assert [ordinal(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 102, 111)] == \
        ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "102nd", "111th"]
