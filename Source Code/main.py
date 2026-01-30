# ============================================================================
# FLAPPY BIRD GAME
# ============================================================================
# A high-fidelity reconstruction of the mobile arcade classic.
# Features real-time physics, sprite animation, and high score persistence.
#
# Authors:          Amey Thakur & Mega Satish
# Modified by:      Han Zhang
# Date:             January 28, 2026
# License:          MIT License
# Repository:       https://github.com/Amey-Thakur/FLAPPY-BIRD-USING-PYGAME
# Profiles:
#   - Amey Thakur:  https://github.com/Amey-Thakur
#   - Mega Satish:  https://github.com/msatmod
# ============================================================================
# title: Flappy Bird
# icon: favicon.png

import pygame
import sys
import random
import csv
import time
from datetime import datetime

# ============================================================================
# GLOBAL CONFIGURATION
# ============================================================================
SCREEN_WIDTH    = 576
SCREEN_HEIGHT   = 1024
FPS             = 120
GRAVITY         = 0.25      # Downward acceleration applied per frame
FLAP_STRENGTH   = 8         # Upward velocity impulse on flap
PIPE_SPAWN_TIME = 1200      # Milliseconds between pipe generation
PIPE_GAP        = 300       # Vertical space between top and bottom pipes

# ============================================================================
# CORE LOGIC
# ============================================================================

def draw_floor():
    """
    Renders the infinite scrolling floor effect.
    
    Logic:
        Two identical floor surfaces are drawn side-by-side. As they move left,
        if the first one leaves the screen, it resets to the right, creating
        a seamless loop.
    """
    screen.blit(floor_surface, (floor_x_position, 900))
    screen.blit(floor_surface, (floor_x_position + 576, 900))

    # Render static text on top of the floor
    # Content and Colors
    # Text structure: [ ("Text", (R, G, B)) ]
    text_parts = [
    #     ("Developed by ", (255, 255, 255)),           # White
    #     ("Amey Thakur ", (85, 172, 238)),             # Sky Blue
    #     ("& ", (255, 255, 255)),                      # White
    #     ("Mega Satish", (85, 172, 238))               # Sky Blue
    ]

    # Calculate Total Width for Centering
    total_width = 0
    surfaces = []
    for text, color in text_parts:
        surface = footer_font.render(text, True, color)
        shadow = footer_font.render(text, True, (0, 0, 0)) # Black shadow
        width = surface.get_width()
        total_width += width
        surfaces.append( (surface, shadow, width) )

    # Starting X Position (Centered)
    current_x = (SCREEN_WIDTH - total_width) // 2
    text_y = 962
    
    # Render Loop
    for surface, shadow, width in surfaces:
        surface_rect = surface.get_rect(midleft=(current_x, text_y))
        shadow_rect = shadow.get_rect(midleft=(current_x + 2, text_y + 2)) # Offset shadow
        
        screen.blit(shadow, shadow_rect) # Draw shadow first
        screen.blit(surface, surface_rect) # Draw text on top
        
        current_x += width


def create_pipe():
    """
    Generates a new pipe obstacle pair (Top and Bottom).
    
    Returns:
        tuple: (bottom_pipe_rect, top_pipe_rect)
        
    Logic:
        Selects a random height from predefined positions.
        Calculates the position of the bottom pipe primarily, then
        derives the top pipe's position by subtracting the PIPE_GAP.
    """
    random_pipe_position = random.choice(pipe_height)
    
    # Bottom Pipe: Anchored at midtop position
    bottom_pipe = pipe_surface.get_rect(midtop=(700, random_pipe_position))
    
    # Top Pipe: Anchored relative to bottom pipe with fixed gap
    top_pipe = pipe_surface.get_rect(midbottom=(700, random_pipe_position - PIPE_GAP))
    
    return bottom_pipe, top_pipe


def move_pipes(pipes):
    """
    Updates the horizontal position of all active pipes.
    
    Parameters:
        pipes (list): List of pygame.Rect objects representing pipes.
        
    Returns:
        list: Updated list of moved pipes.
    """
    for pipe in pipes:
        pipe.centerx -= 5   # Move pipe leftward by 5 pixels per frame
    return pipes


