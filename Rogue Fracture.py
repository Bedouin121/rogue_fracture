from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys
import numpy as np

player_ammo = 30
circular_obstacles = []
max_circular_obstacles = 5
obstacle_radius = 40
mouse_aim_enabled = False
mouse_aim_base_rotation = 0
mouseX, mouseY = 0, 0
mouse_click_mode = False
level = 1
forward_velocity = [0, 0]
leap_speed = 8
gravity = -0.8
vertical_velocity = 0
is_jumping = False
on_ground = False
leap_speed = 8
bullets = []
player_lives = 10
bullet_speed = 5
fire_rate = 10
fire_cooldown = 0
key_states = {}
linger_frames = 10
top_wall_segments = []
bottom_wall_segments = []
gameover = False
found_portal = False
playersize = 30
player_height = 45
playerpos = [0, 0, 0 + player_height * 0.5]
playerrot = 0
playerspeed = 5
rotspeed = 5
gridlen = 600
maze_width = 800
maze_length = 1500
corridor_width = 100
wall_thickness = 50
maze_height = 100
portal_position = [maze_width / 2 - corridor_width / 2, -maze_length / 2 + corridor_width / 2, 0]
portal_size = 60
portal_rotation = 0
top_platform_height = 0
bottom_platform_height = -300
platform_size = [maze_width + 200, maze_length + 200]
enemies = []

