import arcade
import os
import random

# Game window settings
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Will the Knight?"

TILE_SCALING = 1
GRAVITY = 0.9

UPDATES_PER_FRAME = 7

RIGHT_FACING = 0
LEFT_FACING = 1

CHARACTER_SCALING = 1

# Item system
common_item_pool = ["SpeedUp", "JumpUp", "DmgUp", "RollUp"]
item_list = []

def load_texture_pair(filename):
    """Load a texture pair for left and right facing directions."""
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True)
    ]

# Player character class with all animations
class PlayerCharacter(arcade.Sprite):
    """Main player character with movement and animation system."""
    
    def __init__(self, idle_texture_pair, walk_texture_pairs, 
                 jump_texture_pair, fall_texture_pair, land_texture_pair, 
                 roll_texture_pairs, swing_texture_pairs):
        self.character_face_direction = RIGHT_FACING
        self.cur_texture = 0

        self.roll_texture_pairs = roll_texture_pairs
        self.swing_texture_pairs = swing_texture_pairs
        self.cur_roll_frame = 0

        self.was_on_ground_last_frame = True
        self.land_frame_timer = 0

        self.on_ground = True

        self.falling = False
        self.jumping = False
        self.is_rolling = False

        
        self.walk_textures = walk_texture_pairs
        self.swing_textures = swing_texture_pairs
        self.idle_texture_pair = idle_texture_pair
        self.jump_texture_pair = jump_texture_pair
        self.fall_texture_pair = fall_texture_pair
        self.land_texture_pair = land_texture_pair
        self.roll_textures = roll_texture_pairs

        # Attack system
        self.is_attacking = False
        self.cur_swing_frame = 0

        super().__init__(self.idle_texture_pair[0], scale=CHARACTER_SCALING)

    def update_animation(self, delta_time: float = 1 / 60):
        """Update player sprite animation based on current state."""

        # Set facing direction based on movement
        if self.change_x < 0:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0:
            self.character_face_direction = RIGHT_FACING

        # Jump animation
        if self.change_y > 0:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return

        # Landing animation
        if self.change_y == 0 and not self.was_on_ground_last_frame:
            self.texture = self.land_texture_pair[self.character_face_direction]
            self.was_on_ground_last_frame = True
            return
            
        if self.land_frame_timer > 0:
            self.land_frame_timer -= delta_time
            self.texture = self.land_texture_pair[self.character_face_direction]
            return

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return
        
        # Walking animation
        if self.change_x != 0 and self.change_y == 0:
            self.cur_texture += 1
            if self.cur_texture >= 8 * UPDATES_PER_FRAME:
                self.cur_texture = 0
            frame = self.cur_texture // UPDATES_PER_FRAME
            direction = self.character_face_direction
            self.texture = self.walk_textures[frame][direction]

        # Rolling animation
        if self.is_rolling:
            total_frames = len(self.roll_texture_pairs)
            frame = self.cur_roll_frame // UPDATES_PER_FRAME
            if frame >= total_frames:
                frame = total_frames - 1
            self.texture = (self.roll_texture_pairs[frame]
                            [self.character_face_direction])
            self.cur_roll_frame += 1

            if self.change_y == 0:
                self.texture = (self.roll_texture_pairs[frame]
                                [self.character_face_direction])
                self.cur_roll_frame += 1
            elif self.change_y < 0:
                self.texture = (self.fall_texture_pair
                                [self.character_face_direction])
                self.was_on_ground_last_frame = False
                return
            
            return

# Base enemy entity class        
class Entity(arcade.Sprite):
    """Base entity class for all game characters."""
    
    def __init__(self, name_folder, name_file):
        super().__init__()

        self.facing_direction = RIGHT_FACING
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        main_path = f"{name_folder}/{name_file}"

        # Load spider walking textures
        self.walk_textures = []
        path = os.path.join(os.path.dirname(__file__), 
                            "Characters/Enemies/spider")
        for i in range(1, 6):
            texture = arcade.load_texture(f"{path}{i}.png")
            self.walk_textures.append([texture.flip_horizontally(), texture])

        self.texture = self.walk_textures[0][0]

