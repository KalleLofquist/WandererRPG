# particles.py — Simple particle system for game juice.
import pygame
import random

class Particle:
    """A small colored square that moves and fades out."""
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        # Random velocity
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        # Lifetime in frames
        self.lifetime = random.randint(20, 40)
        self.age = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.age += 1
        return self.age < self.lifetime

    def draw(self, screen, camera_offset):
        # Calculate screen position
        screen_x = self.x - camera_offset[0]
        screen_y = self.y - camera_offset[1]
        
        # Fade color based on age
        alpha = 255 * (1.0 - self.age / self.lifetime)
        # Pygame draw.rect doesn't support alpha directly without a surface,
        # so we'll just shrink the particle or use a simple color fade.
        size = max(1, int(4 * (1.0 - self.age / self.lifetime)))
        pygame.draw.rect(screen, self.color, (screen_x, screen_y, size, size))

class ParticleManager:
    """Manages a collection of active particles."""
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, screen, camera):
        offset = camera.offset
        for p in self.particles:
            p.draw(screen, offset)