class Bullet:
    def __init__(self, position, direction, source):
        self.position = list(position)
        self.direction = list(direction)
        self.size = 5
        self.alive = True
        self.source = source
    def update(self):
        self.position[0] += self.direction[0] * bullet_speed
        self.position[1] += self.direction[1] * bullet_speed
        self.position[2] += self.direction[2] * bullet_speed
        if abs(self.position[0]) > 1000 or abs(self.position[1]) > 1500 or abs(self.position[2]) > 500:
            self.alive = False
    def draw(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glColor3f(1, 0, 0)
        draw_cube(self.size * 1.5)
        glPopMatrix()

def ray_intersects_wall(start, end, wall_segments):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return False
    dir_x = dx / length
    dir_y = dy / length
    step_size = 5
    steps = int(length / step_size) + 1
    for i in range(steps):
        t = i / steps
        x = start[0] + t * dx
        y = start[1] + t * dy
        if is_inside_wall(x, y, wall_segments, 1):
            return True
    return False

class Enemy:
    def __init__(self, enemy_type, size, body_color, head_color, position):
        self.type = enemy_type
        self.size = size
        self.body_color = body_color
        self.head_color = head_color
        self.position = list(position)
        self.rotation = random.uniform(0, 360)
        if self.type == 'red':
            self.lives = 1
        elif self.type == 'purple':
            self.lives = 3
        elif self.type == 'black':
            self.lives = 5
        self.shoot_cooldown = random.randint(30, 90)
    def is_alive(self):
        return self.lives > 0
    def draw(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glRotatef(self.rotation, 0, 0, 1)
        scale_factor = self.size / playersize
        leg_base_radius = 5 * scale_factor
        leg_height = 15 * scale_factor
        glColor3f(0.5, 0.3, 0.1)
        for i in [-1, 1]:
            glPushMatrix()
            glTranslatef(i * 10 * scale_factor, 0, 0)
            glRotatef(90, 1, 0, 0)
            draw_cone(leg_base_radius, leg_height, 10, 10)
            glPopMatrix()
        body_width = 15 * scale_factor
        body_depth = 10 * scale_factor
        body_height = 30 * scale_factor
        glColor3f(*self.body_color)
        glPushMatrix()
        glTranslatef(0, 0, body_height * 0.5)
        glScalef(body_width, body_depth, body_height)
        draw_cube(1)
        glPopMatrix()
        head_radius = 10 * scale_factor
        glColor3f(*self.head_color)
        glPushMatrix()
        glTranslatef(0, 0, body_height + head_radius)
        draw_sphere(head_radius, 20, 20)
        glPopMatrix()
        arm_radius = 3 * scale_factor
        arm_height = 45 * scale_factor
        glColor3f(0.1, 0.5, 0.8)
        for i in [-1, 1]:
            glPushMatrix()
            arm_z_position = 25 * scale_factor
            glTranslatef(i * 12 * scale_factor, 0, arm_z_position)
            glRotatef(45, 0, 1, 0)
            glRotatef(-90, 1, 0, 0)
            draw_cylinder(arm_radius, arm_radius, arm_height, 10, 10)
            if i == 1:
                glColor3f(0.3, 0.3, 0.3)
                glTranslatef(0, 0, arm_height)
                glScalef(4, 4, 10)
                draw_cube(1)
            glPopMatrix()
        glPopMatrix()
    def shoot(self, player_pos):
        self.shoot_cooldown -= 1
        if self.shoot_cooldown > 0:
            return
        ex, ey = self.position[0], self.position[1]
        px, py = player_pos[0], player_pos[1]
        player_base_z = player_pos[2] - player_height * 0.5
        enemy_base_z = self.position[2]
        player_on_top = abs(player_base_z - top_platform_height) < maze_height / 2
        enemy_on_top = abs(enemy_base_z - top_platform_height) < maze_height / 2
        if player_on_top != enemy_on_top:
            return
        wall_segments = top_wall_segments if player_on_top else bottom_wall_segments
        if ray_intersects_wall((ex, ey), (px, py), wall_segments):
            return
        delta_x = px - ex
        delta_y = py - ey
        angle_to_player = math.degrees(math.atan2(delta_y, delta_x))
        relative_angle = abs((angle_to_player - (self.rotation)) % 360)
        if relative_angle > 180:
            relative_angle = 360 - relative_angle
        if relative_angle > 45:
            return
        rad = math.radians(-self.rotation)
        dir_x = math.sin(rad)
        dir_y = math.cos(rad)
        bullet_start_x = ex + dir_x * 20
        bullet_start_y = ey + dir_y * 20
        bullet_start_z = self.position[2]
        bullet_dir_x = px - bullet_start_x
        bullet_dir_y = py - bullet_start_y
        bullet_dir_z = player_pos[2] - bullet_start_z
        length = math.sqrt(bullet_dir_x ** 2 + bullet_dir_y ** 2 + bullet_dir_z ** 2)
        if length != 0:
            bullet_dir_x /= length
            bullet_dir_y /= length
            bullet_dir_z /= length
        bullets.append(Bullet([bullet_start_x, bullet_start_y, bullet_start_z],
                              [bullet_dir_x, bullet_dir_y, bullet_dir_z], "enemy"))
        self.shoot_cooldown = random.randint(60, 120)
    def update_rotation(self):
        global level
        rotation_speed = 1 * level
        self.rotation += rotation_speed
        if self.rotation >= 360:
            self.rotation -= 360

def draw_circular_obstacles():
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(1, 0, 0, 0.7)
    for x, y, r in circular_obstacles:
        glPushMatrix()
        glTranslatef(x, y, top_platform_height + 2)
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(0, 0)
        for i in range(0, 360, 10):
            angle = math.radians(i)
            glVertex2f(math.cos(angle) * r, math.sin(angle) * r)
        glEnd()
        glPopMatrix()

def generate_circular_obstacles():
    global circular_obstacles
    circular_obstacles.clear()
    corridor_spacing = (maze_width - 5 * wall_thickness) / 4
    random.seed(level + 1000)
    attempts = 0
    max_attempts = 1000
    while len(circular_obstacles) < max_circular_obstacles and attempts < max_attempts:
        attempts += 1
        corridor_idx = random.randint(0, 4)
        x_center = -maze_width / 2 + wall_thickness + corridor_idx * (
                    corridor_spacing + wall_thickness) + corridor_spacing / 2
        rand_y = random.uniform(-maze_length / 2 + wall_thickness, maze_length / 2 - wall_thickness)
        overlap = False
        for enemy in enemies:
            dx = enemy.position[0] - x_center
            dy = enemy.position[1] - rand_y
            dist = math.hypot(dx, dy)
            if dist < obstacle_radius * 2:
                overlap = True
                break
        if overlap:
            continue
        if is_inside_wall(x_center, rand_y, top_wall_segments, obstacle_radius):
            continue
        circular_obstacles.append((x_center, rand_y, obstacle_radius))

def draw_cube(size):
    half = size / 2
    glBegin(GL_QUADS)
    glVertex3f(-half, -half, half)
    glVertex3f(half, -half, half)
    glVertex3f(half, half, half)
    glVertex3f(-half, half, half)
    glVertex3f(-half, -half, -half)
    glVertex3f(-half, half, -half)
    glVertex3f(half, half, -half)
    glVertex3f(half, -half, -half)
    glVertex3f(-half, -half, -half)
    glVertex3f(-half, -half, half)
    glVertex3f(-half, half, half)
    glVertex3f(-half, half, -half)
    glVertex3f(half, -half, -half)
    glVertex3f(half, half, -half)
    glVertex3f(half, half, half)
    glVertex3f(half, -half, half)
    glVertex3f(-half, half, -half)
    glVertex3f(-half, half, half)
    glVertex3f(half, half, half)
    glVertex3f(half, half, -half)
    glVertex3f(-half, -half, -half)
    glVertex3f(half, -half, -half)
    glVertex3f(half, -half, half)
    glVertex3f(-half, -half, half)
    glEnd()

def draw_sphere(radius, slices, stacks):
    for i in range(stacks):
        lat0 = math.pi * (-0.5 + float(i) / stacks)
        z0 = math.sin(lat0) * radius
        zr0 = math.cos(lat0) * radius
        lat1 = math.pi * (-0.5 + float(i + 1) / stacks)
        z1 = math.sin(lat1) * radius
        zr1 = math.cos(lat1) * radius
        glBegin(GL_QUAD_STRIP)
        for j in range(slices + 1):
            lng = 2 * math.pi * float(j) / slices
            x = math.cos(lng)
            y = math.sin(lng)
            glVertex3f(x * zr0, y * zr0, z0)
            glVertex3f(x * zr1, y * zr1, z1)
        glEnd()

def draw_cone(base, height, slices, stacks):
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)
    for i in range(slices + 1):
        angle = 2.0 * math.pi * i / slices
        x = base * math.cos(angle)
        y = base * math.sin(angle)
        glVertex3f(x, y, 0)
    glEnd()
    glBegin(GL_TRIANGLE_STRIP)
    glVertex3f(0, 0, height)
    for i in range(slices + 1):
        angle = 2.0 * math.pi * i / slices
        x = base * math.cos(angle)
        y = base * math.sin(angle)
        glVertex3f(x, y, 0)
        glVertex3f(0, 0, height)
    glEnd()

def draw_cylinder(base, top, height, slices, stacks):
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        angle = 2.0 * math.pi * i / slices
        x = math.cos(angle)
        y = math.sin(angle)
        glVertex3f(base * x, base * y, 0)
        glVertex3f(top * x, top * y, height)
    glEnd()
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0)
    for i in range(slices + 1):
        angle = 2.0 * math.pi * i / slices
        x = base * math.cos(angle)
        y = base * math.sin(angle)
        glVertex3f(x, y, 0)
    glEnd()
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, height)
    for i in range(slices + 1):
        angle = 2.0 * math.pi * (slices - i) / slices
        x = top * math.cos(angle)
        y = top * math.sin(angle)
        glVertex3f(x, y, height)
    glEnd()

