import pygame
import random
import sys
import json
import math
import array
import os

# 1. Initialization and Window Config
pygame.mixer.pre_init(44100, -16, 2, 512) 
pygame.init()
pygame.font.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("X-Wing Fighter - Arcade Edition")
clock = pygame.time.Clock()

# --- SYNTHETIC RETRO AUDIO CONFIGURATION LAYER ---
def generate_laser_sound():
    sample_rate = 44100
    duration = 0.12
    num_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * num_samples)
    phi = 0.0
    for i in range(num_samples):
        t = i / sample_rate
        freq = 1300.0 - (1000.0 * (t / duration))
        phi += 2.0 * math.pi * freq / sample_rate
        sample = 0.4 if math.sin(phi) > 0 else -0.4
        fade = 1.0 - (t / duration)
        buf[i] = int(sample * 32767 * fade)
    return pygame.mixer.Sound(buffer=buf)

def generate_explosion_sound():
    sample_rate = 44100
    duration = 0.22
    num_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        t = i / sample_rate
        sample = random.uniform(-0.5, 0.5)
        fade = 1.0 - (t / duration)
        buf[i] = int(sample * 32767 * fade)
    return pygame.mixer.Sound(buffer=buf)

sound_laser = generate_laser_sound()
sound_explode = generate_explosion_sound()
sound_laser.set_volume(0.25)
sound_explode.set_volume(0.40)

# Fonts
FONT_SMALL = pygame.font.SysFont("Courier New", 20, bold=True)
FONT_LARGE = pygame.font.SysFont("Courier New", 54, bold=True)
FONT_SUB = pygame.font.SysFont("Courier New", 24, bold=True)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
ORANGE = (255, 140, 0)
YELLOW = (255, 215, 0)
BLUE = (0, 150, 255)       
DARK_GRAY = (40, 40, 40)   
PURPLE = (180, 0, 255)

# --- PERSISTENT FILE PERSISTENCE LAYER ---
# 1. Dynamically locate the actual folder where the script/EXE is running
BASE_DIR = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
HIGH_SCORE_FILE = os.path.join(BASE_DIR, "highscores.json")

DEFAULT_SCORES = [
    ["VAD", 10000],
    ["LUK", 9500],
    ["HAN", 9000],
    ["LEI", 8500],
    ["OBI", 8000],
    ["YOD", 7500],
    ["CHE", 7000],
    ["LAN", 6500],
    ["BOB", 6000],
    ["R2D", 5500]
]

def load_high_scores():
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return list(DEFAULT_SCORES)

def save_high_scores(scores):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            json.dump(scores, f)
    except IOError:
        print("Could not write high score data to disk.")

high_scores = load_high_scores()
# --- GAME STATES ---
# 0 = Gameplay, 1 = Game Over, 2 = Main Menu, 3 = Cinematic Level Transition
game_state = 2 

# Game Variables
player_x = WIDTH // 2
player_y = HEIGHT - 90
player_speed = 7
player_score = 0
player_shields = 100  
player_hull = 100     

# --- WAVE-BASED PROGRESSION CONFIGURATION ---
current_level = 1
enemies_destroyed_in_level = 0

def get_level_quota(level):
    return 5 + (level * 15)

# --- BOSS LAYER VARIABLES ---
boss_active = False
boss_x = WIDTH // 2
boss_y = -150                 # Starts off-screen to glide in smoothly
boss_max_hull = 1000
boss_hull = 1000
boss_state = 0                # 0 = Entering, 1 = Combat Engaged, 2 = Dying
boss_fire_timer = 0
boss_death_timer = 0

# New Weapon Array Attributes
boss_phase = 1                # 1 = Tracking Turrets, 2 = Superlaser Desperation
superlaser_charge = 0         # Timer for charging the beam
superlaser_active = 0         # Timer for beam active duration
superlaser_x = WIDTH // 2     # Laser beam target lock coordinate

# --- POWER-UP CONFIGURATION MATRIX ---
power_ups = []
power_up_speed = 3
weapon_mod_timer = 0       
hyperdrive_mod_timer = 0   

# Transition Sequence Timers
transition_timer = 0
target_level = 1