def draw_pipes(pipes):
    """
    Renders the pipe sprites onto the screen.
    
    Logic:
        Iterates through the pipe list. If the pipe is a 'top' pipe
        (determined by its bottom Y coordinate being visible), checking
        logic is simplified here by context or we flip based on position.
        In this implementation, logic infers orientation:
        - If pipe bottom is >= 1024 (off screen low? No, Logic checks position).
        
        Correction:
        The logic checks if `pipe.bottom >= 1024`. This condition seems specific
        to how `create_pipe` sets rectangles. Ideally, distinction should be explicit.
        Here, we check geometry to decide whether to flip the sprite vertically.
    """
    for pipe in pipes:
        if pipe.bottom >= 1024:
            # Bottom pipe (Standard orientation)
            screen.blit(pipe_surface, pipe)
        else:
            # Top pipe (Flipped vertically)
            flip_pipe = pygame.transform.flip(pipe_surface, False, True)
            screen.blit(flip_pipe, pipe)


def check_collision(pipes):
    """
    Performs Axis-Aligned Bounding Box (AABB) collision detection.
    
    Parameters:
        pipes (list): List of obstacle rectangles.
        
    Returns:
        tuple: (bool, str) - (False if collision detected, collision_type)
                Returns (True, None) if no collision.
        
    Side Effects:
        Plays `death_sound` upon collision detection.
    """
    global game_active
    
    # 1. Pipe Collision
    for pipe in pipes:
        if bird_rectangle.colliderect(pipe):
            if game_active:
                death_sound.play()
                game_active = False
            return False, 'pipe'

    # 2. Environmental Collision (Floor/Ceiling)
    # Thresholds: -100 (Ceiling buffer), 900 (Floor Y-coordinate)
    # Ceiling Collision
    if bird_rectangle.top <= -100: 
        if game_active:
             death_sound.play()
             game_active = False
        return False, 'ceiling'
    # Floor Collision
    if bird_rectangle.bottom >= 900:
        if game_active:
             death_sound.play()
             game_active = False
        return False, 'floor'

    return True, None


def rotate_bird(bird):
    """
    Applies affine transformation (rotation) to the bird sprite.
    
    Logic:
        Rotation angle is proportional to vertical velocity (`bird_movement`).
        - Upward movement (negative velocity) -> Rotate Up (CCW).
        - Downward movement (positive velocity) -> Rotate Down (CW).
        Multiplier (3) exaggerates the visual effect.
        
    Returns:
        pygame.Surface: The rotated image surface.
    """
    new_bird = pygame.transform.rotozoom(bird, -bird_movement * 3, 1)
    return new_bird


def bird_animation():
    """
    Updates the bird's sprite frame to simulate wing flapping.
    
    Returns:
        tuple: (new_bird_surface, new_bird_rect)
    """
    new_bird = bird_frames[bird_index]
    new_bird_rectangle = new_bird.get_rect(center=(100, bird_rectangle.centery))
    return new_bird, new_bird_rectangle


def score_display(game_state):
    """
    Renders textual score information based on game state.
    
    Parameters:
        game_state (str): 'main_game' or 'game_over'.
    """
    if game_state == 'main_game':
        # Live Score
        score_surface = game_font.render(str(int(score)), True, (255, 255, 255))
        score_rectangle = score_surface.get_rect(center=(288, 100))
        screen.blit(score_surface, score_rectangle)

    if game_state == 'game_over':
        # Score Summary
        score_surface = game_font.render(f'Score: {int(score)}', True, (255, 255, 255))
        score_rectangle = score_surface.get_rect(center=(288, 100))
        screen.blit(score_surface, score_rectangle)

        # High Score
        high_score_surface = game_font.render(f'High Score: {int(high_score)}', True, (255, 255, 255))
        high_score_rectangle = high_score_surface.get_rect(center=(288, 185))
        screen.blit(high_score_surface, high_score_rectangle)