def draw_torus(inner_radius, outer_radius, sides, rings):
    ring_radius = (outer_radius - inner_radius) / 2
    center_radius = inner_radius + ring_radius
    for i in range(rings):
        glBegin(GL_QUAD_STRIP)
        for j in range(sides + 1):
            for k in range(2):
                s = (i + k) % rings
                r = j % sides
                u = 2.0 * math.pi * r / sides
                v = 2.0 * math.pi * s / rings
                x = (center_radius + ring_radius * math.cos(v)) * math.cos(u)
                y = (center_radius + ring_radius * math.cos(v)) * math.sin(u)
                z = ring_radius * math.sin(v)
                glVertex3f(x, y, z)
        glEnd()

def is_inside_wall(x, y, wall_segments, object_radius):
    for wall_x, start_y, end_y, thickness in wall_segments:
        wall_left = wall_x - object_radius
        wall_right = wall_x + thickness + object_radius
        wall_bottom = start_y - object_radius
        wall_top = end_y + object_radius
        if (x >= wall_left and x <= wall_right and y >= wall_bottom and y <= wall_top):
            return True
    return False

def generate_enemies():
    global enemies
    enemies = []
    enemy_configs = [
        {'type': 'red', 'size': playersize * 0.7, 'body_color': (1, 0, 0)},
        {'type': 'purple', 'size': playersize * 1.0, 'body_color': (0.5, 0, 0.5)},
        {'type': 'black', 'size': playersize * 1.3, 'body_color': (0, 0, 0)},
        {'type': 'red', 'size': playersize * 0.7, 'body_color': (1, 0, 0)},
        {'type': 'purple', 'size': playersize * 1.0, 'body_color': (0.5, 0, 0.5)},
    ]
    if level >= 2:
        enemy_configs += [
            {'type': 'red', 'size': playersize * 0.7, 'body_color': (1, 0, 0)},
            {'type': 'purple', 'size': playersize * 1.0, 'body_color': (0.5, 0, 0.5)},
            {'type': 'black', 'size': playersize * 1.3, 'body_color': (0, 0, 0)},
            {'type': 'red', 'size': playersize * 0.7, 'body_color': (1, 0, 0)},
        ]
    head_color = (1, 1, 0)
    corridor_spacing = (maze_width - 5 * wall_thickness) / 4
    corridor_centers = []
    for i in range(5):
        x_center = -maze_width / 2 + wall_thickness + i * (corridor_spacing + wall_thickness) + corridor_spacing / 2
        corridor_centers.append(x_center)
    min_y = -maze_length / 2 + wall_thickness
    max_y = maze_length / 2 - wall_thickness
    for idx, config in enumerate(enemy_configs):
        enemy_type = config['type']
        size = config['size']
        body_color = config['body_color']
        attempts = 0
        max_attempts = 500
        scale_factor = size / playersize
        leg_horizontal_extent = 10 * scale_factor + 5 * scale_factor
        body_horizontal_extent = 15 * scale_factor * 0.5
        head_horizontal_extent = 10 * scale_factor
        arm_horizontal_extent = 12 * scale_factor + 3 * scale_factor
        enemy_approx_radius = max(
            leg_horizontal_extent,
            body_horizontal_extent,
            head_horizontal_extent,
            arm_horizontal_extent
        ) * 1.2
        placed = False
        while not placed and attempts < max_attempts:
            attempts += 1
            corridor_idx = random.randint(0, len(corridor_centers) - 1)
            rand_x = corridor_centers[corridor_idx]
            corridor_start_y = -maze_length / 2 + wall_thickness
            corridor_end_y = maze_length / 2 - wall_thickness
            rand_y = random.uniform(corridor_start_y, corridor_end_y)
            rand_z = top_platform_height
            if is_inside_wall(rand_x, rand_y, top_wall_segments, enemy_approx_radius):
                continue
            overlap = False
            for existing_enemy in enemies:
                dx = rand_x - existing_enemy.position[0]
                dy = rand_y - existing_enemy.position[1]
                dist_sq = dx * dx + dy * dy
                existing_scale = existing_enemy.size / playersize
                existing_radius = max(
                    10 * existing_scale + 5 * existing_scale,
                    15 * existing_scale * 0.5,
                    10 * existing_scale,
                    12 * existing_scale + 3 * existing_scale
                ) * 1.2
                if dist_sq < (enemy_approx_radius + existing_radius) ** 2:
                    overlap = True
                    break
            if overlap:
                continue
            enemies.append(Enemy(enemy_type, size, body_color, head_color, [rand_x, rand_y, rand_z]))
            placed = True
        if not placed:
            print(f"Warning: Could not place {enemy_type} enemy after {max_attempts} attempts.")

