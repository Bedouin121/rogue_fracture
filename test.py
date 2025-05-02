from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys

camangle = 0
camheight = 500
camdistance = 500
firstperson = False
savedcam = (0, 500, 500)

key_states = {}
linger_frames = 10

wall_segments = []

gameover = False
found_portal = False
playerpos = [0, 0, 50]
playerrot = 0
playerspeed = 5
rotspeed = 5
playersize = 30

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

def draw_maze():
    glColor3f(0.8, 0.8, 0.8)
    glBegin(GL_QUADS)
    glVertex3f(-platform_size[0] / 2, -platform_size[1] / 2, top_platform_height)
    glVertex3f(platform_size[0] / 2, -platform_size[1] / 2, top_platform_height)
    glVertex3f(platform_size[0] / 2, platform_size[1] / 2, top_platform_height)
    glVertex3f(-platform_size[0] / 2, platform_size[1] / 2, top_platform_height)
    glEnd()

    glColor3f(0.5, 0.3, 0.2)

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

    wall_segments.clear()

    for i in range(1, 4):
        wall_x = -maze_width / 2 + i * (corridor_spacing + wall_thickness)
        glColor3f(0.6, 0.4, 0.2)

        if i % 2 == 1:
            start_y = -maze_length / 2
            end_y = start_y + (maze_length * 4 / 5)
        else:
            start_y = -maze_length / 2 + (maze_length * 1 / 5)
            end_y = -maze_length / 2 + maze_length

        wall_segments.append((wall_x, start_y, end_y))

        glBegin(GL_QUADS)
        glVertex3f(wall_x, start_y, top_platform_height)
        glVertex3f(wall_x, end_y, top_platform_height)
        glVertex3f(wall_x, end_y, top_platform_height + maze_height)
        glVertex3f(wall_x, start_y, top_platform_height + maze_height)
        glEnd()

    draw_portal()

def draw_portal():
    global portal_rotation

    glPushMatrix()
    glTranslatef(portal_position[0], portal_position[1], portal_position[2] + portal_size / 2)
    portal_rotation += 1
    glRotatef(portal_rotation, 0, 0, 1)

    glColor3f(0.3, 0.1, 0.6)
    glutSolidTorus(10, portal_size / 2, 20, 20)

    glColor3f(0.1, 0.7, 0.9)
    for i in range(0, 360, 20):
        glPushMatrix()
        glRotatef(i, 0, 0, 1)
        glTranslatef(portal_size / 4, 0, 0)
        glutSolidSphere(5, 10, 10)
        glPopMatrix()

    glPopMatrix()

def drawplayer():
    glPushMatrix()
    glTranslatef(playerpos[0], playerpos[1], playerpos[2])
    glRotatef(playerrot, 0, 0, 1)

    glColor3f(0.5, 0.3, 0.1)
    for i in [-1, 1]:
        glPushMatrix()
        glTranslatef(i * 10, 0, 0)
        glRotatef(-90, 1, 0, 0)
        glutSolidCone(5, 15, 10, 10)
        glPopMatrix()

    glColor3f(0.1, 0.5, 0.8)
    glPushMatrix()
    glTranslatef(0, 0, 15)
    glScalef(15, 10, 30)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(1, 0.8, 0.6)
    glPushMatrix()
    glTranslatef(0, 0, 45)
    glutSolidSphere(10, 20, 20)
    glPopMatrix()

    glColor3f(0.1, 0.5, 0.8)
    for i in [-1, 1]:
        glPushMatrix()
        glTranslatef(i * 12, 0, 25)
        glRotatef(45, 0, 1, 0)
        glRotatef(-90, 1, 0, 0)
        glutSolidCylinder(3, 45, 10, 10)
        glPopMatrix()

    glPopMatrix()

def setupcam():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 1.25, 0.1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    global firstperson, savedcam

    if firstperson:
        rad = math.radians(-playerrot)
        dx = math.sin(rad)
        dy = math.cos(rad)

        ex = playerpos[0] + dx * 10
        ey = playerpos[1] + dy * 10
        ez = playerpos[2] + 40

        cx = ex + dx * 30
        cy = ey + dy * 30
        cz = ez - 10

        gluLookAt(ex, ey, ez, cx, cy, cz, 0, 0, 1)
    else:
        rad = math.radians(camangle)
        cx = math.sin(rad) * camdistance
        cy = math.cos(rad) * camdistance
        cz = camheight
        gluLookAt(cx, cy, cz, 0, 0, 0, 0, 0, 1)

def specialkeys(key, x, y):
    global camangle, camheight
    if key == GLUT_KEY_UP:
        camheight += 10
    elif key == GLUT_KEY_DOWN:
        camheight -= 10
    elif key == GLUT_KEY_LEFT:
        camangle += 5
    elif key == GLUT_KEY_RIGHT:
        camangle -= 5
    camangle %= 360
    glutPostRedisplay()

