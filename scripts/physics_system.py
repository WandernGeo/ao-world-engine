#!/usr/bin/env python3
"""
Physics System
==============

Tick-based physics simulation for the AO World Engine.

Provides:
- Gravity and falling for entities
- Inertia and momentum for moving objects
- Collision detection (basic AABB)
- Projectile trajectories
- Environmental forces (wind, currents)

Note: This is a discrete-time simulation. Physics are updated per-tick,
not in real-time. Good for deterministic, reproducible simulations.
"""

import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


# ============================================================
# CONSTANTS
# ============================================================

GRAVITY = 9.81  # m/s² (can be adjusted for world)
TICK_DURATION = 0.5  # seconds per tick
AIR_RESISTANCE = 0.02  # drag coefficient
TERMINAL_VELOCITY = 50.0  # m/s
FRICTION_GROUND = 0.3
FRICTION_ICE = 0.05
FRICTION_MUD = 0.7


@dataclass
class Vector3:
    """3D vector for positions and velocities."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0  # Height (up is positive)
    
    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'Vector3':
        mag = self.magnitude()
        if mag == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x / mag, self.y / mag, self.z / mag)
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class PhysicsBody:
    """A physical entity in the world."""
    id: str
    position: Vector3 = field(default_factory=Vector3)
    velocity: Vector3 = field(default_factory=Vector3)
    mass: float = 1.0  # kg
    radius: float = 0.5  # meters (for collision)
    grounded: bool = True
    friction: float = FRICTION_GROUND
    elasticity: float = 0.3  # bounce factor
    drag: float = AIR_RESISTANCE
    
    # Flags
    affected_by_gravity: bool = True
    is_static: bool = False  # Static objects don't move
    is_projectile: bool = False


@dataclass 
class AABB:
    """Axis-Aligned Bounding Box for collision."""
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float
    max_z: float
    
    def intersects(self, other: 'AABB') -> bool:
        """Check if two AABBs intersect."""
        return (
            self.min_x <= other.max_x and self.max_x >= other.min_x and
            self.min_y <= other.max_y and self.max_y >= other.min_y and
            self.min_z <= other.max_z and self.max_z >= other.min_z
        )
    
    @classmethod
    def from_body(cls, body: PhysicsBody) -> 'AABB':
        """Create AABB from a physics body."""
        r = body.radius
        return cls(
            body.position.x - r, body.position.x + r,
            body.position.y - r, body.position.y + r,
            body.position.z - r, body.position.z + r
        )


class PhysicsWorld:
    """The physics simulation environment."""
    
    def __init__(self, gravity: float = GRAVITY, tick_duration: float = TICK_DURATION):
        self.gravity = gravity
        self.tick_duration = tick_duration
        self.bodies: Dict[str, PhysicsBody] = {}
        self.static_colliders: List[AABB] = []
        self.ground_height: float = 0.0
        self.wind: Vector3 = Vector3(0, 0, 0)
        
    def add_body(self, body: PhysicsBody) -> None:
        """Add a physics body to the simulation."""
        self.bodies[body.id] = body
    
    def remove_body(self, body_id: str) -> None:
        """Remove a physics body."""
        if body_id in self.bodies:
            del self.bodies[body_id]
    
    def add_static_collider(self, aabb: AABB) -> None:
        """Add a static collision box (building, wall, etc)."""
        self.static_colliders.append(aabb)
    
    def set_wind(self, direction: Vector3, strength: float) -> None:
        """Set environmental wind force."""
        self.wind = direction.normalize() * strength
    
    def apply_force(self, body_id: str, force: Vector3) -> None:
        """Apply a force to a body (impulse)."""
        if body_id in self.bodies:
            body = self.bodies[body_id]
            if not body.is_static:
                # F = ma, so a = F/m
                acceleration = force * (1.0 / body.mass)
                body.velocity = body.velocity + acceleration * self.tick_duration
    
    def launch_projectile(
        self, 
        start: Vector3, 
        velocity: Vector3, 
        mass: float = 0.5
    ) -> str:
        """Launch a projectile with given initial velocity."""
        import uuid
        proj_id = f"proj_{uuid.uuid4().hex[:8]}"
        
        body = PhysicsBody(
            id=proj_id,
            position=start,
            velocity=velocity,
            mass=mass,
            radius=0.1,
            grounded=False,
            is_projectile=True,
            affected_by_gravity=True,
            drag=AIR_RESISTANCE * 2  # Projectiles have more drag
        )
        self.add_body(body)
        return proj_id
    
    def tick(self) -> List[Dict[str, Any]]:
        """
        Advance physics simulation by one tick.
        
        Returns list of events (collisions, landings, etc).
        """
        events = []
        dt = self.tick_duration
        
        for body_id, body in list(self.bodies.items()):
            if body.is_static:
                continue
            
            # Store previous state
            prev_pos = Vector3(body.position.x, body.position.y, body.position.z)
            
            # Apply gravity
            if body.affected_by_gravity and not body.grounded:
                gravity_force = Vector3(0, 0, -self.gravity * body.mass)
                body.velocity = body.velocity + gravity_force * (dt / body.mass)
            
            # Apply wind (if airborne)
            if not body.grounded:
                body.velocity = body.velocity + self.wind * dt
            
            # Apply drag (air resistance)
            speed = body.velocity.magnitude()
            if speed > 0:
                drag_force = body.velocity.normalize() * (-body.drag * speed * speed)
                body.velocity = body.velocity + drag_force * dt
            
            # Terminal velocity cap
            if body.velocity.z < -TERMINAL_VELOCITY:
                body.velocity = Vector3(body.velocity.x, body.velocity.y, -TERMINAL_VELOCITY)
            
            # Apply friction (if grounded)
            if body.grounded:
                friction = body.friction
                body.velocity = Vector3(
                    body.velocity.x * (1 - friction * dt),
                    body.velocity.y * (1 - friction * dt),
                    body.velocity.z
                )
                # Stop if very slow
                if abs(body.velocity.x) < 0.01:
                    body.velocity = Vector3(0, body.velocity.y, body.velocity.z)
                if abs(body.velocity.y) < 0.01:
                    body.velocity = Vector3(body.velocity.x, 0, body.velocity.z)
            
            # Update position
            body.position = body.position + body.velocity * dt
            
            # Ground collision
            if body.position.z <= self.ground_height:
                if not body.grounded:
                    # Landing event
                    impact_speed = abs(body.velocity.z)
                    events.append({
                        "type": "landing",
                        "body_id": body_id,
                        "impact_speed": impact_speed,
                        "position": body.position.to_tuple()
                    })
                    
                    # Bounce if elastic
                    if body.elasticity > 0 and impact_speed > 1:
                        body.velocity = Vector3(
                            body.velocity.x,
                            body.velocity.y,
                            -body.velocity.z * body.elasticity
                        )
                        body.position = Vector3(body.position.x, body.position.y, self.ground_height + 0.01)
                    else:
                        body.velocity = Vector3(body.velocity.x, body.velocity.y, 0)
                        body.position = Vector3(body.position.x, body.position.y, self.ground_height)
                        body.grounded = True
            else:
                body.grounded = False
            
            # Static collider checks
            body_aabb = AABB.from_body(body)
            for collider in self.static_colliders:
                if body_aabb.intersects(collider):
                    events.append({
                        "type": "collision",
                        "body_id": body_id,
                        "position": body.position.to_tuple()
                    })
                    # Simple response: push back
                    body.position = prev_pos
                    body.velocity = Vector3(0, 0, 0)
                    break
            
            # Remove projectiles that hit ground
            if body.is_projectile and body.grounded:
                events.append({
                    "type": "projectile_impact",
                    "body_id": body_id,
                    "position": body.position.to_tuple()
                })
                self.remove_body(body_id)
        
        return events
    
    def get_state(self, body_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a body."""
        if body_id not in self.bodies:
            return None
        body = self.bodies[body_id]
        return {
            "id": body_id,
            "position": body.position.to_tuple(),
            "velocity": body.velocity.to_tuple(),
            "speed": body.velocity.magnitude(),
            "grounded": body.grounded,
            "height": body.position.z
        }


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def calculate_fall_time(height: float, gravity: float = GRAVITY) -> float:
    """Calculate time to fall from height (ignoring air resistance)."""
    if height <= 0:
        return 0
    return math.sqrt(2 * height / gravity)