def draw_maze():
    glColor3f(0.8, 0.8, 0.8)
    glBegin(GL_QUADS)
    glVertex3f(-platform_size[0] / 2, -platform_size[1] / 2, top_platform_height)
    glVertex3f(platform_size[0] / 2, -platform_size[1] / 2, top_platform_height)
    glVertex3f(platform_size[0] / 2, platform_size[1] / 2, top_platform_height)
    glVertex3f(-platform_size[0] / 2, platform_size[1] / 2, top_platform_height)
    glEnd()
    glColor3f(0.0, 0.6, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-maze_width / 2, -maze_length / 2, top_platform_height)
    glVertex3f(-maze_width / 2, maze_length / 2, top_platform_height)
    glVertex3f(-maze_width / 2, maze_length / 2, top_platform_height + maze_height)
    glVertex3f(-maze_width / 2, -maze_length / 2, top_platform_height + maze_height)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(maze_width / 2, -maze_length / 2, top_platform_height)
    glVertex3f(maze_width / 2, maze_length / 2, top_platform_height)
    glVertex3f(maze_width / 2, maze_length / 2, top_platform_height + maze_height)
    glVertex3f(maze_width / 2, -maze_length / 2, top_platform_height + maze_height)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(-maze_width / 2, -maze_length / 2, top_platform_height)
    glVertex3f(maze_width / 2, -maze_length / 2, top_platform_height)
    glVertex3f(maze_width / 2, -maze_length / 2, top_platform_height + maze_height)
    glVertex3f(-maze_width / 2, -maze_length / 2, top_platform_height + maze_height)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(-maze_width / 2, maze_length / 2, top_platform_height)
    glVertex3f(maze_width / 2, maze_length / 2, top_platform_height)
    glVertex3f(maze_width / 2, maze_length / 2, top_platform_height + maze_height)
    glVertex3f(-maze_width / 2, maze_length / 2, top_platform_height + maze_height)
    glEnd()
    corridor_spacing = (maze_width - 5 * wall_thickness) / 4
    top_wall_segments.clear()
    for i in range(1, 4):
        wall_x_start = -maze_width / 2 + i * (corridor_spacing + wall_thickness)
        wall_x_end = wall_x_start + wall_thickness
        glColor3f(1.0, 0.8, 0.0)
        if i % 2 == 1:
            start_y = -maze_length / 2
            end_y = start_y + (maze_length * 4 / 5)
        else:
            start_y = -maze_length / 2 + (maze_length * 1 / 5)
            end_y = -maze_length / 2 + maze_length
        top_wall_segments.append((wall_x_start, start_y, end_y, wall_thickness))
        glBegin(GL_QUADS)
        glVertex3f(wall_x_start, start_y, top_platform_height)
        glVertex3f(wall_x_end, start_y, top_platform_height)
        glVertex3f(wall_x_end, end_y, top_platform_height)
        glVertex3f(wall_x_start, end_y, top_platform_height)
        glVertex3f(wall_x_start, start_y, top_platform_height + maze_height)
        glVertex3f(wall_x_end, start_y, top_platform_height + maze_height)
        glVertex3f(wall_x_end, end_y, top_platform_height + maze_height)
        glVertex3f(wall_x_start, end_y, top_platform_height + maze_height)
        glVertex3f(wall_x_start, start_y, top_platform_height)
        glVertex3f(wall_x_start, start_y, top_platform_height + maze_height)
        glVertex3f(wall_x_start, end_y, top_platform_height + maze_height)
        glVertex3f(wall_x_start, end_y, top_platform_height)
        glVertex3f(wall_x_end, start_y, top_platform_height)
        glVertex3f(wall_x_end, end_y, top_platform_height)
        glVertex3f(wall_x_end, end_y, top_platform_height + maze_height)
        glVertex3f(wall_x_end, start_y, top_platform_height + maze_height)
        glVertex3f(wall_x_start, start_y, top_platform_height)
        glVertex3f(wall_x_end, start_y, top_platform_height)
        glVertex3f(wall_x_end, start_y, top_platform_height + maze_height)
        glVertex3f(wall_x_start, start_y, top_platform_height + maze_height)
        glVertex3f(wall_x_start, end_y, top_platform_height)
        glVertex3f(wall_x_start, end_y, top_platform_height + maze_height)
        glVertex3f(wall_x_end, end_y, top_platform_height + maze_height)
        glVertex3f(wall_x_end, end_y, top_platform_height)
        glEnd()
    draw_portal()

def draw_portal():
    global portal_rotation
    if not found_portal:
        glPushMatrix()
        glTranslatef(portal_position[0], portal_position[1], top_platform_height + portal_size / 2)
        portal_rotation += 1
        glRotatef(portal_rotation, 0, 0, 1)
        glColor3f(0.3, 0.1, 0.6)
        draw_torus(10, portal_size, 20, 20)
        glColor3f(0.1, 0.7, 0.9)
        for i in range(0, 360, 20):
            glPushMatrix()
            glRotatef(i, 0, 0, 1)
            glTranslatef(portal_size / 4, 0, 0)
            draw_sphere(5, 10, 10)
            glPopMatrix()
        glPopMatrix()