# Enemy behavior system
class Enemy(Entity):
    """Enemy with basic AI and animation."""
    
    def __init__(self, name_folder, name_file):
        super().__init__(name_folder, name_file)
        self.should_update_walk = 0

    def update_animation(self, delta_time: float = 1 / 60):
        """Update enemy animation and facing direction."""
        
        if self.change_x < 0:
            self.facing_direction = LEFT_FACING
        elif self.change_x > 0:
            self.facing_direction = RIGHT_FACING

        # Walking animation with frame timing
        if self.should_update_walk == 3:
            self.cur_texture += 1
            if self.cur_texture > 4:
                self.cur_texture = 0
            self.texture = (self.walk_textures[self.cur_texture]
                            [self.facing_direction])
            self.should_update_walk = 0
            return

        self.should_update_walk += 1

# Spider enemy with patrol behavior
class Spider(Enemy):
    """Spider enemy that patrols back and forth."""
    
    def __init__(self, name_folder="Enemies", name_file="spider"):
        super().__init__(name_folder, name_file)
        
        self.speed = 2
        self.direction = -1
        self.patrol_distance = 128 
        self.start_x = 0.0
        self.health = 1
        
    def setup_patrol(self, start_x):
        """Set up patrol boundaries for spider movement."""
        self.start_x = float(start_x)
        self.center_x = float(start_x)
        
    def update(self):
        """Update spider movement and patrol behavior."""
        
        distance_from_start = abs(self.center_x - self.start_x)
        
        # Reverse direction at patrol boundary
        if distance_from_start >= self.patrol_distance:
            self.direction *= -1
            
        self.change_x = self.speed * self.direction
        
        super().update()
        self.update_animation()

# Boss enemy with jump attacks
class Boss(Enemy):
    """Boss enemy with jumping and advanced AI."""
    
    def __init__(self, name_folder="Enemies", name_file="boss"):
        super().__init__(name_folder, name_file)
        
        self.speed = 4
        self.direction = 1
        self.patrol_distance = 800
        self.start_x = 0.0
        self.health = 10

        # Jump attack system
        self.jump_timer = 0.0
        self.jump_interval = 5.0
        self.is_jumping = False
        self.jump_strength = 20
        self.boss_damaged = False
        
        self.load_boss_textures()

    def load_boss_textures(self):
        """Load all boss animation textures."""
        
        self.walk_textures = []
        path = os.path.join(os.path.dirname(__file__), 
                            "Characters/Enemies/boss")
        
        # Load walking frames
        for i in range(1, 13):
            texture = arcade.load_texture(f"{path}{i}.png")
            self.walk_textures.append([texture, texture.flip_horizontally()])
        
        # Load special attack textures
        jump_texture = arcade.load_texture(f"{path}_jump.png")
        self.jump_texture_pair = [jump_texture, 
                                  jump_texture.flip_horizontally()]
        
        fall_texture = arcade.load_texture(f"{path}_fall.png")
        self.fall_texture_pair = [fall_texture, 
                                  fall_texture.flip_horizontally()]

        damaged_texture = arcade.load_texture(f"{path}_damaged.png")
        self.damaged_texture_pair = [damaged_texture, 
                                     damaged_texture.flip_horizontally()]
        
        self.texture = self.walk_textures[0][0]
        
    def setup_patrol(self, start_x):
        """Set up patrol boundaries for boss movement."""
        self.start_x = float(start_x)
        self.center_x = float(start_x)
        
    def update_animation(self, delta_time: float = 1 / 60):
        """Update boss animation based on current state."""
        
        if self.change_x > 0:
            self.facing_direction = LEFT_FACING
        elif self.change_x < 0:
            self.facing_direction = RIGHT_FACING
        
        # Jump and fall animations
        if self.change_y > 0:
            self.texture = self.jump_texture_pair[self.facing_direction]
            return
            
        if self.change_y < 0:
            self.texture = self.fall_texture_pair[self.facing_direction]
            return
        
        # Walking animation when on ground
        if self.change_x != 0 and self.change_y == 0:
            if self.should_update_walk == 15:
                self.cur_texture += 1
                if self.cur_texture >= len(self.walk_textures):
                    self.cur_texture = 0
                self.texture = (self.walk_textures[self.cur_texture]
                                [self.facing_direction])
                self.should_update_walk = 0
                return
            self.should_update_walk += 1
        else:
            self.texture = self.walk_textures[0][self.facing_direction]
        
    def update(self, delta_time=1/60):
        """Update boss movement, patrol behavior, and jumping."""
        
        # Jump attack timing
        self.jump_timer += delta_time
        
        if self.jump_timer >= self.jump_interval and self.change_y == 0:
            self.change_y = self.jump_strength
            self.jump_timer = 0.0
            self.is_jumping = True

        # Ground movement only
        if self.change_y == 0:
            distance_from_start = abs(self.center_x - self.start_x)
            
            if distance_from_start >= self.patrol_distance:
                self.direction *= -1
                
            self.change_x = self.speed * self.direction
        else:
            self.change_x = 0
        
        super().update()
        self.update_animation(delta_time)

