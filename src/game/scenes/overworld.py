"""Overworld scene for the first playable prototype."""

from __future__ import annotations

from src.game import assets, colors
from src.game.camera import Camera
from src.game.entities.npc import NPC
from src.game.entities.player import Player
from src.game.maps.test_map import find_npcs, find_player_start, load_test_map, map_height, map_width
from src.game.scenes.base import BaseScene
from src.game.ui.dialogue_box import DialogueBox
from src.game.ui.hud import HUD


class OverworldScene(BaseScene):
    def __init__(self, pygame, player_name: str) -> None:
        self.pygame = pygame
        self.map_data = load_test_map()
        start_x, start_y = find_player_start(self.map_data)
        self.player = Player(start_x, start_y, name=player_name)
        self.npcs = [NPC(item.x, item.y, item.name, item.dialogue) for item in find_npcs(self.map_data)]
        self.dialogue: DialogueBox | None = None
        self.font = pygame.font.Font(None, 24)
        self.camera = Camera()
        self.hud = HUD(player_name=player_name)
        self.assets = assets.create_assets(pygame)
        self.camera.follow(self.player.x, self.player.y, map_width(self.map_data), map_height(self.map_data))

    def handle_event(self, event) -> None:
        if event.type != self.pygame.KEYDOWN:
            return
        if self.dialogue and self.dialogue.visible:
            if event.key in {self.pygame.K_SPACE, self.pygame.K_e, self.pygame.K_RETURN}:
                self.dialogue.close()
            return
        movement = self._movement_for_key(event.key)
        if movement is not None:
            self.try_move_player(movement[0], movement[1])
            return
        if event.key in {self.pygame.K_SPACE, self.pygame.K_e}:
            self.interact()

    def update(self) -> None:
        if self.dialogue and not self.dialogue.visible:
            self.dialogue = None
        self.camera.follow(self.player.x, self.player.y, map_width(self.map_data), map_height(self.map_data))

    def draw(self, surface) -> None:
        surface.fill(colors.BLACK)
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                screen_x, screen_y = self.camera.tile_to_screen(x, y)
                assets.draw_tile(self.pygame, surface, tile, screen_x, screen_y, self.assets)
        highlighted_npc = self.facing_npc()
        for npc in self.npcs:
            npc.draw(self.pygame, surface, self.camera, self.assets, highlighted=npc == highlighted_npc)
        self.player.draw(self.pygame, surface, self.camera, self.assets)
        self.hud.draw(self.pygame, surface, self.font)
        if self.dialogue:
            self.dialogue.draw(self.pygame, surface, self.font)

    def try_move_player(self, dx: int, dy: int) -> bool:
        if self.dialogue and self.dialogue.visible:
            return False
        return self.player.move(dx, dy, self.map_data)

    def interact(self) -> bool:
        npc = self.facing_npc()
        if npc is None:
            return False
        self.dialogue = DialogueBox(npc.name, npc.dialogue)
        return True

    def facing_npc(self) -> NPC | None:
        return next((npc for npc in self.npcs if npc.can_interact(self.player)), None)

    def _movement_for_key(self, key: int) -> tuple[int, int] | None:
        keys = self.pygame
        if key in {keys.K_LEFT, keys.K_a}:
            return (-1, 0)
        if key in {keys.K_RIGHT, keys.K_d}:
            return (1, 0)
        if key in {keys.K_UP, keys.K_w}:
            return (0, -1)
        if key in {keys.K_DOWN, keys.K_s}:
            return (0, 1)
        return None