def calculate_impact_velocity(height: float, gravity: float = GRAVITY) -> float:
    """Calculate velocity at impact from height."""
    if height <= 0:
        return 0
    return math.sqrt(2 * gravity * height)


def calculate_projectile_range(
    velocity: float, 
    angle_degrees: float, 
    gravity: float = GRAVITY
) -> float:
    """Calculate horizontal range of a projectile."""
    angle_rad = math.radians(angle_degrees)
    return (velocity ** 2 * math.sin(2 * angle_rad)) / gravity


def create_npc_body(npc_id: str, x: float, y: float, z: float = 0) -> PhysicsBody:
    """Create a physics body for an NPC."""
    return PhysicsBody(
        id=npc_id,
        position=Vector3(x, y, z),
        velocity=Vector3(0, 0, 0),
        mass=70.0,  # Average human mass
        radius=0.4,  # Roughly human width
        grounded=z <= 0,
        friction=FRICTION_GROUND,
        elasticity=0.1,  # Humans don't bounce much
        affected_by_gravity=True
    )


# ============================================================
# CLI TEST
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("  Physics System Test")
    print("="*60 + "\n")
    
    # Create world
    world = PhysicsWorld(gravity=9.81, tick_duration=0.5)
    
    # Test 1: Falling object
    print("--- Test 1: Falling Object ---")
    falling = PhysicsBody(
        id="falling_box",
        position=Vector3(0, 0, 20),  # 20 meters up
        velocity=Vector3(0, 0, 0),
        mass=5.0,
        grounded=False
    )
    world.add_body(falling)
    
    print(f"Starting height: {falling.position.z:.1f}m")
    
    for tick in range(20):
        events = world.tick()
        state = world.get_state("falling_box")
        if state:
            print(f"  Tick {tick}: z={state['height']:.2f}m, vz={state['velocity'][2]:.2f}m/s")
        for event in events:
            if event['type'] == 'landing':
                print(f"  → LANDED! Impact speed: {event['impact_speed']:.2f}m/s")
    
    # Test 2: Projectile
    print("\n--- Test 2: Projectile Trajectory ---")
    world2 = PhysicsWorld()
    
    # Launch at 45 degrees, 20 m/s
    angle = 45
    speed = 20
    vx = speed * math.cos(math.radians(angle))
    vz = speed * math.sin(math.radians(angle))
    
    proj_id = world2.launch_projectile(
        start=Vector3(0, 0, 1),
        velocity=Vector3(vx, 0, vz)
    )
    
    theoretical_range = calculate_projectile_range(speed, angle)
    print(f"Launch: {speed}m/s at {angle}°")
    print(f"Theoretical range: {theoretical_range:.1f}m")
    
    max_height = 0
    for tick in range(100):
        events = world2.tick()
        state = world2.get_state(proj_id)
        if state:
            max_height = max(max_height, state['height'])
            if tick % 5 == 0:
                print(f"  Tick {tick}: x={state['position'][0]:.1f}m, z={state['height']:.1f}m")
        for event in events:
            if event['type'] == 'projectile_impact':
                print(f"  → IMPACT at x={event['position'][0]:.1f}m")
        if not state:
            break
    
    print(f"Max height reached: {max_height:.1f}m")
    
    # Test 3: NPC pushed
    print("\n--- Test 3: NPC with Inertia ---")
    world3 = PhysicsWorld()
    
    npc = create_npc_body("charlie", 0, 0, 0)
    world3.add_body(npc)
    
    # Push the NPC
    world3.apply_force("charlie", Vector3(500, 0, 0))  # 500N push
    
    print("Applied 500N push to Charlie")
    for tick in range(10):
        world3.tick()
        state = world3.get_state("charlie")
        if state:
            print(f"  Tick {tick}: x={state['position'][0]:.2f}m, vx={state['velocity'][0]:.2f}m/s")
    
    print("\n" + "="*60)
    print("✓ Physics System Test Complete!")
    print("="*60)