def draw_bottom_platform():
    glColor3f(0.8, 0.8, 0.8)
    glBegin(GL_QUADS)
    glVertex3f(-platform_size[0] / 2, -platform_size[1] / 2, bottom_platform_height)
    glVertex3f(platform_size[0] / 2, -platform_size[1] / 2, bottom_platform_height)
    glVertex3f(platform_size[0] / 2, platform_size[1] / 2, bottom_platform_height)
    glVertex3f(-platform_size[0] / 2, platform_size[1] / 2, bottom_platform_height)
    glEnd()
    glColor3f(0.5, 0.3, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-maze_width / 2, -maze_length / 2, bottom_platform_height)
    glVertex3f(-maze_width / 2, maze_length / 2, bottom_platform_height)
    glVertex3f(-maze_width / 2, maze_length / 2, bottom_platform_height + maze_height)
    glVertex3f(-maze_width / 2, -maze_length / 2, bottom_platform_height + maze_height)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(maze_width / 2, -maze_length / 2, bottom_platform_height)
    glVertex3f(maze_width / 2, maze_length / 2, bottom_platform_height)
    glVertex3f(maze_width / 2, maze_length / 2, bottom_platform_height + maze_height)
    glVertex3f(maze_width / 2, -maze_length / 2, bottom_platform_height + maze_height)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(-maze_width / 2, -maze_length / 2, bottom_platform_height)
    glVertex3f(maze_width / 2, -maze_length / 2, bottom_platform_height)
    glVertex3f(maze_width / 2, -maze_length / 2, bottom_platform_height + maze_height)
    glVertex3f(-maze_width / 2, -maze_length / 2, bottom_platform_height + maze_height)
    glEnd()
    glBegin(GL_QUADS)
    glVertex3f(-maze_width / 2, maze_length / 2, bottom_platform_height)
    glVertex3f(maze_width / 2, maze_length / 2, bottom_platform_height)
    glVertex3f(maze_width / 2, maze_length / 2, bottom_platform_height + maze_height)
    glVertex3f(-maze_width / 2, maze_length / 2, bottom_platform_height + maze_height)
    glEnd()
    corridor_spacing = (maze_width - 5 * wall_thickness) / 4
    bottom_wall_segments.clear()
    for i in range(1, 4):
        wall_x_start = -maze_width / 2 + i * (corridor_spacing + wall_thickness)
        wall_x_end = wall_x_start + wall_thickness
        glColor3f(0.6, 0.4, 0.2)
        if i % 2 == 1:
            start_y = -maze_length / 2
            end_y = start_y + (maze_length * 4 / 5)
        else:
            start_y = -maze_length / 2 + (maze_length * 1 / 5)
            end_y = -maze_length / 2 + maze_length
        bottom_wall_segments.append((wall_x_start, start_y, end_y, wall_thickness))
        glBegin(GL_QUADS)
        glVertex3f(wall_x_start, start_y, bottom_platform_height)
        glVertex3f(wall_x_end, start_y, bottom_platform_height)
        glVertex3f(wall_x_end, end_y, bottom_platform_height)
        glVertex3f(wall_x_start, end_y, bottom_platform_height)
        glVertex3f(wall_x_start, start_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_end, start_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_end, end_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_start, end_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_start, start_y, bottom_platform_height)
        glVertex3f(wall_x_start, start_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_start, end_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_start, end_y, bottom_platform_height)
        glVertex3f(wall_x_end, start_y, bottom_platform_height)
        glVertex3f(wall_x_end, end_y, bottom_platform_height)
        glVertex3f(wall_x_end, end_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_end, start_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_start, start_y, bottom_platform_height)
        glVertex3f(wall_x_end, start_y, bottom_platform_height)
        glVertex3f(wall_x_end, start_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_start, start_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_start, end_y, bottom_platform_height)
        glVertex3f(wall_x_start, end_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_end, end_y, bottom_platform_height + maze_height)
        glVertex3f(wall_x_end, end_y, bottom_platform_height)
        glEnd()

def drawplayer():
    glPushMatrix()
    glTranslatef(playerpos[0], playerpos[1], playerpos[2])
    glRotatef(playerrot, 0, 0, 1)
    leg_base_radius = 5
    leg_height = 15
    glColor3f(0.5, 0.3, 0.1)
    for i in [-1, 1]:
        glPushMatrix()
        glTranslatef(i * 10, 0, 0)
        glRotatef(90, 1, 0, 0)
        draw_cone(leg_base_radius, leg_height, 10, 10)
        glPopMatrix()
    body_width = 15
    body_depth = 10
    body_height = 30
    glColor3f(0.1, 0.5, 0.8)
    glPushMatrix()
    glTranslatef(0, 0, body_height * 0.5)
    glScalef(body_width, body_depth, body_height)
    draw_cube(1)
    glPopMatrix()
    head_radius = 10
    glColor3f(1, 0.8, 0.6)
    glPushMatrix()
    glTranslatef(0, 0, body_height + head_radius)
    draw_sphere(head_radius, 20, 20)
    glPopMatrix()
    arm_radius = 3
    arm_height = 45
    glColor3f(0.1, 0.5, 0.8)
    for i in [-1, 1]:
        glPushMatrix()
        arm_z_position = 25
        glTranslatef(i * 12, 0, arm_z_position)
        glRotatef(45, 0, 1, 0)
        glRotatef(-90, 1, 0, 0)
        draw_cylinder(arm_radius, arm_radius, arm_height, 10, 10)
        if i == 1:
            glColor3f(0.3, 0.3, 0.3)
            glTranslatef(0, 0, arm_height)
            glScalef(4, 4, 10)
            draw_cube(1)
        glPopMatrix()
    glPopMatrix()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def setupcam():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 1.25, 0.1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    rad = math.radians(-playerrot)
    dx = math.sin(rad)
    dy = math.cos(rad)
    player_head_z = playerpos[2] + 30 + 10
    ex = playerpos[0] + dx * 10
    ey = playerpos[1] + dy * 10
    ez = player_head_z - 5
    cx = ex + dx * 30
    cy = ey + dy * 30
    cz = ez - 10
    gluLookAt(ex, ey, ez, cx, cy, cz, 0, 0, 1)