# Player attack effect
class Slash_attack(arcade.Sprite):
    """Slash attack effect that follows the player."""
    
    def __init__(self, player_sprite, player_direction):
        super().__init__()
        
        self.player_sprite = player_sprite
        self.offset_distance = 50
        
        # Load slash animation
        self.slash_texture_pairs = []
        slash_path = os.path.join(os.path.dirname(__file__), 
                                  "Projectiles/slash")
        for frame in range(1, 10):
            slash = arcade.load_texture(f"{slash_path}{frame}.png")
            self.slash_texture_pairs.append([slash, 
                                             slash.flip_horizontally()])
        
        self.cur_frame = 0
        self.frame_timer = 0
        self.frames_per_texture = 3
        self.player_direction = player_direction
        
        self.texture = (self.slash_texture_pairs[0][self.player_direction])
        self.scale = CHARACTER_SCALING
        
        self.update_position()
        self.is_finished = False
    
    def update_position(self):
        """Keep slash positioned next to player."""
        if self.player_direction == RIGHT_FACING:
            self.center_x = self.player_sprite.center_x + self.offset_distance
        else:
            self.center_x = self.player_sprite.center_x - self.offset_distance
        self.center_y = self.player_sprite.center_y
    
    def update(self, delta_time=1/60):
        """Update slash position and animation."""
        
        self.update_position()
        
        # Animation timing
        self.frame_timer += 1
        
        if self.frame_timer >= self.frames_per_texture:
            self.frame_timer = 0
            self.cur_frame += 1
            
            if self.cur_frame >= len(self.slash_texture_pairs):
                self.is_finished = True
                return
            
            self.texture = (self.slash_texture_pairs[self.cur_frame]
                            [self.player_direction])

