# quest.py — Quest state machine.

from settings import DUNGEON_KILL_QUEST_TARGET

STATE_INACTIVE = 'inactive'
STATE_ACTIVE   = 'active'
STATE_COMPLETE = 'complete'
STATE_REWARDED = 'rewarded'


class DungeonClearQuest:
    """Kill DUNGEON_KILL_QUEST_TARGET dungeon enemies."""

    def __init__(self):
        self.state          = STATE_INACTIVE
        self.kills_needed   = DUNGEON_KILL_QUEST_TARGET
        self.kills_current  = 0

    def accept(self):
        """Transition INACTIVE → ACTIVE."""
        if self.state == STATE_INACTIVE:
            self.state = STATE_ACTIVE

    def on_enemy_killed(self):
        """Call when a dungeon enemy dies. Transitions to COMPLETE when target reached."""
        if self.state != STATE_ACTIVE:
            return
        self.kills_current = min(self.kills_current + 1, self.kills_needed)
        if self.kills_current >= self.kills_needed:
            self.state = STATE_COMPLETE

    def collect_reward(self, player):
        """
        Grant the reward to the player. Transition COMPLETE → REWARDED.
        Reward: 150 bonus XP + full heal.
        """
        if self.state != STATE_COMPLETE:
            return
        player.add_xp(150)
        player.hp = player.max_hp
        self.state = STATE_REWARDED

    @property
    def is_active(self):
        return self.state == STATE_ACTIVE

    @property
    def is_complete(self):
        return self.state == STATE_COMPLETE

    @property
    def is_rewarded(self):
        return self.state == STATE_REWARDED

    @property
    def description(self):
        """Short string for the HUD quest tracker."""
        if self.state == STATE_INACTIVE:
            return ''
        if self.state == STATE_ACTIVE:
            return f'Quest: Slay dungeon enemies  {self.kills_current}/{self.kills_needed}'
        if self.state == STATE_COMPLETE:
            return 'Quest: COMPLETE — return to the Elder!'
        return 'Quest: Completed'