def key_up(key, x, y):
    global key_states
    if key in key_states:
        del key_states[key]

def keyboardListener(key, x, y):
    global playerrot, gameover, key_states, mouse_aim_enabled, mouse_aim_base_rotation, mouseX, mouseY
    if key == b'q':
        glutDestroyWindow(glutGetWindow())
        sys.exit(0)
    if gameover:
        if key == b'r':
            reset()
        return
    if key == b'e':
        mouse_aim_enabled = not mouse_aim_enabled
        if mouse_aim_enabled:
            screen_to_world_rotation(mouseX, mouseY, initialize=True)
        glutPostRedisplay()
        return
    key_states[key] = linger_frames
    glutPostRedisplay()

def screen_to_world_rotation(screen_x, screen_y, initialize=False):
    global playerrot, mouse_aim_base_rotation, mouse_aim_enabled
    if not mouse_aim_enabled and not initialize:
        return
    viewport = glGetIntegerv(GL_VIEWPORT)
    win_w, win_h = viewport[2], viewport[3]
    center_x, center_y = win_w // 2, win_h // 2
    delta_x = screen_x - center_x
    delta_y = center_y - screen_y
    if delta_x == 0 and delta_y == 0:
        return
    angle = math.degrees(math.atan2(delta_x, delta_y))
    if initialize:
        mouse_aim_base_rotation = playerrot - angle
    else:
        playerrot = (mouse_aim_base_rotation + angle) % 360

def mouseMoveListener(x, y):
    global mouse_aim_enabled, mouseX, mouseY
    mouseX, mouseY = x, y
    if mouse_aim_enabled:
        screen_to_world_rotation(x, y)
        glutPostRedisplay()

def mouseListener(button, state, x, y):
    global fire_cooldown, mouseX, mouseY, player_ammo
    mouseX, mouseY = x, y
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not gameover:
        if fire_cooldown <= 0 and player_ammo > 0:
            rad = math.radians(-playerrot)
            dir_x = math.sin(rad)
            dir_y = math.cos(rad)
            bullet_pos = [
                playerpos[0] + dir_x * 20,
                playerpos[1] + dir_y * 20,
                playerpos[2]
            ]
            bullets.append(Bullet(bullet_pos, [dir_x, dir_y, 0], "player"))
            fire_cooldown = fire_rate
            player_ammo -= 1

def check_collision(new_x, new_y):
    global on_ground
    player_base_z = playerpos[2] - player_height * 0.5
    player_radius = playersize / 2
    player_on_top = abs(player_base_z - top_platform_height) < maze_height / 2
    player_on_bottom = abs(player_base_z - bottom_platform_height) < maze_height / 2
    half_width = maze_width / 2
    half_length = maze_length / 2
    collision_tolerance = player_radius
    on_ground = False
    if (new_x - player_radius < -half_width + wall_thickness or
            new_x + player_radius > half_width - wall_thickness or
            new_y - player_radius < -half_length + wall_thickness or
            new_y + player_radius > half_length - wall_thickness):
        return True
    if player_on_top:
        if is_inside_wall(new_x, new_y, top_wall_segments, collision_tolerance):
            return True
        if abs(player_base_z - top_platform_height) < 5:
            on_ground = True
    elif player_on_bottom:
        if is_inside_wall(new_x, new_y, bottom_wall_segments, collision_tolerance):
            return True
        if abs(player_base_z - bottom_platform_height) < 5:
            on_ground = True
    return False

def check_portal_collision():
    global playerpos, found_portal, level
    player_base_z = playerpos[2] - player_height * 0.5
    player_on_top = abs(player_base_z - top_platform_height) < maze_height / 2
    if player_on_top and not found_portal:
        dx = playerpos[0] - portal_position[0]
        dy = playerpos[1] - portal_position[1]
        dz = playerpos[2] - (top_platform_height + portal_size / 2)
        dist_3d = math.sqrt(dx*dx + dy*dy + dz*dz)
        player_approx_radius = player_height * 0.5
        portal_sphere_radius = portal_size / 2
        if dist_3d < player_approx_radius + portal_sphere_radius:
            found_portal = True
            level += 1
            return True
    return False

