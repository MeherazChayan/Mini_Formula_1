from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_STROKE_ROMAN
import math
import sys

# -----------------------------
# Window / World
# -----------------------------
WIN_W, WIN_H = 1000, 800
WORLD_W, WORLD_H = 2000, 1600
TARGET_FPS = 60
LAPS_TO_FINISH = 1

# -----------------------------
# Visual
# -----------------------------
DRAW_CURBS = True
SHOW_CHECKPOINT = False  # normal toggle (non-cheat)

FINISH_DEPTH = 90.0
FINISH_COLS = 16
FINISH_ROWS = 4

# FPP camera size in world units (smaller = more zoom)
FPP_VIEW_W = 900.0
FPP_VIEW_H = 650.0
FPP_CAR_SCREEN_OFFSET = 0.28  # car stays slightly below center

# -----------------------------
# Car physics
# -----------------------------
CAR_L = 60.0
CAR_W = 30.0

ACCEL = 520.0
BRAKE = 760.0
FRICTION = 300.0
MAX_FWD = 520.0
MAX_REV = 220.0
STEER_DEG = 170.0
STEER_DEG_SLOW = 95.0

# -----------------------------
# 3D TPP Camera (Assignment-3 style)
# -----------------------------
TPP_3D_ENABLED = True
tpp_yaw_offset = 0.0
tpp_pitch_deg = 35.0
tpp_dist = 1050.0
tpp_fov = 62.0

# 3D TPP Camera (Assignment-3 style)
# -----------------------------
TPP_3D_ENABLED = True
tpp_yaw_offset = 0.0
tpp_pitch_deg = 35.0
tpp_dist = 1050.0
tpp_fov = 62.0

# First Person View (3D)
FPP_FOV_DEFAULT = 90.0
FPP_FOV_MIN = 60.0
FPP_FOV_MAX = 120.0
FPP_FOV_STEP = 8.0
FPP_YAW_STEP = 4.0

FPP_EYE_HEIGHT = 90.0          # Height of driver's eyes above track
FPP_EYE_BACK_OFFSET = 30.0     # How far behind car center the eyes are
FPP_LOOK_AHEAD = 400.0         # Distance to look-at point
FPP_PITCH_DOWN_DEG = 12.0      # Slight downward tilt for road view
fpp_fov = FPP_FOV_DEFAULT


# -----------------------------
# Cheat mode
# -----------------------------
cheat_on = False          # C toggles
cheat_auto = False        # P toggles autopilot (only when cheat_on)
# Nitro is "hold N" while cheat_on

CHEAT_NITRO_MAX_MULT = 1.70
CHEAT_NITRO_ACCEL_MULT = 1.80
CHEAT_NITRO_FRICTION_MULT = 0.60
CHEAT_WALL_PENALTY_NORMAL = 0.78
CHEAT_WALL_PENALTY_REDUCED = 0.95

# autopilot escape (requested: if it hits border, auto turn left)
auto_bump_cd = 0.0          # seconds
AUTO_BUMP_COOLDOWN = 0.35
AUTO_BUMP_TURN_DEG = 55.0   # turn left amount
AUTO_BUMP_PUSH_IN = 28.0    # push inward from edge

# FPP camera smoothing / auto-align
fpp_cam_ang = 0.0

# NEW: FPP manual camera control (arrow keys in FPP mode)
fpp_yaw_offset = 0.0
FPP_YAW_STEP = 4.0

# Optional: FPP zoom using UP/DOWN arrows
fpp_view_w = FPP_VIEW_W
fpp_view_h = FPP_VIEW_H
FPP_ZOOM_STEP = 40.0
FPP_VIEW_MIN_W = 600.0
FPP_VIEW_MAX_W = 1500.0

# -----------------------------
# Game state
# -----------------------------
STATE_TRACK_MENU = 0
STATE_TEAM_MENU = 1
STATE_RACE = 2
STATE_RESULTS = 3

state = STATE_TRACK_MENU
selected_track = 0
selected_team = 0

car_x = 0.0
car_y = 0.0
car_ang = 0.0
car_v = 0.0

lap = 0
checkpoint_passed = False
finished = False

# NEW: pause
paused = False

keys_down = set()
last_ms = 0
race_now_ms = 0
player_finish_ms = None

cam_x, cam_y = 0.0, 0.0
fpp_mode = False

results_lines = []
opponents = []  # dicts: {"team","s","speed","lat","lap","cp","finished","finish_ms"}

# -----------------------------
# Teams (10)
# -----------------------------
TEAMS = [
    ("McLaren",         (1.00, 0.45, 0.00)),
    ("Mercedes",        (0.00, 0.85, 0.75)),
    ("Red Bull Racing", (0.06, 0.10, 0.35)),
    ("Ferrari",         (0.85, 0.05, 0.08)),
    ("Williams",        (0.00, 0.35, 0.95)),
    ("Racing Bulls",    (0.12, 0.28, 0.70)),
    ("Aston Martin",    (0.00, 0.40, 0.25)),
    ("Haas F1 Team",    (0.90, 0.90, 0.90)),
    ("Kick Sauber",     (0.00, 0.80, 0.30)),
    ("Alpine",          (0.25, 0.45, 1.00)),
]

def team_name():
    return TEAMS[selected_team][0]

def team_color():
    return TEAMS[selected_team][1]

# -----------------------------
# Helpers
# -----------------------------
def clamp(v, a, b):
    return a if v < a else b if v > b else v

def normalize_angle_deg(a):
    while a > 180.0:
        a -= 360.0
    while a < -180.0:
        a += 360.0
    return a

def unit(x, y):
    L = math.hypot(x, y)
    if L < 1e-9:
        return 1.0, 0.0
    return x / L, y / L

def set_ortho(left, right, bottom, top):
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(left, right, bottom, top)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def draw_rect(x, y, w, h, filled=True):
    if filled:
        glBegin(GL_QUADS)
        glVertex2f(x, y);     glVertex2f(x+w, y)
        glVertex2f(x+w, y+h); glVertex2f(x, y+h)
        glEnd()
    else:
        glBegin(GL_LINE_LOOP)
        glVertex2f(x, y);     glVertex2f(x+w, y)
        glVertex2f(x+w, y+h); glVertex2f(x, y+h)
        glEnd()