# Main game class
class GameView(arcade.Window):
    """Main game window and logic controller."""
    
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

        # Core game systems
        self.tile_map = None
        self.scene = None
        self.camera = None
        self.gui_camera = None
        self.player_sprite_list = None
        self.physics_engine = None
        self.background = None
        self.player = None

        # Input tracking
        self.left_held = False
        self.right_held = False
        self.last_direction_key = None

        # Rolling system
        self.is_rolling = False
        self.roll_timer = 0
        self.can_roll = True
        self.roll_cooldown_timer = 0
        self.roll_direction = 0

        # Player stats
        self.base_speed = 5
        self.base_jump = 18
        self.base_dmg = 1
        self.base_roll = 0
        self.base_gold = 0

        # Load player textures
        character = os.path.join(os.path.dirname(__file__), 
                                 "Characters/Player/knight")

        idle = arcade.load_texture(f"{character}_idle.png")
        self.idle_texture_pair = idle, idle.flip_left_right()

        self.walk_texture_pairs = []
        for frame in range(1,11):
            texture = arcade.load_texture(f"{character}{frame}.png")
            self.walk_texture_pairs.append((texture, 
                                            texture.flip_left_right()))

        jump = arcade.load_texture(f"{character}_jump.png")
        self.jump_texture_pair = jump, jump.flip_left_right()

        fall = arcade.load_texture(f"{character}_fall.png")
        self.fall_texture_pair = (fall, fall.flip_left_right())
        
        land = arcade.load_texture(f"{character}_land.png")
        self.land_texture_pair = (land, land.flip_left_right())

        self.roll_textures = []
        for frame in range(1,4):
            texture = arcade.load_texture(f"{character}_roll{frame}.png")
            self.roll_textures.append((texture, texture.flip_left_right()))

        self.swing_textures = []
        for frame in range(1,4):
            texture = arcade.load_texture(f"{character}_swing{frame}.png")
            self.swing_textures.append((texture, texture.flip_left_right()))

        # UI popup system
        self.show_collected_popup = False
        self.popup_timer = 0
        self.show_dmg_popup = False
        self.show_victory_popup = False

        self.show_gold = True
        self.not_enough_gold_popup = False

        self.show_controls = True

        # Level progression system
        self.stages = [
            {
                "map": "intro.tmx",
                "background": "intro.png"
            },
            {
                "map": "stage_1.tmx",
                "background": "stage_1.png"
            },
            {
                "map": "stage_2.tmx",
                "background": "stage_2.png"
            }
        ]
        self.current_stage = 0

        arcade.set_background_color((44, 31, 22))
        
    def setup(self, stage_index=0):
        """Initialize game world and load level data."""
        
        self.current_stage = stage_index
        stage_data = self.stages[stage_index]
        
        # Tilemap layer configuration
        layer_options = {
            "Platforms": {
                "use_spatial_hash": True
            },
            "Chests": {
                "use_spatial_hash": True
            },
            "Obstacles":  {
                "use_spatial_hash": True 
            },
            "Moving_enemies": {
                "use_spatial_hash": True
            },
            "Enemies": {
            "use_spatial_hash": True
            },
            "Exit": {"use_spatial_hash": True
                     },
            "Boss": {"use_spatial_hash": True
            },
        }

        # Load tilemap and create scene
        map_path = os.path.join(os.path.dirname(__file__), 
                                stage_data["map"])
        self.tile_map = arcade.load_tilemap(map_path, 
                                            scaling=TILE_SCALING, 
                                            layer_options=layer_options, 
                                            use_spatial_hash=True)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Setup background
        background_path = os.path.join(os.path.dirname(__file__), 
                                       stage_data["background"])
        bg = arcade.Sprite(background_path)
        bg.center_x = 6400
        bg.center_y = 1250
        bg.width = 12800
        bg.height = 2000
        self.background_list = arcade.SpriteList()
        self.background_list.append(bg)

        # Initialize sprite lists
        self.player_sprite_list = arcade.SpriteList()
        self.slash_list = arcade.SpriteList()

        # Create player character
        self.player = PlayerCharacter(
            self.idle_texture_pair,
            self.walk_texture_pairs,
            self.jump_texture_pair,
            self.fall_texture_pair,
            self.land_texture_pair,
            self.roll_textures,
            self.swing_textures
        )

        self.player.center_x = WINDOW_WIDTH / 2 - 400
        self.player.center_y = WINDOW_HEIGHT / 2
        self.player_sprite_list.append(self.player)
        self.scene.add_sprite_list_before("Player", "Foreground")
        self.scene.add_sprite("Player", self.player)

        if "Moving_enemies" not in self.scene:
            self.scene.add_sprite_list("Moving_enemies")

        # Setup physics
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, walls=self.scene["Platforms"], 
            gravity_constant=GRAVITY
        )

        # Setup cameras
        self.camera = arcade.Camera2D(zoom=0.7)
        self.gui_camera = arcade.Camera2D()

        self.spider_physics_engines = []
        
        # Spawn enemies from tilemap
        self.spawn_spiders()
        self.spawn_bosses()

    def spawn_spiders(self):
        """Create spider enemies from tilemap object data."""
        
        try:
            if (hasattr(self.tile_map, 'object_lists') and 
                "Moving_enemies" in self.tile_map.object_lists):
                enemy_objects = self.tile_map.object_lists["Moving_enemies"]
                
                for i, enemy_object in enumerate(enemy_objects):
                    spider = Spider()
                    
                    coords_found = False
                    
                    # Try different ways to get position data
                    if (hasattr(enemy_object, 'x') and 
                        hasattr(enemy_object, 'y')):
                        spider.center_x = float(enemy_object.x)
                        spider.center_y = float(enemy_object.y)
                        coords_found = True
                    
                    elif (hasattr(enemy_object, 'shape') and 
                          len(enemy_object.shape) >= 2):
                        shape = enemy_object.shape
                        
                        if (isinstance(shape, (list, tuple)) and 
                            len(shape) > 0):
                            first_point = shape[0]
                            if (isinstance(first_point, (list, tuple)) and 
                                len(first_point) >= 2):
                                spider.center_x = float(first_point[0])
                                spider.center_y = float(first_point[1])
                                coords_found = True
                            elif len(shape) >= 2:
                                spider.center_x = float(shape[0])
                                spider.center_y = float(shape[1])
                                coords_found = True
                    
                    elif (hasattr(enemy_object, 'properties') and 
                          enemy_object.properties):
                        if ('x' in enemy_object.properties and 
                            'y' in enemy_object.properties):
                            spider.center_x = float(
                                enemy_object.properties['x'])
                            spider.center_y = float(
                                enemy_object.properties['y'])
                            coords_found = True
                    
                    if not coords_found:
                        spider.center_x = 500.0 + (i * 100)
                        spider.center_y = 400.0
                    
                    spider.setup_patrol(spider.center_x)
                    self.scene.add_sprite("Moving_enemies", spider)
                    
                    # Create physics for spider
                    spider_physics = arcade.PhysicsEnginePlatformer(
                        spider, walls=self.scene["Platforms"], 
                        gravity_constant=GRAVITY
                    )
                    self.spider_physics_engines.append(spider_physics)
                    
        except Exception as e:
            import traceback
            traceback.print_exc()

    def spawn_bosses(self):
        """Create boss enemies from tilemap object data."""
        
        try:
            if (hasattr(self.tile_map, 'object_lists') and 
                "Boss" in self.tile_map.object_lists):
                boss_objects = self.tile_map.object_lists["Boss"]
                
                for i, boss_object in enumerate(boss_objects):
                    boss = Boss()
                    
                    coords_found = False
                    
                    # Get position using same methods as spiders
                    if (hasattr(boss_object, 'x') and 
                        hasattr(boss_object, 'y')):
                        boss.center_x = float(boss_object.x)
                        boss.center_y = float(boss_object.y)
                        coords_found = True
                    
                    elif (hasattr(boss_object, 'shape') and 
                          len(boss_object.shape) >= 2):
                        shape = boss_object.shape
                        if (isinstance(shape, (list, tuple)) and 
                            len(shape) > 0):
                            first_point = shape[0]
                            if (isinstance(first_point, (list, tuple)) and 
                                len(first_point) >= 2):
                                boss.center_x = float(first_point[0])
                                boss.center_y = float(first_point[1])
                                coords_found = True
                            elif len(shape) >= 2:
                                boss.center_x = float(shape[0])
                                boss.center_y = float(shape[1])
                                coords_found = True
                    
                    elif (hasattr(boss_object, 'properties') and 
                          boss_object.properties):
                        if ('x' in boss_object.properties and 
                            'y' in boss_object.properties):
                            boss.center_x = float(
                                boss_object.properties['x'])
                            boss.center_y = float(
                                boss_object.properties['y'])
                            coords_found = True
                    
                    if not coords_found:
                        boss.center_x = 800.0 + (i * 200)
                        boss.center_y = 400.0
                    
                    boss.setup_patrol(boss.center_x)
                    
                    self.scene.add_sprite("Moving_enemies", boss)
                    
                    # Create physics for boss
                    boss_physics = arcade.PhysicsEnginePlatformer(
                        boss, walls=self.scene["Platforms"], 
                        gravity_constant=GRAVITY
                    )
                    self.spider_physics_engines.append(boss_physics)
                    
        except Exception as e:
            import traceback
            traceback.print_exc()

    def on_update(self, delta_time):
        """Main game update loop."""
        
        # Update core systems
        self.physics_engine.update()
        self.player_sprite_list.update()
        self.player.update_animation(delta_time)
        
        # Update enemy physics and AI
        for spider_physics in self.spider_physics_engines:
            spider_physics.update()
        
        spider_list = self.scene.get_sprite_list("Moving_enemies")
        if spider_list:
            for spider in spider_list:
                spider.update()
        
        # Update attack effects
        self.slash_list.update()
        
        # Handle combat collisions
        for slash in self.slash_list:
            if slash.is_finished:
                slash.remove_from_sprite_lists()
                continue
            
            # Attack hits static enemies
            if "Enemies" in self.scene:
                hit_enemies = arcade.check_for_collision_with_list(
                    slash, self.scene["Enemies"])
                for enemy in hit_enemies:
                    enemy.remove_from_sprite_lists()
                    self.base_gold += 10
            
            # Attack hits moving enemies
            if "Moving_enemies" in self.scene:
                hit_enemies = arcade.check_for_collision_with_list(
                    slash, self.scene["Moving_enemies"])
                for enemy in hit_enemies:
                    if isinstance(enemy, Boss):
                        enemy.health -= self.base_dmg
                        if enemy.health <= 0:
                            enemy.remove_from_sprite_lists()
                            # Remove physics engine
                            for i, physics in enumerate(
                                self.spider_physics_engines):
                                if physics.player_sprite == enemy:
                                    self.spider_physics_engines.pop(i)
                                    break
                            self.show_victory_popup = True
                            self.popup_timer = 1000
                    else:
                        enemy.remove_from_sprite_lists()
                        # Remove physics engine
                        for i, physics in enumerate(
                            self.spider_physics_engines):
                            if physics.player_sprite == enemy:
                                self.spider_physics_engines.pop(i)
                                break
                        self.base_gold += 10

        self.scene.update_animation(delta_time)
        self.camera.position = self.player.position 

        # Player damage system
        if ((arcade.check_for_collision_with_list(
            self.player, self.scene["Moving_enemies"]) or 
             arcade.check_for_collision_with_list(
                 self.player, self.scene["Enemies"])) and 
            not self.is_rolling):            
            self.reset_player_position()
            self.show_dmg_popup = True
            self.popup_timer = 3.0

        if arcade.check_for_collision_with_list(
            self.player, self.scene["Obstacles"]):
            self.reset_player_position()
            self.show_dmg_popup = True
            self.popup_timer = 3.0

        # UI popup timers
        if self.show_dmg_popup: 
            self.popup_timer -= delta_time

            if self.popup_timer <= 0:
                self.show_dmg_popup = False

        if self.show_collected_popup:
            self.popup_timer -= delta_time
            if self.popup_timer <= 0:
                self.show_collected_popup = False
                
        if self.not_enough_gold_popup:
            self.popup_timer -= delta_time
            if self.popup_timer <= 0:
                self.not_enough_gold_popup = False

        if self.show_victory_popup:
            self.popup_timer -= delta_time
            if self.popup_timer <= 0:
                self.show_victory_popup = False

        # Rolling mechanics
        self.player.is_rolling = self.is_rolling
        if self.is_rolling:
            self.roll_timer -= delta_time
            roll_speed = self.base_speed + self.base_roll + 4
            self.player.change_x = self.roll_direction * roll_speed
                
            if self.roll_timer <= 0:
                self.is_rolling = False
                self.player.is_rolling = False
                self.player.cur_roll_frame = 0
                self.roll_cooldown_timer = 0
                self.can_roll = False

                # Resume movement if keys still held
                if self.left_held:
                    self.player.change_x = -self.base_speed
                elif self.right_held:
                    self.player.change_x = self.base_speed
                else:
                    self.player.change_x = 0

        if not self.can_roll and not self.is_rolling:
            self.roll_cooldown_timer -= delta_time
            if self.roll_cooldown_timer <= 0:
                self.can_roll = True

        # Normal movement when not rolling
        if not self.is_rolling:
            if self.last_direction_key == "left":
                self.player.change_x = -self.base_speed
            elif self.last_direction_key == "right":
                self.player.change_x = self.base_speed
            else:
                self.player.change_x = 0
        
        # Attack animation system
        if self.player.is_attacking:
            frame = self.player.cur_swing_frame // UPDATES_PER_FRAME
            if frame < len(self.player.swing_textures):
                direction = self.player.character_face_direction
                self.player.texture = (self.player.swing_textures[frame]
                                       [direction])
                self.player.cur_swing_frame += 1
            else:
                self.player.is_attacking = False
                self.player.cur_swing_frame = 0

    def reset_player_position(self):
        """Reset player to starting position after taking damage."""
        self.player.center_x = WINDOW_WIDTH / 2 - 400
        self.player.center_y = WINDOW_HEIGHT / 2
        self.player.change_x = 0
        self.player.change_y = 0

    def on_key_press(self, key, modifiers):
        """Handle keyboard input for player actions."""
        
        # Interact with objects
        if key == arcade.key.E:
            gold_stat = self.base_gold

            # Check for treasure chests
            chest_hit_list = arcade.check_for_collision_with_list(
                self.player, self.scene["Chests"])
            for chest in chest_hit_list:
                gold_stat = self.base_gold
                if gold_stat >= 20:
                    self.base_gold -= 20
                    chest.remove_from_sprite_lists()

                    # Random item upgrade system
                    selected_item = random.choice(common_item_pool)
                    item_list.append(selected_item)

                    if selected_item == "SpeedUp":
                        self.base_speed += 2
                    elif selected_item == "DmgUp":
                        self.base_dmg += 1
                    elif selected_item == "JumpUp":
                        self.base_jump += 2
                    elif selected_item == "RollUp":
                        self.base_roll += 2

                    self.show_collected_popup = True
                    self.popup_timer = 4.0  
                elif gold_stat < 20:
                    self.not_enough_gold_popup = True
                    self.popup_timer = 3.0

            # Check for level exit
            if "Exit" in self.scene:
                exit_hit_list = arcade.check_for_collision_with_list(
                    self.player, self.scene["Exit"])
                if (exit_hit_list and 
                    self.current_stage < len(self.stages) - 1):
                    self.current_stage += 1
                    self.setup(self.current_stage)
                    self.reset_player_position()
                    return
                    
        # Jump controls
        elif (key in (arcade.key.UP, arcade.key.W, arcade.key.SPACE) and 
              not self.is_rolling):
            if self.physics_engine.can_jump():
                jump_stat = self.base_jump
                self.player.change_y = jump_stat
                
        # Movement controls
        elif key in (arcade.key.LEFT, arcade.key.A, 
                     arcade.key.RIGHT, arcade.key.D):
            speed_stat = self.base_speed
            if key in (arcade.key.LEFT, arcade.key.A):
                self.left_held = True
                self.last_direction_key = "left"
                if not self.is_rolling:
                    self.player.change_x = -speed_stat

            elif key in (arcade.key.RIGHT, arcade.key.D):
                self.right_held = True
                self.last_direction_key = "right"
                if not self.is_rolling:
                    self.player.change_x = speed_stat

        # Roll/dodge ability
        elif (key == arcade.key.LSHIFT and self.can_roll and 
              not self.is_rolling):
            self.is_rolling = True
            self.roll_timer = 0.3

            if self.player.character_face_direction == RIGHT_FACING:
                self.roll_direction = 1
            else:
                self.roll_direction = -1

        # Quit game
        elif key in (arcade.key.ESCAPE, arcade.key.Q):
            arcade.close_window()

        # Melee attack
        elif (key == arcade.key.C and not self.player.is_attacking and 
              not self.is_rolling):
            self.player.is_attacking = True
            self.player.cur_swing_frame = 0
            
            # Create slash effect
            slash = Slash_attack(
                self.player,
                self.player.character_face_direction
            )
            self.slash_list.append(slash)

    def on_key_release(self, key, modifiers):
        """Handle keyboard key release events."""
        
        if key in (arcade.key.LEFT, arcade.key.A):
            self.left_held = False
            if self.last_direction_key == "left":
                self.last_direction_key = ("right" if self.right_held 
                                           else None)

        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_held = False
            if self.last_direction_key == "right":
                self.last_direction_key = ("left" if self.left_held 
                                           else None)

    def on_draw(self):
        """Render all game graphics and UI elements."""
        
        self.clear()
        
        # Draw game world
        self.camera.use()
        self.background_list.draw()

        self.scene.draw()
        self.slash_list.draw()

        # Draw UI elements
        self.gui_camera.use()

        # Death popup
        if self.show_dmg_popup:
            text= f"You died and lost all of your gold!"
            font_size = 36
            x = WINDOW_WIDTH // 2 - 300
            y = 100 
            self.base_gold = 0
            arcade.draw_text(
                text,
                x,
                y,
                arcade.color.WHITE,
                font_size,
                 bold=True
            )
            
        # Victory popup
        if self.show_victory_popup:
            text= f"Boss slain! You win! Press ESCAPE to restart"
            font_size = 34
            x = WINDOW_WIDTH // 2 - 300
            y = 100 
            arcade.draw_text(
                text,
                x,
                y,
                arcade.color.WHITE,
                font_size,
                 bold=True
            )

        # Item collected popup
        if self.show_collected_popup:
            text = f"{item_list[-1]} Collected"
            font_size = 24
            x = WINDOW_WIDTH // 2 - 90 
            y = 60 

            arcade.draw_text(
                text,
                x,
                y,
                arcade.color.WHITE,
                font_size,
                bold=True
            )

        # Not enough gold popup
        if self.not_enough_gold_popup:
            text = f"Not enough gold!"
            font_size = 24
            x = WINDOW_WIDTH // 2 - 90 
            y = 60 

            arcade.draw_text(
                text,
                x,
                y,
                arcade.color.WHITE,
                font_size,
                bold=True
            )

        # Gold counter
        if self.show_gold: 
            text = f"Gold: {self.base_gold}"
            font_size = 18
            x = WINDOW_WIDTH // 1 - 100 
            y = 10

            arcade.draw_text(
                text,
                x,
                y,
                arcade.color.WHITE,
                font_size,
            )

        # Control instructions
        if self.show_controls:
            text = (f"Shift=Roll/Dive     E=Interact (chests cost $20)     "
                    f"C=Attack")
            font_size = 18 
            x = WINDOW_WIDTH // 1 - 1000 
            y = 650

            arcade.draw_text(
                text,
                x,
                y,
                arcade.color.WHITE,
                font_size,
            )

def main():
    """Initialize and run the game."""
    window = GameView()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()
        