def debug_event_display(logger, display_duration_ms=1000):
    """
    Render the most recently logged event in the top-left corner for a short time.
    Intended purely for debugging/inspection while playing.
    """
    if logger is None or logger.last_event_message is None:
        return

    # Compute how long ago the last event was logged
    now_ms = int((time.time() - logger.game_start_time) * 1000)
    if now_ms - logger.last_event_timestamp > display_duration_ms:
        return

    # Prepare text surface
    text_surface = footer_font.render(logger.last_event_message, True, (255, 255, 0))
    text_rect = text_surface.get_rect(topleft=(10, 10))

    # Draw a simple background box for readability
    bg_rect = text_rect.inflate(10, 6)
    pygame.draw.rect(screen, (0, 0, 0), bg_rect)

    # Blit text on top
    screen.blit(text_surface, text_rect)


def wrap_text(text, font, max_width):
    """
    Simple word-wrap helper.
    Splits `text` into a list of lines that fit within `max_width`.
    """
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        test_line = word if current_line == "" else current_line + " " + word
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def collect_session_metadata():
    """
    Display a simple dialog at the beginning of the game to collect:
      - Subject ID
      - Simulator run
      - Comments
    Returns a tuple (subject_id, simulator_run, comments).
    """
    fields = [
        {"label": "Subject ID", "value": ""},
        {"label": "Simulator run", "value": ""},
        {"label": "Comments", "value": ""},
    ]
    current_field = 0
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Navigate between fields
                if event.key == pygame.K_TAB:
                    current_field = (current_field + 1) % len(fields)
                elif event.key == pygame.K_RETURN:
                    # Enter moves to next field, or finishes on last field
                    if current_field < len(fields) - 1:
                        current_field += 1
                    else:
                        done = True
                elif event.key == pygame.K_ESCAPE:
                    # Allow escape to skip (leave fields as-is)
                    done = True
                elif event.key == pygame.K_BACKSPACE:
                    value = fields[current_field]["value"]
                    fields[current_field]["value"] = value[:-1]
                else:
                    # Append printable characters
                    char = event.unicode
                    if char and char.isprintable():
                        # Modest length limit to avoid overflow; comments can be a bit longer
                        max_len = 24 if current_field < 2 else 80
                        if len(fields[current_field]["value"]) < max_len:
                            fields[current_field]["value"] += char

        # Draw dialog
        screen.blit(background_surface, (0, 0))

        dialog_width = SCREEN_WIDTH - 120
        dialog_height = 360
        dialog_rect = pygame.Rect(
            (SCREEN_WIDTH - dialog_width) // 2,
            (SCREEN_HEIGHT - dialog_height) // 2,
            dialog_width,
            dialog_height,
        )

        # Background and border
        pygame.draw.rect(screen, (0, 0, 0), dialog_rect)
        pygame.draw.rect(screen, (255, 255, 255), dialog_rect, 2)

        # Title
        title_surface = game_font.render("Session Info", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, dialog_rect.top + 40))
        screen.blit(title_surface, title_rect)

        # Instructions (wrapped to fit inside the dialog)
        instructions = "TAB / ENTER to move fields. ENTER on last field to start. ESC to skip."
        instr_lines = wrap_text(instructions, footer_font, dialog_width - 60)
        instr_y = title_rect.bottom + 25
        instructions_bottom = instr_y
        for line in instr_lines:
            instr_surface = footer_font.render(line, True, (200, 100, 200))
            instr_rect = instr_surface.get_rect(center=(SCREEN_WIDTH // 2, instr_y))
            screen.blit(instr_surface, instr_rect)
            instructions_bottom = instr_rect.bottom
            instr_y += instr_surface.get_height() + 4

        # Fields
        start_y = instructions_bottom + 30
        line_height = 40
        for idx, field in enumerate(fields):
            label_color = (255, 255, 0) if idx == current_field else (200, 200, 200)
            value_color = (255, 255, 255)

            label_surface = footer_font.render(f"{field['label']}:", True, label_color)
            base_y = start_y + idx * line_height
            label_rect = label_surface.get_rect(topleft=(dialog_rect.left + 30, base_y))

            text_value = field["value"] if field["value"] else "_"

            screen.blit(label_surface, label_rect)

            # Wrap comments visually so they don't overflow the dialog
            if field["label"] == "Comments":
                wrapped_lines = wrap_text(text_value, footer_font, dialog_width - 260)
                value_y = base_y
                for v_line in wrapped_lines:
                    value_surface = footer_font.render(v_line, True, value_color)
                    value_rect = value_surface.get_rect(
                        topleft=(dialog_rect.left + 220, value_y)
                    )
                    screen.blit(value_surface, value_rect)
                    value_y += value_surface.get_height() + 2
            else:
                value_surface = footer_font.render(text_value, True, value_color)
                value_rect = value_surface.get_rect(
                    topleft=(dialog_rect.left + 220, base_y)
                )
                screen.blit(value_surface, value_rect)

        pygame.display.update()
        clock.tick(30)

    subject_id = fields[0]["value"].strip()
    simulator_run = fields[1]["value"].strip()
    comments = fields[2]["value"].strip()
    return subject_id, simulator_run, comments

def update_score(current_score, current_high_score):
    """Updates the high score persistence variable."""
    if current_score > current_high_score:
        return current_score
    return current_high_score


# ============================================================================
# EVENT LOGGING SYSTEM
# ============================================================================

class EventLogger:
    """
    Records game events with timestamps to a CSV file.
    
    Tracks:
    - Trial start/end
    - Collisions
    - Pipe passages
    - Key presses
    """
    
    def __init__(self, subject_id, simulator_run):

        """
        Initialize the event logger.
        
        Parameters:
            subject_id (str): Subject ID
            simulator_run (str): Simulator run
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.filename = f"data/{subject_id}_{simulator_run}_{timestamp}.csv"
        
        self.attempt_id = 0
        self.csv_file = None
        self.writer = None
        self.game_start_time = time.time()

        # In-memory debug fields for on-screen display
        self.last_event_message = None
        self.last_event_timestamp = 0  # milliseconds since game_start_time
        
        # Create CSV file with headers
        try:
            self.csv_file = open(self.filename, 'w', newline='', encoding='utf-8')
            self.writer = csv.writer(self.csv_file)
            # Columns:
            #   unix_timestamp: absolute time (seconds since Unix epoch, float)
            #   timestamp:      ms since game_start_time
            self.writer.writerow(['unix_timestamp', 'timestamp', 'attempt_id', 'event', 'additional_info'])
            self.csv_file.flush()  # Ensure headers are written immediately
            print(f"Event logging initialized: {self.filename}")
        except Exception as e:
            print(f"Warning: Could not initialize event logger ({e})")
            self.csv_file = None
            self.writer = None
    
    def log_event(self, event, additional_info=None):
        """
        Log an event with current timestamp.
        
        Parameters:
            event (str): Type of event (e.g., 'TRIAL_START', 'COLLISION', etc.)
            additional_info (str): Optional additional information about the event
        """
        if self.writer is None:
            return
        
        try:
            unix_ts = time.time()
            timestamp = int((time.time() - self.game_start_time) * 1000)
            info = additional_info if additional_info is not None else ''

            # Persist to CSV
            self.writer.writerow([
                unix_ts,
                timestamp,
                self.attempt_id,
                event,
                info
            ])
            self.csv_file.flush()  # Write immediately to prevent data loss

            # Update in-memory debug info for on-screen display
            if info != '':
                self.last_event_message = f"Attempt {self.attempt_id}: {event}: {info}"
            else:
                self.last_event_message = event
            self.last_event_timestamp = timestamp
        except Exception as e:
            print(f"Warning: Failed to log event ({e})")
    
    def log_collision(self, collision_type):
        """
        Log a collision event.
        
        Parameters:
            collision_type (str): Type of collision ('pipe' or 'boundary')
        """
        self.log_event('COLLISION', additional_info=collision_type)
    
    def log_pipe_passed(self, score):
        """
        Log when bird passes through a pipe.
        
        Parameters:
            score (int): Current score
        """
        self.log_event('PIPE_PASSED', additional_info=score)
    
    def log_key_press(self, key_name):
        """
        Log a key press event.
        
        Parameters:
            key_name (str): Name of the key pressed
        """
        self.log_event('KEY_PRESS', additional_info=key_name)

    def log_quit(self):
        """
        Log the quit event.
        """
        self.log_event('QUIT')
        
    def close(self):
        """Close the CSV file and finalize logging."""
        if self.csv_file:
            try:
                self.csv_file.close()
                print(f"Event logging completed: {self.filename}")
            except Exception as e:
                print(f"Warning: Error closing event logger ({e})")


# ============================================================================
# INITIALIZATION
# ============================================================================

# Audio Mixer: Pre-init required to avoid audio lag
pygame.mixer.pre_init(frequency=44100, size=16, channels=1, buffer=512)
pygame.init()

# Display Setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird")

# Icon Setup
try:
    icon_surface = pygame.image.load('favicon.png')
    pygame.display.set_icon(icon_surface)
except Exception as e:
    print(f"Warning: Could not load icon ({e})")

clock = pygame.time.Clock()

# Typography
try:
    try:
        # Try finding the font with uppercase extension (Primary check)
        game_font = pygame.font.Font('04B_19.TTF', 40)
        footer_font = pygame.font.Font('04B_19.TTF', 20)
    except:
        # Fallback to lowercase extension (Secondary check)
        game_font = pygame.font.Font('04B_19.ttf', 40)
        footer_font = pygame.font.Font('04B_19.ttf', 20)
except:
    print("Warning: Custom font not found. Using system font.")
    game_font = pygame.font.SysFont('Arial', 40, bold=True)
    footer_font = pygame.font.SysFont('Arial', 20, bold=True)
bird_movement       = 0
game_active         = False
score               = 0
high_score          = 0
floor_x_position    = 0
pipe_list           = []
pipe_height         = [400, 600, 800]

# ============================================================================
# ASSET MANAGEMENT
# ============================================================================

try:
    # Textures
    background_surface = pygame.image.load('assets/background-day.png').convert()
    background_surface = pygame.transform.scale2x(background_surface)

    floor_surface = pygame.image.load('assets/base.png').convert()
    floor_surface = pygame.transform.scale2x(floor_surface)

    # Bird Animation Frames
    bird_downflap = pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha())
    bird_midflap  = pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha())
    bird_upflap   = pygame.transform.scale2x(pygame.image.load('assets/bluebird-midflap.png').convert_alpha())
    bird_frames   = [bird_downflap, bird_midflap, bird_upflap]
    bird_index    = 0
    bird_surface  = bird_frames[bird_index]
    bird_rectangle= bird_surface.get_rect(center=(100, 512))

    # Obstacles & UI
    pipe_surface    = pygame.image.load('assets/pipe-green.png')
    pipe_surface    = pygame.transform.scale2x(pipe_surface)
    
    game_over_surface   = pygame.transform.scale2x(pygame.image.load('assets/message.png').convert_alpha())
    game_over_rectangle = game_over_surface.get_rect(center=(288, 512))

    # Sound Effects
    flap_sound  = pygame.mixer.Sound('sound/sfx_wing.wav')
    death_sound = pygame.mixer.Sound('sound/sfx_hit.wav')
    score_sound = pygame.mixer.Sound('sound/sfx_point.wav')

except Exception as e:
    print(f"CRITICAL ERROR: Asset loading failed ({e}). Playing in fallback mode.")
    # Fallback Assets (Mock generation)
    background_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background_surface.fill((30, 30, 30))
    floor_surface = pygame.Surface((SCREEN_WIDTH, 100))
    floor_surface.fill((200, 200, 200))
    bird_surface = pygame.Surface((34, 24))
    bird_surface.fill((255, 255, 0))
    bird_rectangle = bird_surface.get_rect(center=(100, 512))
    bird_frames = [bird_surface]
    pipe_surface = pygame.Surface((52, 320))
    pipe_surface.fill((0, 255, 0))
    game_over_surface = pygame.Surface((200, 50))
    game_over_rectangle = game_over_surface.get_rect(center=(288, 512))
    
    # Sound Mock
    class MockSound:
        def play(self): pass
    flap_sound = MockSound()
    death_sound = MockSound()
    score_sound = MockSound()


# ============================================================================
# EVENT TIMERS
# ============================================================================
SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, PIPE_SPAWN_TIME)

# Bird flap animation timer (cycles wing frames)
BIRDFLAP = pygame.USEREVENT + 1
pygame.time.set_timer(BIRDFLAP, 200)

previous_game_active = False
# ============================================================================
# MAIN LOOP
# ============================================================================
def main(debug_mode=True):
    """
    The main game loop.
    Handles events, updates game state, and renders the frame.
    """
    global bird_movement, game_active, score, high_score, bird_index, bird_surface, bird_rectangle, pipe_list, floor_x_position, previous_game_active
    
    # Initialize event logger and collect session metadata
    subject_id, simulator_run, comments = collect_session_metadata()
    logger = EventLogger(subject_id, simulator_run)
    logger.log_event('SESSION_INFO', additional_info=f"subject_id={subject_id};run={simulator_run};comments={comments}")
    
    while True:
        # Event Handling
        for event in pygame.event.get():
            # New Attempt Mechanic
            if not previous_game_active and game_active:
                logger.attempt_id += 1
                previous_game_active = True

            if event.type == pygame.QUIT:
                # Log quit event
                logger.log_quit()
                logger.close()
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # Log key presses
                if game_active:
                    key_name = pygame.key.name(event.key).upper()
                    logger.log_key_press(key_name)
                
                # Flap Mechanic
                if event.key == pygame.K_SPACE and game_active:
                    bird_movement = 0
                    bird_movement -= FLAP_STRENGTH
                    flap_sound.play()

                # Restart Mechanic
                if event.key == pygame.K_SPACE and not game_active:
                    game_active         = True
                    pipe_list.clear() # Reset obstacles
                    bird_rectangle.center = (100, 512)
                    bird_movement       = 0
                    score               = 0
                    previous_game_active = False

                # Quit Mechanic
                if event.key == pygame.K_ESCAPE:
                    # Log quit event
                    logger.log_quit()
                    logger.close()
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Log mouse clicks as key presses
                if game_active:
                    logger.log_key_press('MOUSE_CLICK')
                
                # Flap Mechanic (Mouse)
                if game_active:
                    bird_movement = 0
                    bird_movement -= FLAP_STRENGTH
                    flap_sound.play()
                
                # Restart Mechanic (Mouse)
                else:
                    game_active         = True
                    pipe_list.clear() # Reset obstacles
                    bird_rectangle.center = (100, 512)
                    bird_movement       = 0
                    score               = 0
                    previous_game_active = False
                    
            if event.type == SPAWNPIPE:
                pipe_list.extend(create_pipe())

            if event.type == BIRDFLAP:
                # Cycle through bird animation frames to create a flapping effect
                if bird_index < 2:
                    bird_index += 1
                else:
                    bird_index = 0
                bird_surface, bird_rectangle = bird_animation()

        # Render Background
        screen.blit(background_surface, (0, 0))

        if game_active:
            # --- Active Gameplay State ---

            # 1. Physics: Apply Gravity
            bird_movement += GRAVITY
            
            # 2. Physics: Rotation
            rotated_bird = rotate_bird(bird_surface)
            bird_rectangle.centery += bird_movement
            screen.blit(rotated_bird, bird_rectangle)
            
            # 3. Collision Detection
            collision_result, collision_type = check_collision(pipe_list)
            game_active = collision_result
            if not game_active:
                logger.log_collision(collision_type)

            # 4. Obstacle Update
            pipe_list = move_pipes(pipe_list)
            draw_pipes(pipe_list)

            # 5. Scoring System
            # Check if bird passed the pipe (Pipe Center X passes 100)
            for pipe in pipe_list:
                if pipe.centerx == 100:
                    score += 0.5 
                    if score % 1 == 0:
                        score_sound.play()
                        logger.log_pipe_passed(score)
            
            score_display('main_game')
            
            # 6. Audio Feedback (Score) - Handled above
        else:
            # --- Game Over State ---
            screen.blit(game_over_surface, game_over_rectangle)
            high_score = update_score(score, high_score)
            score_display('game_over')

        # Debug overlay: show last logged event in the corner (for a short time)
        if debug_mode:
            debug_event_display(logger)

        # Floor Animation (Independent of game state for visual polish)
        floor_x_position -= 1
        draw_floor()
        if floor_x_position <= -576:
            floor_x_position = 0

        # Frame Update
        pygame.display.update()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