def draw_cross(x, y, s=10.0):
    glBegin(GL_LINES)
    glVertex2f(x - s, y); glVertex2f(x + s, y)
    glVertex2f(x, y - s); glVertex2f(x, y + s)
    glEnd()

def seg_intersect(p1, p2, q1, q2):
    def orient(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def on_seg(a, b, c):
        return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0]) and
                min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))

    o1 = orient(p1, p2, q1)
    o2 = orient(p1, p2, q2)
    o3 = orient(q1, q2, p1)
    o4 = orient(q1, q2, p2)

    if (o1 > 0) != (o2 > 0) and (o3 > 0) != (o4 > 0):
        return True

    if abs(o1) < 1e-9 and on_seg(p1, p2, q1): return True
    if abs(o2) < 1e-9 and on_seg(p1, p2, q2): return True
    if abs(o3) < 1e-9 and on_seg(q1, q2, p1): return True
    if abs(o4) < 1e-9 and on_seg(q1, q2, p2): return True
    return False

# -----------------------------
# Stroke text
# -----------------------------
def stroke_text_width(text):
    w = 0
    for ch in text:
        w += glutStrokeWidth(GLUT_STROKE_ROMAN, ord(ch))
    return w

def draw_stroke_text(text, x, y, px_height=28, center=True):
    scale = px_height / 119.0
    w = stroke_text_width(text) * scale
    if center:
        x -= w * 0.5
    glPushMatrix()
    glTranslatef(x, y, 0.0)
    glScalef(scale, scale, 1.0)
    for ch in text:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(ch))
    glPopMatrix()

# -----------------------------
# Geometry: infinite line intersection
# -----------------------------
def line_intersection(p1, p2, p3, p4):
    x1, y1 = p1; x2, y2 = p2
    x3, y3 = p3; x4, y4 = p4
    den = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    if abs(den) < 1e-9:
        return None
    px = ((x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)) / den
    py = ((x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)) / den
    return (px, py)

    def draw(self):
        glPushMatrix()
        glTranslatef(0.0, 0.0, 0.00)
        glColor3f(0.10, 0.45, 0.18)
        draw_rect(0, 0, WORLD_W, WORLD_H, True)
        glPopMatrix()

        if DRAW_CURBS:
            glPushMatrix()
            glTranslatef(0.0, 0.0, 0.05)
            glColor3f(0.65, 0.10, 0.10)
            glBegin(GL_TRIANGLE_STRIP)
            for i in range(len(self.left) + 1):
                idx = i % len(self.left)
                lx, ly = self.left[idx]
                ox, oy = self.outL[idx]
                outx, outy = lx + ox*self.curb, ly + oy*self.curb
                glVertex2f(outx, outy)
                glVertex2f(lx, ly)
            glEnd()

            glBegin(GL_TRIANGLE_STRIP)
            for i in range(len(self.right) + 1):
                idx = i % len(self.right)
                rx, ry = self.right[idx]
                ox, oy = self.outR[idx]
                outx, outy = rx + ox*self.curb, ry + oy*self.curb
                glVertex2f(outx, outy)
                glVertex2f(rx, ry)
            glEnd()
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0.0, 0.0, 0.10)
        glColor3f(0.18, 0.18, 0.20)
        glBegin(GL_TRIANGLE_STRIP)
        for i in range(len(self.left) + 1):
            li = self.left[i % len(self.left)]
            ri = self.right[i % len(self.right)]
            glVertex2f(li[0], li[1])
            glVertex2f(ri[0], ri[1])
        glEnd()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.0, 0.0, 0.12)
        self.draw_finish_grid()
        glPopMatrix()

        # Debug visuals are always ON when cheat_on (no V needed)
        if SHOW_CHECKPOINT or cheat_on:
            glPushMatrix()
            glTranslatef(0.0, 0.0, 0.14)

            (c, d) = self.cp_line
            glColor3f(0.95, 0.85, 0.15)
            glLineWidth(6.0)
            glBegin(GL_LINES)
            glVertex2f(c[0], c[1])
            glVertex2f(d[0], d[1])
            glEnd()

            (sa, sb) = self.start_line
            glColor3f(0.60, 0.85, 1.00)
            glBegin(GL_LINES)
            glVertex2f(sa[0], sa[1])
            glVertex2f(sb[0], sb[1])
            glEnd()

            cx, cy, _, _, _ = self.closest_point_and_dist(car_x, car_y)
            glColor3f(1.0, 1.0, 1.0)
            draw_cross(cx, cy, 12.0)

            glLineWidth(1.0)
            glPopMatrix()

    def draw_preview(self, x, y, w, h):
        glColor3f(0.10, 0.45, 0.18)
        draw_rect(x, y, w, h, True)

        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        bw = max(1.0, maxx - minx)
        bh = max(1.0, maxy - miny)

        pad = 8.0
        scale = min((w - 2*pad)/bw, (h - 2*pad)/bh)
        ox = x + pad + (w - 2*pad - bw*scale)*0.5
        oy = y + pad + (h - 2*pad - bh*scale)*0.5

        def S(p):
            return (ox + (p[0] - minx)*scale, oy + (p[1] - miny)*scale)

        if DRAW_CURBS:
            glColor3f(0.65, 0.10, 0.10)
            glBegin(GL_TRIANGLE_STRIP)
            for i in range(len(self.left) + 1):
                idx = i % len(self.left)
                lx, ly = self.left[idx]
                oxv, oyv = self.outL[idx]
                outx, outy = lx + oxv*self.curb, ly + oyv*self.curb
                a = S((outx, outy))
                b = S((lx, ly))
                glVertex2f(a[0], a[1])
                glVertex2f(b[0], b[1])
            glEnd()

            glBegin(GL_TRIANGLE_STRIP)
            for i in range(len(self.right) + 1):
                idx = i % len(self.right)
                rx, ry = self.right[idx]
                oxv, oyv = self.outR[idx]
                outx, outy = rx + oxv*self.curb, ry + oyv*self.curb
                a = S((outx, outy))
                b = S((rx, ry))
                glVertex2f(a[0], a[1])
                glVertex2f(b[0], b[1])
            glEnd()

        glColor3f(0.18, 0.18, 0.20)
        glBegin(GL_TRIANGLE_STRIP)
        for i in range(len(self.left) + 1):
            li = S(self.left[i % len(self.left)])
            ri = S(self.right[i % len(self.right)])
            glVertex2f(li[0], li[1])
            glVertex2f(ri[0], ri[1])
        glEnd()