def generate_maze(level):
    top_wall_segments.clear()
    bottom_wall_segments.clear()
    corridor_spacing = (maze_width - 5 * wall_thickness) / 4
    random.seed(level)
    for i in range(1, 4):
        wall_x_start = -maze_width / 2 + i * (corridor_spacing + wall_thickness)
        wall_x_end = wall_x_start + wall_thickness
        if random.choice([True, False]):
            start_y = -maze_length / 2
            end_y = start_y + (maze_length * 4 / 5)
        else:
            start_y = -maze_length / 2 + (maze_length * 1 / 5)
            end_y = -maze_length / 2 + maze_length
        top_wall_segments.append((wall_x_start, start_y, end_y, wall_thickness))
        bottom_wall_segments.append((wall_x_start, start_y, end_y, wall_thickness))
    portal_position[0] = maze_width / 2 - corridor_width / 2
    portal_position[1] = -maze_length / 2 + corridor_width / 2
    portal_position[2] = top_platform_height

def reset():
    global playerpos, playerrot, gameover, found_portal, enemies, player_lives, player_ammo, level
    corridor_spacing = (maze_width - 5 * wall_thickness) / 4
    playerpos[0] = -maze_width / 2 + wall_thickness + corridor_spacing / 2
    playerpos[1] = -maze_length / 2 + 100
    playerpos[2] = top_platform_height + player_height * 0.5
    playerrot = 0
    gameover = False
    found_portal = False
    player_lives = 10
    player_ammo = 10
    level = 1
    generate_maze(level)
    generate_enemies()
    generate_circular_obstacles()
    circular_obstacles.append((0, 0, 40))

def idle():
    global fire_cooldown
    update()
    if fire_cooldown > 0:
        fire_cooldown -= 1
    glutPostRedisplay()

def update():
    global playerpos, playerrot, gameover, found_portal, player_lives, mouse_aim_base_rotation
    global vertical_velocity, is_jumping, on_ground, forward_velocity
    if gameover:
        return
    dx, dy = 0, 0
    moved = False
    current_speed = playerspeed + (2 if level >= 2 else 0)
    if b'w' in key_states:
        rad = math.radians(-playerrot)
        dx += math.sin(rad) * current_speed
        dy += math.cos(rad) * current_speed
        moved = True
    if b's' in key_states:
        rad = math.radians(-playerrot)
        dx -= math.sin(rad) * current_speed
        dy -= math.cos(rad) * current_speed
        moved = True
    if not mouse_aim_enabled:
        if b'a' in key_states:
            playerrot = (playerrot + rotspeed) % 360
        if b'd' in key_states:
            playerrot = (playerrot - rotspeed) % 360
        if b'j' in key_states:
            playerrot = (playerrot + rotspeed) % 360
        if b'l' in key_states:
            playerrot = (playerrot - rotspeed) % 360
    if b'w' in key_states or b's' in key_states:
        new_x = playerpos[0] + dx
        new_y = playerpos[1] + dy
        if not check_collision(new_x, playerpos[1]):
            playerpos[0] = new_x
        if not check_collision(playerpos[0], new_y):
            playerpos[1] = new_y
    if b' ' in key_states and on_ground and not is_jumping:
        vertical_velocity = 10  
        rad = math.radians(-playerrot)  
        dx = math.sin(rad) * leap_speed  
        dy = math.cos(rad) * leap_speed * 2  
        forward_velocity = [dx, dy]  
        is_jumping = True
        on_ground = False
        forward_velocity = [dx, dy]
        vertical_velocity = 10  
        is_jumping = True
    if is_jumping or not on_ground:
        playerpos[2] += vertical_velocity
        vertical_velocity += gravity
        playerpos[0] += forward_velocity[0]
        playerpos[1] += forward_velocity[1]
        player_base_z = playerpos[2] - player_height * 0.5
        if player_base_z <= top_platform_height + 1 or player_base_z <= bottom_platform_height + 1:
            player_base_z = top_platform_height if abs(player_base_z - top_platform_height) < abs(
                player_base_z - bottom_platform_height) else bottom_platform_height
            playerpos[2] = player_base_z + player_height * 0.5
            vertical_velocity = 0
            forward_velocity = [0, 0]
            is_jumping = False
            on_ground = True
    keys_to_remove = []
    for k in key_states:
        key_states[k] -= 1
        if key_states[k] <= 0:
            keys_to_remove.append(k)
    for k in keys_to_remove:
        if k in key_states:
            del key_states[k]
    if not found_portal:
        check_portal_collision()
    player_base_z = playerpos[2] - player_height * 0.5
    for cx, cy, cr in circular_obstacles:
        dx = playerpos[0] - cx
        dy = playerpos[1] - cy
        dist = math.hypot(dx, dy)
        if dist < cr and abs(player_base_z - top_platform_height) < 5:
            gameover = True
    for enemy in enemies:
        enemy.update_rotation()
        if enemy.is_alive():
            enemy.shoot(playerpos)
    for bullet in bullets:
        bullet.update()
        player_base_z = playerpos[2] - player_height * 0.5
        player_on_top = abs(player_base_z - top_platform_height) < maze_height / 2
        wall_segments = top_wall_segments if player_on_top else bottom_wall_segments
        bullet_radius = 5
        if is_inside_wall(bullet.position[0], bullet.position[1], wall_segments, bullet_radius):
            bullet.alive = False
    bullets[:] = [b for b in bullets if b.alive]
    player_approx_radius = player_height * 0.5
    player_center_z = playerpos[2]
    player_collision_radius = 20
    for bullet in bullets:
        if bullet.source == "enemy":
            dx = bullet.position[0] - playerpos[0]
            dy = bullet.position[1] - playerpos[1]
            dz = bullet.position[2] - player_center_z
            dist_sq = dx * dx + dy * dy + dz * dz
            if dist_sq < (player_collision_radius + 5) ** 2:
                bullet.alive = False
                player_lives -= 1
                if player_lives <= 0:
                    gameover = True
    for enemy in enemies:
        enemy_base_z = enemy.position[2]
        enemy_on_top = abs(enemy_base_z - top_platform_height) < maze_height / 2
        player_base_z = playerpos[2] - player_height * 0.5
        player_on_top = abs(player_base_z - top_platform_height) < maze_height / 2
        if player_on_top and enemy_on_top:
            enemy_scale_factor = enemy.size / playersize
            enemy_body_height = 30 * enemy_scale_factor
            enemy_head_radius = 10 * enemy_scale_factor
            enemy_height_approx = (15 + 30 + 10) * enemy_scale_factor
            enemy_approx_radius = enemy_height_approx * 0.5
            player_center_z = player_base_z + player_height * 0.5
            enemy_center_z = enemy_base_z + enemy_height_approx * 0.5
            dist_sq = (playerpos[0] - enemy.position[0]) ** 2 + (playerpos[1] - enemy.position[1]) ** 2 + (
                        player_center_z - enemy_center_z) ** 2
            collision_distance_sq = (player_approx_radius + enemy_approx_radius) ** 2
            if dist_sq < collision_distance_sq:
                gameover = True
    for bullet in bullets:
        bullet.update()
    bullets[:] = [b for b in bullets if b.alive]
    player_base_z = playerpos[2] - player_height * 0.5
    player_on_top = abs(player_base_z - top_platform_height) < maze_height / 2
    for bullet in bullets:
        if bullet.source == "player":
            for enemy in enemies:
                enemy_base_z = enemy.position[2]
                enemy_on_top = abs(enemy_base_z - top_platform_height) < maze_height / 2
                if player_on_top == enemy_on_top:
                    dx = bullet.position[0] - enemy.position[0]
                    dy = bullet.position[1] - enemy.position[1]
                    dz = bullet.position[2] - enemy.position[2]
                    dist_sq = dx * dx + dy * dy + dz * dz
                    enemy_scale = enemy.size / playersize
                    body_width = 15 * enemy_scale
                    head_radius = 10 * enemy_scale
                    arm_horizontal = 12 * enemy_scale + 3 * enemy_scale
                    enemy_radius = max(body_width, head_radius, arm_horizontal) * 1.2
                    if dist_sq < (enemy_radius + 10) ** 2.5:
                        bullet.alive = False
                        enemy.lives -= 1
                        if not enemy.is_alive():
                            enemies.remove(enemy)
                        break