lasers = []
laser_speed = -12
enemy_lasers = []
bomber_ordnance = []       
radius_explosions = []     
explosion_particles = []
tie_fighters = []          
tie_spawn_timer = 0

flash_timer = 0
stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT), random.uniform(2, 6)] for _ in range(120)]

user_initials = ""
score_saved = False

def draw_text(text, font, color, x, y, center=False):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)

def reset_game():
    global player_shields, player_hull, player_score, player_x, player_y, lasers, enemy_lasers, bomber_ordnance, radius_explosions, tie_fighters, explosion_particles, current_level, enemies_destroyed_in_level, power_ups, weapon_mod_timer, hyperdrive_mod_timer, boss_active, boss_hull, boss_state, boss_y
    player_shields = 100
    player_hull = 100
    player_score = 0
    current_level = 1
    enemies_destroyed_in_level = 0
    weapon_mod_timer = 0
    hyperdrive_mod_timer = 0
    player_x = WIDTH // 2
    player_y = HEIGHT - 90
    boss_active = False
    boss_hull = boss_max_hull
    boss_state = 0
    boss_y = -150
    lasers.clear()
    enemy_lasers.clear()
    bomber_ordnance.clear()
    radius_explosions.clear()
    tie_fighters.clear()
    explosion_particles.clear()
    power_ups.clear()

def take_damage(amount):
    global player_shields, player_hull
    if player_shields > 0:
        player_shields -= amount
        if player_shields < 0:
            player_hull += player_shields  
            player_shields = 0
    else:
        player_hull -= amount
    if player_hull < 0:
        player_hull = 0

