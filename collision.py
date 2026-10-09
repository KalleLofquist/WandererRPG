# collision.py — Shared collision detection utilities.

from settings import TILE_SIZE


def corners_clear(x: float, y: float, size: int, tilemap) -> bool:
    """
    Check if all four corners of a size×size bounding box at (x, y) are on walkable floor tiles.
    
    Args:
        x, y: Top-left corner in world-pixel space.
        size: Side length of the bounding box (typically PLAYER_SIZE or ENEMY_SIZE).
        tilemap: TileMap instance for wall queries.
    
    Returns:
        True if all four corners are floor tiles; False if any corner is a wall.
    """
    corners = [
        (x,             y),
        (x + size - 1,  y),
        (x,             y + size - 1),
        (x + size - 1,  y + size - 1),
    ]
    for cx, cy in corners:
        tile_x = int(cx) // TILE_SIZE
        tile_y = int(cy) // TILE_SIZE
        if tilemap.is_wall(tile_x, tile_y):
            return False
    return True