def drawhud():
    draw_text(10, 680, f"Aim Mode: {'Mouse' if mouse_aim_enabled else 'Keyboard'}", GLUT_BITMAP_HELVETICA_18)
    draw_text(10, 700, f"Lives: {player_lives}", GLUT_BITMAP_HELVETICA_18)
    draw_text(10, 720, f"Ammo: {player_ammo}", GLUT_BITMAP_HELVETICA_18)
    draw_text(10, 740, f"Level: {level}", GLUT_BITMAP_HELVETICA_18)
    if not found_portal:
        draw_text(10, 780, "Objective: Find the portal in the rightmost corridor")
    else:
        draw_text(10, 780, "Portal found! You've fallen to the bottom platform. Press 'r' to reset.")
    draw_text(10, 760, f"Player position: ({playerpos[0]:.1f}, {playerpos[1]:.1f}, {playerpos[2]:.1f})", GLUT_BITMAP_HELVETICA_12)
    if gameover:
        draw_text(400, 400, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(350, 370, "Press 'r' to restart", GLUT_BITMAP_HELVETICA_18)
    if player_ammo == 0:
        draw_text(500, 370, "CHECK YOUR BULLETS - RUN!!!!", GLUT_BITMAP_HELVETICA_18)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    setupcam()
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    light_position = [200, 200, 800, 1]
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    light_diffuse = [0.8, 0.8, 0.8, 1]
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glEnable(GL_COLOR_MATERIAL)
    draw_circular_obstacles()
    draw_maze()
    draw_bottom_platform()
    for enemy in enemies:
        enemy.draw()
    for bullet in bullets:
        bullet.draw()
    drawplayer()
    glDisable(GL_LIGHTING)
    glDisable(GL_COLOR_MATERIAL)
    drawhud()
    glutSwapBuffers()

#Main
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(1000, 800)
glutInitWindowPosition(0, 0)
wind = glutCreateWindow(b"Rogue Fracture with Enemies")
glEnable(GL_DEPTH_TEST)
corridor_spacing = (maze_width - 5 * wall_thickness) / 4
playerpos[0] = -maze_width / 2 + wall_thickness + corridor_spacing / 2
playerpos[1] = -maze_length / 2 + 100
playerpos[2] = top_platform_height
generate_enemies()
generate_circular_obstacles()
glutKeyboardUpFunc(key_up)
glutDisplayFunc(showScreen)
glutKeyboardFunc(keyboardListener)
glutPassiveMotionFunc(mouseMoveListener)
glutIdleFunc(idle)
glutMouseFunc(mouseListener)
glutIdleFunc(idle)
glClearColor(0.5, 0.7, 1.0, 1.0)
glutMainLoop()