# --- MAIN LOOP ---
while True:
    flash_timer += 1
    
    # --- STARFIELD RENDERING LAYER ---
    is_transitioning = (game_state == 3 and transition_timer > 90)
    is_hyperdrive_active = (game_state == 0 and hyperdrive_mod_timer > 0)
    
    star_speed_multiplier = 4.5 if (is_transitioning or is_hyperdrive_active) else 1.0
    for star in stars:
        star[1] += star[2] * star_speed_multiplier
        if star[1] > HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, WIDTH)

    # --- STATE 2: ARCADE CABINET START SCREEN ---
    if game_state == 2:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN or (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                reset_game()
                game_state = 0

        screen.fill(BLACK)
        for star in stars:
            pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), 1 if star[2] < 4 else 2)
            
        draw_text("X-WING FIGHTER", FONT_LARGE, GREEN, WIDTH // 2, 80, center=True)
        draw_text("1 CREDIT = PLAY", FONT_SMALL, WHITE, WIDTH // 2, 140, center=True)
        
        if (flash_timer // 30) % 2 == 0:
            draw_text("INSERT COIN / PRESS SPACEBAR TO START", FONT_SMALL, YELLOW, WIDTH // 2, 190, center=True)
            
        draw_text("= GALACTIC TOP SCORES =", FONT_SMALL, ORANGE, WIDTH // 2, 260, center=True)
        start_y = 300
        for index, row in enumerate(high_scores):
            line_str = f"{index + 1:2d}.  {row[0]}  .......  {row[1]:05d}"
            draw_text(line_str, FONT_SMALL, WHITE, WIDTH // 2, start_y, center=True)
            start_y += 24
            
        draw_text("© 1983 ATARI REALM EMULATION", FONT_SMALL, RED, WIDTH // 2, 560, center=True)

    # --- STATE 0: ACTIVE ARCADE PILOT GAMEPLAY ---
    elif game_state == 0:
        if weapon_mod_timer > 0: weapon_mod_timer -= 1
        if hyperdrive_mod_timer > 0: hyperdrive_mod_timer -= 1

        # Check if minion quota is filled on a boss milestone level (Levels 4, 9, 14, etc.)
        is_boss_level = (current_level % 5 == 4)
        
        if enemies_destroyed_in_level >= get_level_quota(current_level):
            if is_boss_level and not boss_active and boss_state == 0:
                boss_active = True
                boss_hull = boss_max_hull + (current_level * 100) # Scales health over time
                boss_max_hull_current = boss_hull
                boss_y = -150
                tie_fighters.clear() # Clear out old minions
            elif not is_boss_level:
                # Standard stage progression bypass
                target_level = current_level + 1
                game_state = 3
                transition_timer = 180  
                lasers.clear()
                enemy_lasers.clear()
                bomber_ordnance.clear()
                power_ups.clear()
                continue

        # Progression Scaling Calculations
        time_dilation = 0.45 if hyperdrive_mod_timer > 0 else 1.0
        
        spawn_delay = max(10, 25 - (current_level * 1.5))
        if hyperdrive_mod_timer > 0: spawn_delay *= 2  
        
        speed_modifier = 1 + ((current_level - 1) // 5) * 0.5
        enemy_speed = 4.0 * speed_modifier * time_dilation
        enemy_laser_speed = 8.0 * speed_modifier * time_dilation
        bomber_laser_speed = 5.0 * speed_modifier * time_dilation
        fire_chance = min(0.04, 0.015 + (current_level * 0.002)) * time_dilation

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if weapon_mod_timer > 0:
                    lasers.append([player_x - 35, player_y - 10])
                    lasers.append([player_x - 15, player_y - 20])
                    lasers.append([player_x + 15, player_y - 20])
                    lasers.append([player_x + 35, player_y - 10])
                else:
                    lasers.append([player_x - 35, player_y - 10])
                    lasers.append([player_x + 35, player_y - 10])
                sound_laser.play()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and player_x > 45:
            player_x -= player_speed
        if keys[pygame.K_d] and player_x < WIDTH - 45:
            player_x += player_speed

        # Process Player Blasters
        for laser in lasers[:]:
            laser[1] += laser_speed
            
            # Hitbox registration for Star Destroyer Hull
            if boss_active and boss_state == 1:
                # Box collision targeting the core triangular body profile
                if (150 < laser[0] < 650) and (boss_y < laser[1] < boss_y + 110):
                    boss_hull -= 10
                    sound_explode.play()
                    if laser in lasers: lasers.remove(laser)
                    
                    # Spawn tiny surface spark sparks
                    for _ in range(3):
                        explosion_particles.append([laser[0], laser[1], random.uniform(-2,2), random.uniform(-1,3), random.randint(5,12), YELLOW])
                    
                    if boss_hull <= 0:
                        boss_state = 2 # Initiate explosion cascade
                        boss_active = False
                        boss_death_timer = 240  # <-- ADD THIS LINE
                    continue
                    
            if laser[1] < 0:
                lasers.remove(laser)

        # --- BOSS UPDATE LOGIC LOOP ---
        if boss_active:
            # Difficulty scaling based on the current 5-level sector block
            sector_tier = (current_level // 5) + 1
            scaled_fire_rate = max(15, 50 - (sector_tier * 5))
            scaled_laser_speed = 6.0 + (sector_tier * 1.5)

            if boss_state == 0: # Smooth entry glide from orbit
                if boss_y < 40:
                    boss_y += 1
                else:
                    boss_state = 1
                    boss_phase = 1
            elif boss_state == 1: 
                # Phase Transition: Desperation mode at under 40% hull integrity
                if boss_hull < (boss_max_hull_current * 0.40) and boss_phase == 1:
                    boss_phase = 2
                    superlaser_charge = 90 # 1.5 second warning charge time

                # --- PHASE 1: TARGETING TURRETS ---
                if boss_phase == 1:
                    boss_fire_timer += 1 * time_dilation
                    if boss_fire_timer >= scaled_fire_rate:
                        # Left and Right Turret positions on the graphic profile
                        turrets = [(280, boss_y + 80), (520, boss_y + 80)]
                        for tx, ty in turrets:
                            # Calculate exact trajectory vector targeting the player
                            dx = player_x - tx
                            dy = player_y - ty
                            dist = math.hypot(dx, dy)
                            if dist > 0:
                                # Inject vector coordinates directly [x, y, vx, vy]
                                enemy_lasers.append([tx, ty, (dx / dist) * scaled_laser_speed, (dy / dist) * scaled_laser_speed])
                        boss_fire_timer = 0

                # --- PHASE 2: DESPERATION SUPERLASER BEAM ---
                elif boss_phase == 2:
                    if superlaser_charge > 0:
                        superlaser_charge -= 1 * time_dilation
                        # Warning lock closely follows player position before freezing
                        if superlaser_charge > 20:
                            superlaser_x = player_x
                        if superlaser_charge <= 0:
                            superlaser_active = 60 # Beam fires continuously for 1 second
                            sound_explode.play()   # Roaring laser initiation hum
                    
                    elif superlaser_active > 0:
                        superlaser_active -= 1 * time_dilation
                        # Collision detection check: Is player inside the beam boundaries?
                        if abs(player_x - superlaser_x) < 25 and player_y > boss_y + 110:
                            # Inflicts continuous grinding structural decay frame-by-frame
                            take_damage(2 + (sector_tier // 2)) 
                        
                        if superlaser_active <= 0:
                            # Reload phase loop cycle
                            superlaser_charge = max(60, 150 - (sector_tier * 10))
                    
        elif is_boss_level and boss_state == 2:
            # Boss death explosion sequence cascade animation
            boss_death_timer -= 1  # Tick down the death sequence
            
            if random.random() < 0.40:
                sound_explode.play()
                ex = random.randint(200, 600)
                ey = random.randint(int(boss_y), int(boss_y) + 90)
                for _ in range(20):
                    explosion_particles.append([ex, ey, random.uniform(-5,5), random.uniform(-5,5), random.randint(15,40), random.choice([RED, ORANGE, YELLOW])])
            
            boss_y -= 0.5 # Slow drift back away
            
            # Once the 2-second death cinematic finishes, transition cleanly!
            if boss_death_timer <= 0: 
                boss_state = 0
                boss_y = -150
                player_score += 2500
                
                # Advance to next sector stage boundary setup
                target_level = current_level + 1
                game_state = 3
                transition_timer = 180  
                lasers.clear()
                enemy_lasers.clear()
                bomber_ordnance.clear()
                power_ups.clear()
                continue

        # Process Dropped Powerups
        for pu in power_ups[:]:
            pu[1] += power_up_speed
            if math.hypot(player_x - pu[0], player_y - pu[1]) < 35:
                if pu[2] == 'shield':
                    player_shields = min(100, player_shields + 40)
                elif pu[2] == 'weapon':
                    weapon_mod_timer = 420  
                elif pu[2] == 'hyper':
                    hyperdrive_mod_timer = 300 
                elif pu[2] == 'bomb':
                    if boss_active and boss_state == 1:
                        boss_hull -= 150 # Massive baseline flat damage bypass block to boss unit
                    for bomb_tie in tie_fighters[:]:
                        sound_explode.play()
                        enemies_destroyed_in_level += 1
                        player_score += 250 if bomb_tie[3] == 'bomber' else 100
                        for _ in range(15):
                            explosion_particles.append([bomb_tie[0], bomb_tie[1], random.uniform(-4, 4), random.uniform(-4, 4), random.randint(10, 25), WHITE])
                    tie_fighters.clear()
                    enemy_lasers.clear()
                    bomber_ordnance.clear()
                    
                sound_explode.play() 
                power_ups.remove(pu)
            elif pu[1] > HEIGHT + 20:
                power_ups.remove(pu)

        # Process Enemy Lasers (Handles standard fighters and tracking boss shots)
        for e_laser in enemy_lasers[:]:
            # If the laser has 4 items, it's a tracking shot with [x, y, vx, vy]
            if len(e_laser) == 4:
                e_laser[0] += e_laser[2] # Move horizontally via vx
                e_laser[1] += e_laser[3] # Move vertically via vy
            else:
                e_laser[1] += enemy_laser_speed # Standard straight-down fighter blast
            
            # Hit box collision detection
            if (player_x - 35 < e_laser[0] < player_x + 35) and (player_y - 20 < e_laser[1] < player_y + 20):
                take_damage(10)  
                sound_explode.play()
                if e_laser in enemy_lasers: enemy_lasers.remove(e_laser)
            
            # Off-screen cleanup boundary check
            elif e_laser[1] > HEIGHT or e_laser[1] < -50 or e_laser[0] < 0 or e_laser[0] > WIDTH:
                if e_laser in enemy_lasers: enemy_lasers.remove(e_laser)

        # Process Heavy Bomber Ordnance 
        for ordn in bomber_ordnance[:]:
            ordn[1] += bomber_laser_speed
            direct_hit = (player_x - 35 < ordn[0] < player_x + 35) and (player_y - 20 < ordn[1] < player_y + 20)
            if direct_hit or ordn[1] >= ordn[2]:
                radius_explosions.append([ordn[0], ordn[1], 2, 45])  
                sound_explode.play()
                bomber_ordnance.remove(ordn)
                if direct_hit:
                    take_damage(15)
            elif ordn[1] > HEIGHT:
                bomber_ordnance.remove(ordn)

        # Process Expanding Blast Radius Damage Rings
        for expl in radius_explosions[:]:
            expl[2] += 3  
            dist = math.hypot(player_x - expl[0], player_y - expl[1])
            if dist < expl[2] and dist > (expl[2] - 8):
                take_damage(1)  
            if expl[2] >= expl[3]:
                radius_explosions.remove(expl)

        # Fleet Spawning Matrix (Suspended if Capital Flagship block is active)
        if not boss_active and boss_state == 0:
            tie_spawn_timer += 1
            if tie_spawn_timer > spawn_delay:
                if current_level >= 2 and random.random() < 0.30:
                    tie_fighters.append([random.randint(60, WIDTH - 60), -30, random.choice([-1, 0, 1]), 'bomber'])
                else:
                    tie_fighters.append([random.randint(50, WIDTH - 50), -20, random.choice([-1, 0, 1]), 'fighter'])
                tie_spawn_timer = 0

        # Process Fleet Actions
        for tie in tie_fighters[:]:
            tie[1] += enemy_speed        
            tie[0] += tie[2]   
            
            if random.random() < fire_chance and 0 < tie[1] < HEIGHT - 180:
                if tie[3] == 'fighter':
                    enemy_lasers.append([tie[0], tie[1] + 10])
                elif tie[3] == 'bomber':
                    bomber_ordnance.append([tie[0], tie[1] + 15, player_y + random.randint(-15, 15)])
                    
            if tie[1] > HEIGHT + 30:
                tie_fighters.remove(tie)
            elif (player_x - 40 < tie[0] < player_x + 40) and (player_y - 20 < tie[1] < player_y + 40):
                take_damage(25)  
                sound_explode.play()
                for _ in range(15):
                    explosion_particles.append([tie[0], tie[1], random.uniform(-5, 5), random.uniform(-5, 5), random.randint(10, 20), RED])
                tie_fighters.remove(tie)

        # Collision Check: Player Lasers vs Enemy Fleet
        for laser in lasers[:]:
            for tie in tie_fighters[:]:
                if (tie[0] - 25 < laser[0] < tie[0] + 25) and (tie[1] - 20 < laser[1] < tie[1] + 20):
                    sound_explode.play()
                    enemies_destroyed_in_level += 1 
                    
                    if random.random() < 0.18:
                        power_ups.append([tie[0], tie[1], random.choice(['shield', 'weapon', 'hyper', 'bomb'])])
                    
                    if tie[3] == 'bomber':
                        player_score += 250  
                        p_color = PURPLE
                    else:
                        player_score += 100
                        p_color = ORANGE
                        
                    for _ in range(25):
                        explosion_particles.append([tie[0], tie[1], random.uniform(-4, 4), random.uniform(-4, 4), random.randint(15, 30), random.choice([p_color, YELLOW, WHITE])])
                    
                    if tie in tie_fighters: tie_fighters.remove(tie)
                    if laser in lasers: lasers.remove(laser)

        for particle in explosion_particles[:]:
            particle[0] += particle[2]
            particle[1] += particle[3]
            particle[4] -= 1
            if particle[4] <= 0:
                explosion_particles.remove(particle)

        if player_hull <= 0:
            game_state = 1  
            user_initials = ""
            score_saved = False

        # --- DRAW ACTIVE GAME LAYER ---
        screen.fill(BLACK)
        for star in stars:
            pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), 1 if star[2] < 4 else 2)
            
        # Draw Star Destroyer Flagship if active or dying
        if boss_active or (is_boss_level and boss_state == 2):
            # Outer hull geometric polygon lines
            points_hull = [(WIDTH // 2, boss_y + 110), (120, boss_y), (680, boss_y)]
            pygame.draw.polygon(screen, DARK_GRAY, points_hull)
            pygame.draw.polygon(screen, WHITE, points_hull, 2)
            
            # Bridge Command Tower Superstructure 
            pygame.draw.rect(screen, DARK_GRAY, (WIDTH // 2 - 40, boss_y - 15, 80, 20))
            pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 40, boss_y - 15, 80, 20), 2)
            pygame.draw.line(screen, WHITE, (WIDTH // 2 - 50, boss_y - 15), (WIDTH // 2 + 50, boss_y - 15), 3)

            # --- SUPERLASER RENDER PIPELINE ---
            if boss_active and boss_phase == 2:
                core_x, core_y = WIDTH // 2, boss_y + 90
                if superlaser_charge > 0:
                    # Target acquisition phase: draw thin flashing red threat projection vector
                    if (flash_timer // 5) % 2 == 0:
                        pygame.draw.line(screen, RED, (core_x, core_y), (superlaser_x, HEIGHT), 1)
                        pygame.draw.circle(screen, RED, (core_x, core_y), 6, 1)
                elif superlaser_active > 0:
                    # Main weapon ignition canvas overlay: continuous glowing green core beam
                    pygame.draw.line(screen, GREEN, (core_x, core_y), (superlaser_x, HEIGHT), 35)
                    pygame.draw.line(screen, WHITE, (core_x, core_y), (superlaser_x, HEIGHT), 12) # Hyper-hot white core
                    
                    # Thermal discharge flare ring at the gun emitter tip
                    pygame.draw.circle(screen, GREEN, (core_x, core_y), random.randint(20, 35))
                    pygame.draw.circle(screen, WHITE, (core_x, core_y), random.randint(8, 15))

        for laser in lasers:
            pygame.draw.line(screen, GREEN, (laser[0], laser[1]), (laser[0], laser[1] - 15), 3)
            
        for e_laser in enemy_lasers:
            pygame.draw.line(screen, RED, (e_laser[0], e_laser[1]), (e_laser[0], e_laser[1] + 15), 3)

        for ordn in bomber_ordnance:
            pygame.draw.circle(screen, PURPLE, (ordn[0], ordn[1]), 5)
            pygame.draw.circle(screen, WHITE, (ordn[0], ordn[1]), 2)

        for expl in radius_explosions:
            pygame.draw.circle(screen, ORANGE, (expl[0], expl[1]), int(expl[2]), 2)

        for pu in power_ups:
            px, py = int(pu[0]), int(pu[1])
            pulse_offset = int(math.sin(flash_timer * 0.15) * 2)
            rad = 12 + pulse_offset
            
            if pu[2] == 'shield':
                pygame.draw.circle(screen, BLUE, (px, py), rad, 2)
                draw_text("S", FONT_SMALL, BLUE, px, py, center=True)
            elif pu[2] == 'weapon':
                pygame.draw.rect(screen, GREEN, (px - rad, py - rad, rad*2, rad*2), 2)
                draw_text("W", FONT_SMALL, GREEN, px, py, center=True)
            elif pu[2] == 'bomb':
                points = [(px, py - rad), (px + rad, py), (px, py + rad), (px - rad, py)]
                pygame.draw.polygon(screen, RED, points, 2)
                draw_text("B", FONT_SMALL, RED, px, py, center=True)
            elif pu[2] == 'hyper':
                points = [(px, py - rad), (px + rad, py + rad), (px - rad, py + rad)]
                pygame.draw.polygon(screen, YELLOW, points, 2)
                draw_text("H", FONT_SMALL, YELLOW, px, py, center=True)

        for tie in tie_fighters:
            if tie[3] == 'fighter':
                pygame.draw.circle(screen, WHITE, (tie[0], tie[1]), 8)
                pygame.draw.line(screen, WHITE, (tie[0] - 12, tie[1]), (tie[0] + 12, tie[1]), 2)
                pygame.draw.line(screen, WHITE, (tie[0] - 15, tie[1] - 15), (tie[0] - 15, tie[1] + 15), 4)
                pygame.draw.line(screen, WHITE, (tie[0] + 15, tie[1] - 15), (tie[0] + 15, tie[1] + 15), 4)
            elif tie[3] == 'bomber':
                pygame.draw.circle(screen, DARK_GRAY, (tie[0] - 7, tie[1]), 7)
                pygame.draw.circle(screen, BLUE, (tie[0] + 7, tie[1]), 7)
                pygame.draw.line(screen, WHITE, (tie[0] - 18, tie[1]), (tie[0] + 18, tie[1]), 3)
                pygame.draw.line(screen, WHITE, (tie[0] - 20, tie[1] - 12), (tie[0] - 20, tie[1] + 12), 5)
                pygame.draw.line(screen, WHITE, (tie[0] + 20, tie[1] - 12), (tie[0] + 20, tie[1] + 12), 5)

        for particle in explosion_particles:
            p_radius = max(1, int(particle[4] / 5))
            pygame.draw.circle(screen, particle[5], (int(particle[0]), int(particle[1])), p_radius)

        # Render X-Wing Ship Layout
        pygame.draw.polygon(screen, WHITE, [(player_x, player_y - 25), (player_x - 10, player_y + 15), (player_x + 10, player_y + 15)])
        pygame.draw.line(screen, WHITE, (player_x - 35, player_y + 5), (player_x + 35, player_y + 5), 4)
        
        wing_glow = ORANGE if weapon_mod_timer > 0 else GREEN
        pygame.draw.line(screen, wing_glow, (player_x - 35, player_y + 5), (player_x - 35, player_y - 10), 2)
        pygame.draw.line(screen, wing_glow, (player_x + 35, player_y + 5), (player_x + 35, player_y - 10), 2)

        # UI Headers
        draw_text(f"SCORE: {player_score:05d}", FONT_SMALL, WHITE, 20, 20)
        draw_text(f"STAGE: {current_level}", FONT_SMALL, YELLOW, 180, 20) 
        
        if boss_active:
            draw_text("WARNING: CAPITAL FLAGSHIP DETECTED", FONT_SMALL, RED, 290, 20)
            
            # Draw dedicated Capital Ship Health bar right below standard HUD
            draw_text("STAR DESTROYER:", FONT_SMALL, WHITE, 20, HEIGHT - 30)
            pygame.draw.rect(screen, DARK_GRAY, (200, HEIGHT - 28, 580, 14))
            pct = max(0, boss_hull / boss_max_hull_current)
            pygame.draw.rect(screen, RED, (200, HEIGHT - 28, int(580 * pct), 14))
            pygame.draw.rect(screen, WHITE, (200, HEIGHT - 28, 580, 14), 1)
        else:
            quota_text = f"CLEARANCE: {enemies_destroyed_in_level}/{get_level_quota(current_level)}"
            draw_text(quota_text, FONT_SMALL, ORANGE, 290, 20)
        
        if weapon_mod_timer > 0:
            draw_text(f"QUAD BLASTER: {weapon_mod_timer//60}s", FONT_SMALL, GREEN, 20, 50)
        if hyperdrive_mod_timer > 0:
            draw_text(f"TIME DILATION: {hyperdrive_mod_timer//60}s", FONT_SMALL, YELLOW, 20, 75)

        # Health & Shield Bars
        draw_text("DEFLECTORS:", FONT_SMALL, BLUE, 460, 15)
        pygame.draw.rect(screen, DARK_GRAY, (590, 15, 180, 16)) 
        pygame.draw.rect(screen, BLUE, (590, 15, int(1.8 * player_shields), 16)) 
        pygame.draw.rect(screen, WHITE, (590, 15, 180, 16), 1) 

        draw_text("HULL INTEGRITY:", FONT_SMALL, RED, 416, 38)
        pygame.draw.rect(screen, DARK_GRAY, (590, 38, 180, 16)) 
        pygame.draw.rect(screen, RED, (590, 38, int(1.8 * player_hull), 16)) 
        pygame.draw.rect(screen, WHITE, (590, 38, 180, 16), 1) 

    # --- STATE 3: CINEMATIC LEVEL TRANSITION INTERMISSION ---
    elif game_state == 3:
        transition_timer -= 1
        
        if transition_timer > 90:
            for tie in tie_fighters[:]:
                tie[1] += 16
                if tie[1] > HEIGHT + 50:
                    tie_fighters.remove(tie)
            if player_y > HEIGHT // 2:
                player_y -= 3
        else:
            tie_fighters.clear() 
            if player_y < HEIGHT - 90:
                player_y += 3

        if transition_timer <= 0:
            current_level = target_level
            enemies_destroyed_in_level = 0 
            game_state = 0
            tie_spawn_timer = 0

        screen.fill(BLACK)
        for star in stars:
            pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), 1 if star[2] < 4 else 2)

        pygame.draw.polygon(screen, WHITE, [(player_x, player_y - 25), (player_x - 10, player_y + 15), (player_x + 10, player_y + 15)])
        pygame.draw.line(screen, WHITE, (player_x - 35, player_y + 5), (player_x + 35, player_y + 5), 4)
        pygame.draw.line(screen, GREEN, (player_x - 35, player_y + 5), (player_x - 35, player_y - 10), 2)
        pygame.draw.line(screen, GREEN, (player_x + 35, player_y + 5), (player_x + 35, player_y - 10), 2)

        if transition_timer <= 90:
            if (transition_timer // 10) % 2 == 0:
                draw_text(f"STAGE {target_level}", FONT_LARGE, ORANGE, WIDTH // 2, HEIGHT // 2 - 40, center=True)
                draw_text("PREPARE FOR ENGAGEMENT", FONT_SUB, YELLOW, WIDTH // 2, HEIGHT // 2 + 30, center=True)

        draw_text(f"SCORE: {player_score:05d}", FONT_SMALL, WHITE, 20, 20)
        draw_text(f"STAGE: {current_level}", FONT_SMALL, YELLOW, 180, 20) 

    # --- STATE 1: GAME OVER / LEADERBOARD WINDOW ---
    elif game_state == 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if not score_saved:
                    if event.unicode.isalpha() and len(user_initials) < 3:
                        user_initials += event.unicode.upper()
                    elif event.key == pygame.K_BACKSPACE:
                        user_initials = user_initials[:-1]
                    elif event.key == pygame.K_RETURN and len(user_initials) == 3:
                        high_scores.append([user_initials, player_score])
                        high_scores.sort(key=lambda x: x[1], reverse=True)
                        if len(high_scores) > 10:
                            high_scores.pop()
                        score_saved = True
                        save_high_scores(high_scores)  
                else:
                    if event.key == pygame.K_SPACE:
                        game_state = 2

        screen.fill(BLACK)
        for star in stars:
            pygame.draw.circle(screen, WHITE, (int(star[0]), int(star[1])), 1 if star[2] < 4 else 2)
            
        draw_text("GAME OVER", FONT_LARGE, RED, WIDTH // 2, 50, center=True)
        draw_text(f"YOUR FINAL SCORE: {player_score} (STAGE {current_level})", FONT_SMALL, YELLOW, WIDTH // 2, 110, center=True)
        
        if not score_saved:
            draw_text("ENTER YOUR INITIALS (3 LETTERS):", FONT_SMALL, WHITE, WIDTH // 2, 170, center=True)
            display_initials = user_initials + "_" * (3 - len(user_initials))
            draw_text(display_initials, FONT_LARGE, GREEN, WIDTH // 2, 210, center=True)
            if len(user_initials) == 3:
                draw_text("PRESS ENTER TO LOCK SCORE", FONT_SMALL, ORANGE, WIDTH // 2, 260, center=True)
        else:
            draw_text("SCORE RECORDED SUCCESSFULLY!", FONT_SMALL, GREEN, WIDTH // 2, 170, center=True)
            draw_text("PRESS SPACEBAR TO RETURN TO TITLE", FONT_SMALL, WHITE, WIDTH // 2, 210, center=True)

        draw_text("--- GALACTIC TOP 10 HIGH SCORES ---", FONT_SMALL, YELLOW, WIDTH // 2, 310, center=True)
        start_y = 340
        for index, row in enumerate(high_scores):
            text_color = GREEN if (score_saved and row[0] == user_initials and row[1] == player_score) else WHITE
            line_str = f"{index + 1:2d}.  {row[0]}  .......  {row[1]:05d}"
            draw_text(line_str, FONT_SMALL, text_color, WIDTH // 2, start_y, center=True)
            start_y += 24

    pygame.display.flip()
    clock.tick(60)