def key_up(key, x, y):
    global key_states
    key = key.lower()
    pass

def keys(key, x, y):
    global playerrot, playerpos, gameover, firstperson, key_states, savedcam, camangle, camheight, camdistance

    if key == b'q':
        glutDestroyWindow(glutGetWindow())
        sys.exit(0)

    if gameover:
        if key == b'r':
            reset()
        return

    key_states[key] = linger_frames

    if key == b'v':
        if not firstperson:
            savedcam = (camangle, camheight, camdistance)
            firstperson = True
        else:
            camangle, camheight, camdistance = savedcam
            firstperson = False

    glutPostRedisplay()

def mouseclick(button, state, x, y):
    global firstperson, savedcam, camangle, camheight, camdistance
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN and not gameover:
        if not firstperson:
            savedcam = (camangle, camheight, camdistance)
            firstperson = True
        else:
            camangle, camheight, camdistance = savedcam
            firstperson = False
        glutPostRedisplay()

def check_collision(new_x, new_y):
    player_radius = playersize / 2
    if playerpos[2] < top_platform_height:
        return False

    if (new_x - player_radius < -maze_width / 2 or
            new_x + player_radius > maze_width / 2 or
            new_y - player_radius < -maze_length / 2 or
            new_y + player_radius > maze_length / 2):
        return True

    corridor_spacing = (maze_width - 5 * wall_thickness) / 4
    wall_start_y = -maze_length / 2
    wall_end_y = wall_start_y + (maze_length * 4 / 5)

    for wall_x, start_y, end_y in wall_segments:
        if (wall_x - player_radius <= new_x <= wall_x + wall_thickness + player_radius and
                start_y <= new_y <= end_y):
            return True

    return False

def check_portal_collision():
    global playerpos, found_portal

    dx = playerpos[0] - portal_position[0]
    dy = playerpos[1] - portal_position[1]
    distance = math.sqrt(dx * dx + dy * dy)

    if distance < portal_size / 2:
        found_portal = True
        playerpos[2] = bottom_platform_height + 50
        playerpos[0] = 0
        playerpos[1] = 0
        return True

    return False

def update():
    global playerpos, playerrot, gameover

    for k in list(key_states.keys()):
        if key_states[k] > 0:
            key_states[k] -= 1

    if not gameover:
        dx, dy = 0, 0

        if key_states.get(b'w', 0) > 0:
            rad = math.radians(-playerrot)
            dx = math.sin(rad) * playerspeed
            dy = math.cos(rad) * playerspeed
        if key_states.get(b's', 0) > 0:
            rad = math.radians(-playerrot)
            dx = -math.sin(rad) * playerspeed
            dy = -math.cos(rad) * playerspeed
        if key_states.get(b'a', 0) > 0:
            playerrot += rotspeed
        if key_states.get(b'd', 0) > 0:
            playerrot -= rotspeed

        playerrot %= 360

        new_x = playerpos[0] + dx
        new_y = playerpos[1] + dy

        if not check_collision(new_x, playerpos[1]):
            playerpos[0] = new_x
        if not check_collision(playerpos[0], new_y):
            playerpos[1] = new_y

        if not found_portal:
            check_portal_collision()

    glutPostRedisplay()

def drawhud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(1, 1, 1)

    glRasterPos2f(10, 780)
    t = "Controls: WASD to move, V or right-click to toggle view, Q to quit"
    for c in t:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

    glRasterPos2f(10, 760)
    if not found_portal:
        t = "Objective: Find the portal in the rightmost corridor"
    else:
        t = "Portal found! You've fallen to the bottom platform"
    for c in t:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_bottom_floor():
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_QUADS)
    glVertex3f(-platform_size[0] / 2, -platform_size[1] / 2, bottom_platform_height)
    glVertex3f(platform_size[0] / 2, -platform_size[1] / 2, bottom_platform_height)
    glVertex3f(platform_size[0] / 2, platform_size[1] / 2, bottom_platform_height)
    glVertex3f(-platform_size[0] / 2, platform_size[1] / 2, bottom_platform_height)
    glEnd()

def draw():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glViewport(0, 0, 1000, 800)
    setupcam()

    draw_maze()
    draw_bottom_floor()
    drawplayer()
    drawhud()

    glutSwapBuffers()

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GL_DEPTH)
glutInitWindowSize(1000, 800)
glutCreateWindow(b"3D Maze Game")
glEnable(GL_DEPTH_TEST)

corridor_spacing = (maze_width - 5 * wall_thickness) / 4
playerpos[0] = -maze_width / 2 + wall_thickness + corridor_spacing / 2
playerpos[1] = -maze_length / 2 + 100

glutKeyboardUpFunc(key_up)
glutDisplayFunc(draw)
glutSpecialFunc(specialkeys)
glutKeyboardFunc(keys)
glutMouseFunc(mouseclick)
glutIdleFunc(update)
glutMainLoop()