# -----------------------------
# Tracks
# -----------------------------
TRACKS = [
    Track("Monza (Italy)",
          [(350, 520), (1500, 520), (1700, 680), (1700, 980),
           (1500, 1140), (350, 1140), (200, 980), (200, 680)],
          340),
    Track("Spa-Francorchamps (Belgium)",
          [(420, 420), (1200, 360), (1680, 640), (1760, 980),
           (1420, 1280), (820, 1340), (380, 1060), (320, 720)],
          320),
    Track("Silverstone (UK)",
          [(520, 520), (1320, 520), (1700, 760), (1560, 1160),
           (1120, 1360), (700, 1280), (420, 960), (420, 640)],
          320),
]

def cur_track():
    return TRACKS[selected_track]

# -----------------------------
# Camera / View transforms
# -----------------------------
def apply_view_transform():
    if fpp_mode:
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = float(WIN_W) / WIN_H if WIN_H > 0 else 1.0
        gluPerspective(fpp_fov, aspect, 10.0, 6000.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Combined view angle (auto-align + manual yaw offset)
        view_ang_deg = fpp_cam_ang + fpp_yaw_offset
        view_rad = math.radians(view_ang_deg)
        pitch_rad = math.radians(-FPP_PITCH_DOWN_DEG)

        # Forward direction with downward pitch
        dx = math.cos(view_rad) * math.cos(pitch_rad)
        dy = math.sin(view_rad) * math.cos(pitch_rad)
        dz = math.sin(pitch_rad)

        # Eye position (inside the car)
        eye_x = car_x - math.cos(view_rad) * FPP_EYE_BACK_OFFSET
        eye_y = car_y - math.sin(view_rad) * FPP_EYE_BACK_OFFSET
        eye_z = FPP_EYE_HEIGHT

        # Look-at point ahead
        center_x = eye_x + dx * FPP_LOOK_AHEAD
        center_y = eye_y + dy * FPP_LOOK_AHEAD
        center_z = eye_z + dz * FPP_LOOK_AHEAD

        gluLookAt(eye_x, eye_y, eye_z,
                  center_x, center_y, center_z,
                  0.0, 0.0, 1.0)
        return

    if TPP_3D_ENABLED:
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = max(1.0, float(WIN_W) / float(WIN_H))
        gluPerspective(tpp_fov, aspect, 2.0, 6000.0)

        base_yaw = car_ang + 180.0
        yaw = math.radians(base_yaw + tpp_yaw_offset)
        pitch = math.radians(clamp(tpp_pitch_deg, 10.0, 80.0))

        ex = car_x + math.cos(yaw) * math.cos(pitch) * tpp_dist
        ey = car_y + math.sin(yaw) * math.cos(pitch) * tpp_dist
        ez = 0.0 + math.sin(pitch) * tpp_dist + 80.0

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(ex, ey, ez, car_x, car_y, 0.0, 0.0, 0.0, 1.0)
        return

    glDisable(GL_DEPTH_TEST)
    set_ortho(0, WIN_W, 0, WIN_H)

# -----------------------------
# Opponents
# -----------------------------
def wrap_s(tr, s):
    if tr.total <= 0:
        return 0.0
    s %= tr.total
    if s < 0:
        s += tr.total
    return s

def crossed_s_mark(tr, prev_s, new_s, mark_s):
    mark_s = wrap_s(tr, mark_s)
    if prev_s <= new_s:
        return (prev_s < mark_s <= new_s)
    return (prev_s < mark_s <= tr.total) or (0.0 <= mark_s <= new_s)

def init_opponents():
    global opponents
    tr = cur_track()
    base_s = 80.0
    spacing = 120.0

    lane_pattern = [-0.32, 0.32, -0.20, 0.20, -0.10, 0.10, -0.26, 0.26, 0.0]
    lane_scale = tr.half * 0.62

    team_indices = [i for i in range(len(TEAMS)) if i != selected_team]
    opponents = []
    for k, ti in enumerate(team_indices):
        s = wrap_s(tr, base_s - (k + 1) * spacing)
        speed = 270.0 + (k % 3) * 30.0 + (ti % 4) * 12.0
        lat = lane_pattern[k % len(lane_pattern)] * lane_scale
        opponents.append({
            "team": ti,
            "s": s,
            "speed": speed,
            "lat": lat,
            "lap": 0,
            "cp": False,
            "finished": False,
            "finish_ms": None
        })

def opponent_pose(o):
    tr = cur_track()
    x, y, tx, ty = tr.point_at_s(o["s"])
    nx, ny = -ty, tx
    x += nx * o["lat"]
    y += ny * o["lat"]
    x, y, _ = tr.constrain_to_track(x, y)
    ang = math.degrees(math.atan2(ty, tx))
    return x, y, ang

def update_opponents(dt):
    tr = cur_track()
    for o in opponents:
        if o["finished"]:
            continue

        prev_s = o["s"]
        new_s = wrap_s(tr, prev_s + o["speed"] * dt)
        o["s"] = new_s

        if not o["cp"] and crossed_s_mark(tr, prev_s, new_s, tr.cp_s):
            o["cp"] = True

        wrapped = (new_s < prev_s)
        if wrapped and o["cp"]:
            o["lap"] += 1
            o["cp"] = False
            if o["lap"] >= LAPS_TO_FINISH:
                o["finished"] = True
                o["finish_ms"] = race_now_ms

def draw_opponents():
    for o in opponents:
        x, y, ang = opponent_pose(o)
        draw_f1_car_world(x, y, ang, TEAMS[o["team"]][1])

# -----------------------------
# Cheat actions
# -----------------------------
def cheat_teleport_next_checkpoint():
    global car_x, car_y, car_ang, car_v, checkpoint_passed
    tr = cur_track()
    if not checkpoint_passed:
        target_s = tr.cp_s - 35.0
    else:
        target_s = tr.total - 35.0

    x, y, tx, ty = tr.point_at_s(target_s)
    x, y, _ = tr.constrain_to_track(x, y)
    car_x, car_y = x, y
    car_ang = math.degrees(math.atan2(ty, tx))
    car_v = 0.0

# -----------------------------
# FPP camera auto angle
# -----------------------------
def update_fpp_camera_angle(dt):
    global fpp_cam_ang

    target = car_ang
    if fpp_mode and cheat_on and cheat_auto:
        cx, cy, tx, ty, _ = cur_track().closest_point_and_dist(car_x, car_y)
        target = math.degrees(math.atan2(ty, tx))

    if dt <= 0:
        fpp_cam_ang = target
        return

    diff = normalize_angle_deg(target - fpp_cam_ang)
    follow_speed = 10.0
    fpp_cam_ang = normalize_angle_deg(fpp_cam_ang + diff * clamp(follow_speed * dt, 0.0, 1.0))

# -----------------------------
# Results
# -----------------------------
def build_results():
    global results_lines
    tr = cur_track()
    total = tr.total

    p_s, _ = tr.closest_s(car_x, car_y)
    p_progress = lap * total + p_s

    entries = []
    entries.append((f"{team_name()} (You)", selected_team,
                    True,
                    player_finish_ms if player_finish_ms is not None else race_now_ms,
                    p_progress))

    for o in opponents:
        progress = o["lap"] * total + o["s"]
        entries.append((TEAMS[o["team"]][0], o["team"],
                        (o["finish_ms"] is not None),
                        o["finish_ms"],
                        progress))

    def sort_key(e):
        name, tidx, fin, finms, prog = e
        if fin:
            return (0, finms if finms is not None else 10**18, 0)
        return (1, 10**18, -prog)

    entries.sort(key=sort_key)

    results_lines = []
    for i, e in enumerate(entries, start=1):
        name, tidx, fin, finms, prog = e
        status = "FIN" if fin else "DNF"
        results_lines.append((i, name, tidx, status))

def end_race_and_build_results():
    global state, fpp_mode
    fpp_mode = False
    keys_down.clear()
    build_results()
    state = STATE_RESULTS

def draw_results_screen():
    set_ortho(0, WIN_W, 0, WIN_H)

    glColor3f(0.05, 0.07, 0.10)
    draw_rect(0, 0, WIN_W, WIN_H, True)

    card_w = WIN_W * 0.82
    card_h = WIN_H * 0.86
    cx = (WIN_W - card_w) * 0.5
    cy = (WIN_H - card_h) * 0.5

    glColor3f(0.0, 0.0, 0.0)
    draw_rect(cx, cy, card_w, card_h, True)

    glColor3f(0.18, 0.22, 0.30)
    draw_rect(cx + 6, cy + 6, card_w - 12, card_h - 12, True)

    pad_x = 50
    inner_left = cx + pad_x
    inner_right = cx + card_w - pad_x
    inner_w = inner_right - inner_left

    title_y = cy + card_h - 70
    sub_y = title_y - 45
    header_y = sub_y - 85
    divider_y = header_y - 18

    footer_y = cy + 45
    list_bottom = footer_y + 55
    list_top = divider_y - 30

    glColor3f(1.0, 1.0, 1.0)
    draw_stroke_text("Race Results", WIN_W * 0.5, title_y, px_height=34, center=True)

    glColor3f(0.92, 0.92, 0.92)
    draw_stroke_text(f"{cur_track().title}  |  Laps: {LAPS_TO_FINISH}",
                     WIN_W * 0.5, sub_y, px_height=18, center=True)

    glColor3f(0.90, 0.90, 0.90)
    draw_stroke_text("Pos", inner_left + 0, header_y, px_height=18, center=False)
    draw_stroke_text("Team", inner_left + 110, header_y, px_height=18, center=False)
    draw_stroke_text("Status", inner_left + inner_w - 120, header_y, px_height=18, center=False)

    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex2f(inner_left, divider_y)
    glVertex2f(inner_right, divider_y)
    glEnd()
    glLineWidth(1.0)

    N = max(1, len(results_lines))
    avail_h = max(120.0, list_top - list_bottom)
    row_gap = avail_h / N
    row_h = row_gap * 0.70
    row_font = clamp(row_gap * 0.55, 14, 22)

    pos_x = inner_left + 0
    team_x = inner_left + 110
    status_x = inner_left + inner_w - 120

    for idx, (rank, name, tidx, status) in enumerate(results_lines):
        y = list_top - (idx + 0.5) * row_gap

        if idx % 2 == 0:
            glColor3f(0.14, 0.16, 0.20)
            draw_rect(inner_left, y - row_h*0.5, inner_w, row_h, True)

        if "(You)" in name:
            glColor3f(0.08, 0.08, 0.09)
            draw_rect(inner_left, y - row_h*0.5, inner_w, row_h, True)

        r, g, b = TEAMS[tidx][1]
        glColor3f(r, g, b)
        draw_rect(team_x - 32, y - 11, 22, 22, True)
        glColor3f(0.0, 0.0, 0.0)
        draw_rect(team_x - 32, y - 11, 22, 22, False)

        glColor3f(1.0, 1.0, 1.0)
        draw_stroke_text(f"{rank}.", pos_x, y - 6, px_height=row_font, center=False)
        draw_stroke_text(name, team_x, y - 6, px_height=row_font, center=False)

        glColor3f(0.92, 0.92, 0.92)
        draw_stroke_text(status, status_x, y - 6, px_height=row_font, center=False)

    glColor3f(0.88, 0.88, 0.88)
    draw_stroke_text("R = restart   |   M = main menu   |   ESC = exit",
                     WIN_W * 0.5, footer_y, px_height=18, center=True)

# -----------------------------
# Player lap logic
# -----------------------------
def update_lap(prev_x, prev_y, new_x, new_y, vx, vy):
    global lap, checkpoint_passed, finished, player_finish_ms
    if finished:
        return

    tr = cur_track()
    p1 = (prev_x, prev_y)
    p2 = (new_x, new_y)

    cp_a, cp_b = tr.cp_line
    cp_tx, cp_ty = tr.cp_tan
    cp_forward = (vx * cp_tx + vy * cp_ty) > 0.0
    if seg_intersect(p1, p2, cp_a, cp_b) and cp_forward:
        checkpoint_passed = True

    st_a, st_b = tr.start_line
    st_tx, st_ty = tr.start_tan
    st_forward = (vx * st_tx + vy * st_ty) > 0.0
    if seg_intersect(p1, p2, st_a, st_b) and st_forward and checkpoint_passed:
        lap += 1
        checkpoint_passed = False
        if lap >= LAPS_TO_FINISH:
            finished = True
            player_finish_ms = race_now_ms
            end_race_and_build_results()

# -----------------------------
# Reset / Spawn
# -----------------------------
def reset_game():
    global car_x, car_y, car_ang, car_v, lap, checkpoint_passed, finished, player_finish_ms
    global fpp_cam_ang, auto_bump_cd, paused
    global fpp_yaw_offset, fpp_view_w, fpp_view_h

    tr = cur_track()
    sx, sy, tx, ty = tr.point_at_s(80.0)
    car_x, car_y = sx, sy
    car_ang = math.degrees(math.atan2(ty, tx))
    car_v = 0.0
    lap = 0
    checkpoint_passed = False
    finished = False
    player_finish_ms = None
    init_opponents()
    fpp_cam_ang = car_ang
    auto_bump_cd = 0.0
    paused = False

    # reset FPP manual camera settings
    fpp_yaw_offset = 0.0
    fpp_view_w = FPP_VIEW_W
    fpp_view_h = FPP_VIEW_H
    fpp_fov = FPP_FOV_DEFAULT 

# -----------------------------
# Player update
# -----------------------------
def update_player(dt):
    global car_x, car_y, car_ang, car_v, auto_bump_cd

    if auto_bump_cd > 0.0:
        auto_bump_cd = max(0.0, auto_bump_cd - dt)

    prev_x, prev_y = car_x, car_y

    w = ('w' in keys_down) or ('W' in keys_down)
    s = ('s' in keys_down) or ('S' in keys_down)
    a = ('a' in keys_down) or ('A' in keys_down)
    d = ('d' in keys_down) or ('D' in keys_down)

    auto_active = (cheat_on and cheat_auto and (not finished))

    # ---- Autopilot: lookahead + strong centering + "edge override" ----
    if auto_active:
        trk = cur_track()

        cx, cy, txc, tyc, _ = trk.closest_point_and_dist(car_x, car_y)
        nx, ny = -tyc, txc
        lat = (car_x - cx) * nx + (car_y - cy) * ny
        lat_n = lat / max(1.0, (trk.half - 15.0))

        spd = abs(car_v)
        lookahead = clamp(90.0 + spd * 0.20, 75.0, 175.0)
        s0, _ = trk.closest_s(car_x, car_y)
        txp, typ, _, _ = trk.point_at_s(s0 + lookahead)

        vx_t = txp - car_x
        vy_t = typ - car_y
        target_ang = math.degrees(math.atan2(vy_t, vx_t))
        ang_err = normalize_angle_deg(target_ang - car_ang)

        steer_cmd = clamp(ang_err * 0.032 + lat_n * 1.35, -1.0, 1.0)

        if abs(lat_n) > 0.62:
            steer_cmd = -math.copysign(1.0, lat_n)

        a = steer_cmd > 0.02
        d = steer_cmd < -0.02

        risk = clamp(abs(ang_err) / 55.0 + abs(lat_n) / 0.60, 0.0, 1.0)
        target_speed = 440.0 * (1.0 - 0.75 * risk) + 150.0 * risk
        if abs(lat_n) > 0.75:
            target_speed = min(target_speed, 260.0)

        if car_v < 0:
            w = True
            s = False
        else:
            w = (car_v < target_speed - 8.0)
            s = (car_v > target_speed + 18.0)

    nitro = cheat_on and (('n' in keys_down) or ('N' in keys_down))

    accel = ACCEL
    brake = BRAKE
    friction = FRICTION
    max_fwd = MAX_FWD
    max_rev = MAX_REV

    if nitro:
        accel *= CHEAT_NITRO_ACCEL_MULT
        friction *= CHEAT_NITRO_FRICTION_MULT
        max_fwd *= CHEAT_NITRO_MAX_MULT

    if finished:
        car_v *= (1.0 - 2.5 * dt)
        if abs(car_v) < 5:
            car_v = 0.0
    else:
        if w and not s:
            car_v += accel * dt
        elif s and not w:
            if car_v > 0:
                car_v -= brake * dt
            else:
                car_v -= accel * 0.85 * dt
        else:
            if car_v > 0:
                car_v -= friction * dt
                if car_v < 0: car_v = 0
            elif car_v < 0:
                car_v += friction * dt
                if car_v > 0: car_v = 0

        car_v = clamp(car_v, -max_rev, max_fwd)

        sp = abs(car_v)
        steer_rate = STEER_DEG_SLOW + (STEER_DEG - STEER_DEG_SLOW) * clamp(sp / 260.0, 0.0, 1.0)

        steer = 0.0
        if a and not d:
            steer = 1.0
        elif d and not a:
            steer = -1.0
        if car_v < 0:
            steer = -steer

        car_ang = normalize_angle_deg(car_ang + steer * steer_rate * dt)

    rad = math.radians(car_ang)
    fx, fy = math.cos(rad), math.sin(rad)
    vx = fx * car_v
    vy = fy * car_v

    car_x += vx * dt
    car_y += vy * dt

    car_x = clamp(car_x, 0.0, WORLD_W)
    car_y = clamp(car_y, 0.0, WORLD_H)

    tr = cur_track()

    if not tr.on_track(car_x, car_y):
        newx, newy, hit = tr.constrain_to_track(car_x, car_y)
        car_x, car_y = newx, newy

        car_v *= (CHEAT_WALL_PENALTY_REDUCED if cheat_on else CHEAT_WALL_PENALTY_NORMAL)

        if auto_active and hit and auto_bump_cd <= 0.0:
            car_ang = normalize_angle_deg(car_ang + AUTO_BUMP_TURN_DEG)
            cx, cy, txc, tyc, _ = tr.closest_point_and_dist(car_x, car_y)
            nx, ny = -tyc, txc
            car_x -= nx * AUTO_BUMP_PUSH_IN
            car_y -= ny * AUTO_BUMP_PUSH_IN
            car_v = max(car_v, 160.0)
            auto_bump_cd = AUTO_BUMP_COOLDOWN

    if auto_active:
        cx2, cy2, tx2, ty2, _ = tr.closest_point_and_dist(car_x, car_y)
        nx2, ny2 = -ty2, tx2
        lat2 = (car_x - cx2) * nx2 + (car_y - cy2) * ny2
        center_pull = 3.4
        car_x -= nx2 * lat2 * center_pull * dt
        car_y -= ny2 * lat2 * center_pull * dt

    update_lap(prev_x, prev_y, car_x, car_y, vx, vy)

# -----------------------------
# Car drawing
# -----------------------------
def draw_f1_car_world(x, y, ang_deg, color_rgb):
    r, g, b = color_rgb

    glPushMatrix()
    glTranslatef(x, y, 0.18)
    glRotatef(ang_deg, 0.0, 0.0, 1.0)

    L = CAR_L
    W = CAR_W

    glColor3f(0.06, 0.06, 0.07)
    def wheel(x0, y0, wx, wy):
        glBegin(GL_QUADS)
        glVertex2f(x0, y0)
        glVertex2f(x0+wx, y0)
        glVertex2f(x0+wx, y0+wy)
        glVertex2f(x0, y0+wy)
        glEnd()

    wheel( 0.20*L,  0.55*W, 0.22*L, 0.28*W)
    wheel( 0.20*L, -0.83*W, 0.22*L, 0.28*W)
    wheel(-0.55*L,  0.62*W, 0.26*L, 0.32*W)
    wheel(-0.55*L, -0.94*W, 0.26*L, 0.32*W)

    glColor3f(0.10, 0.10, 0.12)
    glBegin(GL_QUADS)
    glVertex2f(-0.95*L, -0.85*W)
    glVertex2f(-0.78*L, -0.85*W)
    glVertex2f(-0.78*L,  0.85*W)
    glVertex2f(-0.95*L,  0.85*W)
    glEnd()

    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex2f(-0.70*L, -0.22*W)
    glVertex2f( 0.55*L, -0.22*W)
    glVertex2f( 0.55*L,  0.22*W)
    glVertex2f(-0.70*L,  0.22*W)
    glEnd()

    glColor3f(r*0.92, g*0.92, b*0.92)
    glBegin(GL_QUADS)
    glVertex2f(-0.10*L,  0.22*W)
    glVertex2f( 0.45*L,  0.22*W)
    glVertex2f( 0.35*L,  0.52*W)
    glVertex2f(-0.10*L,  0.52*W)
    glEnd()

    glBegin(GL_QUADS)
    glVertex2f(-0.10*L, -0.22*W)
    glVertex2f( 0.45*L, -0.22*W)
    glVertex2f( 0.35*L, -0.52*W)
    glVertex2f(-0.10*L, -0.52*W)
    glEnd()

    glColor3f(r, g, b)
    glBegin(GL_TRIANGLES)
    glVertex2f(0.55*L,  0.14*W)
    glVertex2f(0.55*L, -0.14*W)
    glVertex2f(0.95*L,  0.00*W)
    glEnd()

    glColor3f(0.10, 0.10, 0.12)
    glBegin(GL_QUADS)
    glVertex2f(0.78*L, -0.88*W)
    glVertex2f(0.92*L, -0.88*W)
    glVertex2f(0.92*L,  0.88*W)
    glVertex2f(0.78*L,  0.88*W)
    glEnd()

    glColor3f(0.15, 0.15, 0.18)
    glBegin(GL_QUADS)
    glVertex2f(0.05*L, -0.16*W)
    glVertex2f(0.28*L, -0.16*W)
    glVertex2f(0.28*L,  0.16*W)
    glVertex2f(0.05*L,  0.16*W)
    glEnd()

    glColor3f(0.0, 0.0, 0.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f(-0.70*L, -0.22*W)
    glVertex2f( 0.55*L, -0.22*W)
    glVertex2f( 0.55*L,  0.22*W)
    glVertex2f(-0.70*L,  0.22*W)
    glEnd()
    glLineWidth(1.0)

    glPopMatrix()

# -----------------------------
# FPP cockpit overlay
# -----------------------------
def draw_cockpit_overlay():
    set_ortho(0, WIN_W, 0, WIN_H)

    glColor3f(0.04, 0.04, 0.05)
    draw_rect(0, 0, WIN_W, 160, True)

    cx = WIN_W * 0.5
    base_y = 20
    tip_y = 160

    r, g, b = team_color()

    glColor3f(r, g, b)
    glBegin(GL_TRIANGLES)
    glVertex2f(cx - 35, base_y + 20)
    glVertex2f(cx + 35, base_y + 20)
    glVertex2f(cx, tip_y - 10)
    glEnd()

    glColor3f(0.10, 0.10, 0.12)
    draw_rect(cx - 180, base_y + 40, 360, 18, True)

    glColor3f(0.06, 0.06, 0.07)
    draw_rect(cx - 220, base_y + 28, 55, 55, True)
    draw_rect(cx + 165, base_y + 28, 55, 55, True)

    glColor3f(0.90, 0.90, 0.90)
    draw_stroke_text("FIRST PERSON VIEW (Press Z to toggle)", WIN_W*0.5, 130, px_height=18, center=True)
    draw_stroke_text("← → Look around    ↑ ↓ Zoom", WIN_W*0.5, 100, px_height=16, center=True)
# -----------------------------
# HUD / Menus
# -----------------------------
def draw_hud():
    set_ortho(0, WIN_W, 0, WIN_H)

    glColor3f(0.0, 0.0, 0.0)
    draw_rect(0, WIN_H - 85, WIN_W, 85, True)

    glColor3f(1.0, 1.0, 1.0)
    draw_stroke_text(cur_track().title, WIN_W * 0.5, WIN_H - 58, px_height=24, center=True)

    y_text = WIN_H - 76
    px_h = 18
    scale = px_h / 119.0

    label = "Team:"
    glColor3f(0.90, 0.90, 0.90)
    draw_stroke_text(label, 24, y_text, px_height=px_h, center=False)

    label_w = stroke_text_width(label) * scale
    box_x = 24 + label_w + 14
    box_y = WIN_H - 78

    trc, tgc, tbc = team_color()
    glColor3f(trc, tgc, tbc)
    draw_rect(box_x, box_y, 22, 16, True)
    glColor3f(0.0, 0.0, 0.0)
    draw_rect(box_x, box_y, 22, 16, False)

    glColor3f(0.90, 0.90, 0.90)
    draw_stroke_text(team_name(), box_x + 22 + 10, y_text, px_height=px_h, center=False)

    if fpp_mode:
        view_label = "FPP"
    else:
        view_label = "TPP-3D" if TPP_3D_ENABLED else "TOP"
    glColor3f(0.90, 0.90, 0.90)
    draw_stroke_text(f"View: {view_label}", WIN_W - 210, WIN_H - 76, px_height=18, center=False)

    if cheat_on:
        nitro = (('n' in keys_down) or ('N' in keys_down))
        glColor3f(1.0, 0.35, 0.25)
        draw_stroke_text("CHEAT ON", WIN_W - 210, WIN_H - 54, px_height=16, center=False)

        glColor3f(0.90, 0.90, 0.90)
        draw_stroke_text(f"NITRO: {'ON' if nitro else 'OFF'}", WIN_W - 210, WIN_H - 36, px_height=14, center=False)
        draw_stroke_text(f"AUTO: {'ON' if cheat_auto else 'OFF'}", WIN_W - 210, WIN_H - 20, px_height=14, center=False)
        draw_stroke_text("T: teleport  |  N: hold nitro", WIN_W - 330, WIN_H - 4, px_height=12, center=False)

    # Pause overlay
    if paused:
        glColor3f(1.0, 1.0, 0.2)
        draw_stroke_text("PAUSED", WIN_W*0.5, WIN_H*0.5 + 40, px_height=42, center=True)
        glColor3f(0.9, 0.9, 0.9)
        draw_stroke_text("Press SPACE to resume", WIN_W*0.5, WIN_H*0.5 - 5, px_height=18, center=True)

    glColor3f(0.0, 0.0, 0.0)
    draw_rect(18, 18, 300, 56, True)
    glColor3f(1.0, 1.0, 1.0)
    draw_stroke_text(f"Lap: {lap}/{LAPS_TO_FINISH}", 30, 32, px_height=22, center=False)

def draw_track_menu():
    set_ortho(0, WIN_W, 0, WIN_H)
    glColor3f(0.06, 0.08, 0.10)
    draw_rect(0, 0, WIN_W, WIN_H, True)

    glColor3f(1.0, 1.0, 1.0)
    draw_stroke_text("Select Track", WIN_W*0.5, WIN_H - 130, px_height=38, center=True)
    draw_stroke_text("Press 1 / 2 / 3, then Enter", WIN_W*0.5, WIN_H - 180, px_height=20, center=True)

    row_h = 170
    start_y = WIN_H - 260
    left = 120
    card_w = WIN_W - 240

    for i, trk in enumerate(TRACKS):
        cy = start_y - i * row_h
        glColor3f(0.18, 0.22, 0.30) if i == selected_track else glColor3f(0.0, 0.0, 0.0)
        draw_rect(left, cy - 130, card_w, 140, True)

        px, py, pw, ph = left + 14, cy - 120, 220, 120
        trk.draw_preview(px, py, pw, ph)

        glColor3f(1.0, 1.0, 1.0) if i == selected_track else glColor3f(0.85, 0.85, 0.85)
        draw_stroke_text(f"{i+1}. {trk.title}", px + pw + 25, py + 70, px_height=26, center=False)

    glColor3f(0.85, 0.85, 0.85)
    draw_stroke_text("ESC exit", WIN_W*0.5, 55, px_height=18, center=True)

def draw_team_menu():
    set_ortho(0, WIN_W, 0, WIN_H)
    glColor3f(0.06, 0.08, 0.10)
    draw_rect(0, 0, WIN_W, WIN_H, True)

    glColor3f(1.0, 1.0, 1.0)
    draw_stroke_text("Select Team", WIN_W*0.5, WIN_H - 110, px_height=38, center=True)
    draw_stroke_text("Press 1-9, and 0 for the 10th team, then Enter", WIN_W*0.5, WIN_H - 160, px_height=20, center=True)
    draw_stroke_text("B = back to track selection", WIN_W*0.5, WIN_H - 195, px_height=18, center=True)

    left_x = 220
    right_x = 560
    top_y = WIN_H - 270
    gap_y = 85

    for idx, (name, col) in enumerate(TEAMS):
        col_x = left_x if idx < 5 else right_x
        row = idx if idx < 5 else idx - 5
        y = top_y - row * gap_y

        is_sel = (idx == selected_team)
        glColor3f(0.18, 0.22, 0.30) if is_sel else glColor3f(0.0, 0.0, 0.0)
        draw_rect(col_x - 30, y - 30, 360, 60, True)

        key_label = str(idx+1) if idx < 9 else "0"
        glColor3f(1.0, 1.0, 1.0)
        draw_stroke_text(f"{key_label}.", col_x - 10, y - 8, px_height=22, center=False)

        r, g, b = col
        glColor3f(r, g, b)
        draw_rect(col_x + 45, y - 14, 28, 28, True)
        glColor3f(0.0, 0.0, 0.0)
        draw_rect(col_x + 45, y - 14, 28, 28, False)

        glColor3f(1.0, 1.0, 1.0) if is_sel else glColor3f(0.88, 0.88, 0.88)
        draw_stroke_text(name, col_x + 90, y - 8, px_height=22, center=False)

# -----------------------------
# Render loop
# -----------------------------
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    if state == STATE_TRACK_MENU:
        glDisable(GL_DEPTH_TEST)
        draw_track_menu()
        glutSwapBuffers()
        return

    if state == STATE_TEAM_MENU:
        glDisable(GL_DEPTH_TEST)
        draw_team_menu()
        glutSwapBuffers()
        return

    if state == STATE_RESULTS:
        glDisable(GL_DEPTH_TEST)
        draw_results_screen()
        glutSwapBuffers()
        return

    apply_view_transform()
    cur_track().draw()

    draw_opponents()

    if not fpp_mode:
        draw_f1_car_world(car_x, car_y, car_ang, team_color())

    glDisable(GL_DEPTH_TEST)
    draw_hud()

    if fpp_mode:
        draw_cockpit_overlay()

    glutSwapBuffers()

def tick(_=0):
    global last_ms, race_now_ms
    now = glutGet(GLUT_ELAPSED_TIME)
    race_now_ms = now

    if last_ms == 0:
        last_ms = now
    dt = (now - last_ms) / 1000.0
    last_ms = now
    dt = clamp(dt, 0.0, 1.0 / 20.0)

    if state == STATE_RACE and (not paused):
        update_player(dt)
        update_opponents(dt)
        update_fpp_camera_angle(dt)
    elif state == STATE_RACE and paused:
        update_fpp_camera_angle(dt)

    glutPostRedisplay()
    glutTimerFunc(int(1000 / TARGET_FPS), tick, 0)

# -----------------------------
# Input
# -----------------------------
def key_down(k, x, y):
    global state, selected_track, selected_team, fpp_mode
    global cheat_on, cheat_auto, paused
    global fpp_cam_ang

    if isinstance(k, bytes):
        k = k.decode("utf-8", errors="ignore")

    if k == '\x1b':
        sys.exit(0)

    if state == STATE_RESULTS:
        if k in ('r', 'R'):
            fpp_mode = False
            reset_game()
            state = STATE_RACE
        elif k in ('m', 'M'):
            keys_down.clear()
            fpp_mode = False
            state = STATE_TRACK_MENU
        return

    if state == STATE_TRACK_MENU:
        if k in ('1', '2', '3'):
            selected_track = int(k) - 1
        elif k in ('\r', '\n'):
            state = STATE_TEAM_MENU
        return

    if state == STATE_TEAM_MENU:
        if k in ('b', 'B'):
            state = STATE_TRACK_MENU
            return
        if k in ('1','2','3','4','5','6','7','8','9'):
            selected_team = int(k) - 1
        elif k == '0':
            selected_team = 9
        elif k in ('\r', '\n'):
            fpp_mode = False
            reset_game()
            state = STATE_RACE
        return

    # Race: Pause toggle (SPACE)
    if state == STATE_RACE and k == ' ':
        paused = not paused
        return

    # Race: movement keys
    if k in ('w','W','a','A','s','S','d','D'):
        keys_down.add(k)

    # Cheat toggle
    if k in ('c', 'C'):
        cheat_on = not cheat_on
        if not cheat_on:
            cheat_auto = False
            keys_down.discard('n')
            keys_down.discard('N')

    # Autopilot toggle (cheat only)
    if cheat_on and k in ('p', 'P'):
        cheat_auto = not cheat_auto

    # Nitro (hold) (cheat only)
    if cheat_on and k in ('n', 'N'):
        keys_down.add(k)

    # Teleport (cheat only)
    if cheat_on and k in ('t', 'T'):
        cheat_teleport_next_checkpoint()

    # reset / menu
    if k in ('r','R'):
        reset_game()

    if k in ('m','M'):
        keys_down.clear()
        fpp_mode = False
        state = STATE_TRACK_MENU
        # Toggle First Person View with Z
    if k in ('z', 'Z'):
        if state == STATE_RACE:
            fpp_mode = not fpp_mode
            if fpp_mode:
                # Reset manual controls when entering FPV
                fpp_yaw_offset = 0.0
                fpp_fov = FPP_FOV_DEFAULT
                # Auto-align camera
                if cheat_on and cheat_auto:
                    cx, cy, tx, ty, _ = cur_track().closest_point_and_dist(car_x, car_y)
                    fpp_cam_ang = math.degrees(math.atan2(ty, tx))
                else:
                    fpp_cam_ang = car_ang
        return

def key_up(k, x, y):
    if isinstance(k, bytes):
        k = k.decode("utf-8", errors="ignore")
    if k in keys_down:
        keys_down.remove(k)

def special_down(key, x, y):
    global tpp_yaw_offset, tpp_pitch_deg, tpp_dist
    global fpp_yaw_offset, fpp_view_w, fpp_view_h

    if state != STATE_RACE:
        return

    # --- FPP controls ---
    if fpp_mode:
        if key == GLUT_KEY_LEFT:
            fpp_yaw_offset = normalize_angle_deg(fpp_yaw_offset - FPP_YAW_STEP)
        elif key == GLUT_KEY_RIGHT:
            fpp_yaw_offset = normalize_angle_deg(fpp_yaw_offset + FPP_YAW_STEP)
        elif key == GLUT_KEY_UP:
            fpp_fov = clamp(fpp_fov - FPP_FOV_STEP, FPP_FOV_MIN, FPP_FOV_MAX)   # zoom in
        elif key == GLUT_KEY_DOWN:
            fpp_fov = clamp(fpp_fov + FPP_FOV_STEP, FPP_FOV_MIN, FPP_FOV_MAX)   # zoom out
        return

    # --- TPP 3D controls ---
    if not TPP_3D_ENABLED:
        return

    if key == GLUT_KEY_LEFT:
        tpp_yaw_offset += 5.0
    elif key == GLUT_KEY_RIGHT:
        tpp_yaw_offset -= 5.0
    elif key == GLUT_KEY_UP:
        tpp_pitch_deg = clamp(tpp_pitch_deg + 3.0, 12.0, 78.0)
    elif key == GLUT_KEY_DOWN:
        tpp_pitch_deg = clamp(tpp_pitch_deg - 3.0, 12.0, 78.0)
    elif key == GLUT_KEY_PAGE_UP:
        tpp_dist = clamp(tpp_dist - 60.0, 520.0, 2400.0)
    elif key == GLUT_KEY_PAGE_DOWN:
        tpp_dist = clamp(tpp_dist + 60.0, 520.0, 2400.0)

def mouse(button, state_btn, x, y):
    global fpp_mode, fpp_cam_ang
    global fpp_yaw_offset, fpp_view_w, fpp_view_h

    if state != STATE_RACE:
        return
    if state_btn != GLUT_DOWN:
        return
    #if button == GLUT_RIGHT_BUTTON:
        fpp_mode = not fpp_mode
        if fpp_mode:
            # reset manual camera settings when entering FPP
            fpp_yaw_offset = 0.0
            fpp_view_w = FPP_VIEW_W
            fpp_view_h = FPP_VIEW_H

            if cheat_on and cheat_auto:
                cx, cy, tx, ty, _ = cur_track().closest_point_and_dist(car_x, car_y)
                fpp_cam_ang = math.degrees(math.atan2(ty, tx))
            else:
                fpp_cam_ang = car_ang

# -----------------------------
# Init
# -----------------------------
def init_gl():
    glClearColor(0.05, 0.05, 0.06, 1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)

def reshape(w, h):
    global WIN_W, WIN_H
    WIN_W = max(1, int(w))
    WIN_H = max(1, int(h))
    glViewport(0, 0, WIN_W, WIN_H)

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutCreateWindow(b"F1 Project - 3D TPP Camera + FPP + Opponents + Cheat + Pause")

    init_gl()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(key_down)
    glutKeyboardUpFunc(key_up)
    glutSpecialFunc(special_down)
    glutMouseFunc(mouse)
    glutTimerFunc(int(1000 / TARGET_FPS), tick, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()
