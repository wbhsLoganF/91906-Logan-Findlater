import arcade
import os
import random

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "TITLE"

TILE_SCALING = 1
GRAVITY = 0.9

UPDATES_PER_FRAME = 7

RIGHT_FACING = 0
LEFT_FACING = 1

CHARACTER_SCALING = 1


#All available 
common_item_pool = ["SpeedUp", "DmgUp", "JumpUp"]
rare_item_pool = ["DoubleJump", "ExtraLife", ]
#Collected items
item_list = []


class PlayerCharacter(arcade.Sprite):
    def __init__(self, idle_texture_pair, walk_texture_pairs, jump_texture_pair, fall_texture_pair, land_texture_pair, roll_texture_pairs, swing_texture_pairs):
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

        
        self.walk_textures = walk_texture_pairs
        self.swing_textures = swing_texture_pairs
        self.idle_texture_pair = idle_texture_pair
        self.jump_texture_pair = jump_texture_pair
        self.fall_texture_pair = fall_texture_pair
        self.land_texture_pair = land_texture_pair
        self.roll_textures = roll_texture_pairs


        self.is_attacking = False
        self.cur_swing_frame = 0

        super().__init__(self.idle_texture_pair[0], scale=CHARACTER_SCALING)

    def update_animation(self, delta_time: float = 1 / 60):

        # Change player texture directions left/right
        if self.change_x < 0:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0:
            self.character_face_direction = RIGHT_FACING

    	# Jumping
        if self.change_y > 0:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return

        # Just landed = start landing animation
        if self.change_y == 0 and not self.was_on_ground_last_frame:
            self.texture = self.land_texture_pair[self.character_face_direction]
            self.was_on_ground_last_frame = True
            return
        # Hold the landing player texture
        if self.land_frame_timer > 0:
            self.land_frame_timer -= delta_time
            self.texture = self.land_texture_pair[self.character_face_direction]
            return


        # Idle
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return
        
        # Walking
        if self.change_x != 0 and self.change_y == 0:
            self.cur_texture += 1
            if self.cur_texture >= 8 * UPDATES_PER_FRAME:
                self.cur_texture = 0
            frame = self.cur_texture // UPDATES_PER_FRAME
            direction = self.character_face_direction
            self.texture = self.walk_textures[frame][direction]

        if self.is_rolling:
            total_frames = len(self.roll_texture_pairs)
            frame = self.cur_roll_frame // UPDATES_PER_FRAME
            if frame >= total_frames:
                frame = total_frames - 1  # Stay on the last frame if past the end
            self.texture = self.roll_texture_pairs[frame][self.character_face_direction]
            self.cur_roll_frame += 1

            if self.change_y == 0:
                self.texture = self.roll_texture_pairs[frame][self.character_face_direction]
                self.cur_roll_frame += 1
            elif self.change_y < 0:
                self.texture = self.fall_texture_pair[self.character_face_direction]
                self.was_on_ground_last_frame = False
                return
            
            return
        
class GameView(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

        self.tile_map = None
        self.scene = None
        self.camera = None
        self.gui_camera = None
        self.player_sprite_list = None
        self.physics_engine = None
        self.background = None
        self.player = None

        self.left_held = False
        self.right_held = False
        self.last_direction_key = None

        self.is_rolling = False
        self.roll_timer = 0
        self.can_roll = True
        self.roll_cooldown_timer = 0
        self.roll_direction = 0

        self.base_speed = 8
        self.base_jump = 18
        self.base_dmg = 1
        self.base_gold = 0

        #Setting up all player sprite frames

        character = os.path.join(os.path.dirname(__file__), "Characters/Player/knight")

        idle = arcade.load_texture(f"{character}_idle.png")
        self.idle_texture_pair = idle, idle.flip_left_right()

        self.walk_texture_pairs = []
        for frame in range(1,11):
            texture = arcade.load_texture(f"{character}{frame}.png")
            self.walk_texture_pairs.append((texture, texture.flip_left_right()))

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

        '''
        self.enemy_texture_pairs = []
        path = os.path.join(os.path.dirname(__file__), "Characters/Enemies/spider")
        for i in range(1, 6):
            texture = arcade.load_texture(f"{path}{i}.png")
            self.enemy_texture_pairs.append((texture, texture.flip_left_right()))
            '''





        self.show_collected_popup = False
        self.popup_timer = 0
        self.show_dmg_popup = False
        self.show_door_popup = False
        self.show_gold = True

        self.show_controls = True


        background_path = os.path.join(os.path.dirname(__file__),"cave_background_1.png")
        bg = arcade.Sprite(background_path)
        bg.center_x = 6400
        bg.center_y = 1250
        bg.width = 12800
        bg.height = 2000
        self.background_list = arcade.SpriteList()
        self.background_list.append(bg)


        arcade.set_background_color((44, 31, 22))
        
    def setup(self):
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
            }
        }
        map_path = os.path.join(os.path.dirname(__file__), "stage_1.tmx")
        self.tile_map = arcade.load_tilemap(map_path, scaling=TILE_SCALING, layer_options=layer_options, use_spatial_hash=True)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)



        self.player_sprite_list = arcade.SpriteList()


        self.player = PlayerCharacter(
            self.idle_texture_pair,
            self.walk_texture_pairs,
            self.jump_texture_pair,
            self.fall_texture_pair,
            self.land_texture_pair,
            self.roll_textures,
            self.swing_textures
        )
        self.player.center_x = WINDOW_WIDTH / 2
        self.player.center_y = WINDOW_HEIGHT / 2
        self.player_sprite_list.append(self.player)
        self.scene.add_sprite_list_before("Player", "Foreground")
        self.scene.add_sprite("Player", self.player)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, walls=self.scene["Platforms"], gravity_constant=GRAVITY
        )

        self.camera = arcade.Camera2D(zoom=0.45)
        self.gui_camera = arcade.Camera2D()


    def on_update(self, delta_time):
        self.physics_engine.update()
        self.player_sprite_list.update()
        self.player.update_animation(delta_time)
        self.scene.update_animation(delta_time)

        self.camera.position = self.player.position 

        if arcade.check_for_collision_with_list(self.player, self.scene["Obstacles"]) or arcade.check_for_collision_with_list(self.player, self.scene["Moving_enemies"]) or arcade.check_for_collision_with_list(self.player, self.scene["Enemies"]):
            self.reset_player_position()
            self.show_dmg_popup = True
            self.popup_timer = 5.0

        if self.show_dmg_popup: 
            self.popup_timer -= delta_time
            if self.popup_timer <= 0:
                self.show_dmg_popup = False

        if self.show_collected_popup:
            self.popup_timer -= delta_time
            if self.popup_timer <= 0:
                self.show_collected_popup = False



        # Rolling
        self.player.is_rolling = self.is_rolling
        if self.is_rolling:
            self.roll_timer -= delta_time
            roll_speed = self.base_speed + 10
            self.player.change_x = self.roll_direction * roll_speed
                

            if self.roll_timer <= 0:
                self.is_rolling = False
                self.player.is_rolling = False
                self.player.cur_roll_frame = 0
                self.roll_cooldown_timer = 0
                self.can_roll = False

                # Resume movement if keys are still held, otherwise stop
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

        # Overide direction for a quick tap
        if not self.is_rolling:
            if self.last_direction_key == "left":
                self.player.change_x = -self.base_speed
            elif self.last_direction_key == "right":
                self.player.change_x = self.base_speed
            else:
                self.player.change_x = 0
        
        if self.player.is_attacking:
            frame = self.player.cur_swing_frame // UPDATES_PER_FRAME
            if frame < len(self.player.swing_textures):
                direction = self.player.character_face_direction
                self.player.texture = self.player.swing_textures[frame][direction]
                self.player.cur_swing_frame += 1
            else:
                self.player.is_attacking = False
                self.player.cur_swing_frame = 0
        
        if len(self.scene["Chests"]) == 0:
            self.show_door_popup = True 


        

    def reset_player_position(self):
        self.player.center_x = WINDOW_WIDTH / 2
        self.player.center_y = WINDOW_HEIGHT / 2
        self.player.change_x = 0
        self.player.change_y = 0

    def on_key_press(self, key, modifiers):
        if key == arcade.key.E:
            gold_stat = self.base_gold
            # Check for chests the player is touching
            chest_hit_list = arcade.check_for_collision_with_list(self.player, self.scene["Chests"])
            for chest in chest_hit_list:
                gold_stat = self.base_gold
                if gold_stat >= 20:
                    self.base_gold -= 20
                    chest.remove_from_sprite_lists()

                    selected_item = random.choice(common_item_pool)
                    item_list.append(selected_item)
                    print(item_list)

                    if selected_item == "SpeedUp":
                        print("SPEED UP!")
                        self.base_speed += 2
                    elif selected_item == "DmgUp":
                        print("DMG UP!")
                        self.base_dmg += 1
                    elif selected_item == "JumpUp":
                        print("JUMP UP!")
                        self.base_jump += 2

                    #Pop up menu 
                    self.show_collected_popup = True
                    self.popup_timer = 5.0  
                elif gold_stat < 20:
                    print("Not enough GOLD!")
                    
        elif key == arcade.key.K:
            self.base_gold += 80
        # Jump
        elif key in (arcade.key.UP, arcade.key.W, arcade.key.SPACE) and not self.is_rolling:
            if self.physics_engine.can_jump():
                jump_stat = self.base_jump
                self.player.change_y = jump_stat
                

        # Move left/right
        elif key in (arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D):
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


        elif key == arcade.key.LSHIFT and self.can_roll and not self.is_rolling:
            self.is_rolling = True
            self.roll_timer = 0.3

            if self.player.character_face_direction == RIGHT_FACING:
                self.roll_direction = 1
            else:
                self.roll_direction = -1

        # Quit
        elif key in (arcade.key.ESCAPE, arcade.key.Q):
            arcade.close_window()

        #   Melee Attack
        elif key == arcade.key.C and not self.player.is_attacking and not self.is_rolling:
            self.player.is_attacking = True
            self.player.cur_swing_frame = 0


    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.left_held = False
            if self.last_direction_key == "left":
                self.last_direction_key = "right" if self.right_held else None

        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_held = False
            if self.last_direction_key == "right":
                self.last_direction_key = "left" if self.left_held else None

    def on_draw(self):
        self.clear()
        
        self.camera.use()
        self.background_list.draw()

        self.scene.draw()

        self.gui_camera.use()

        

        if self.show_dmg_popup:
            text= f"YOU DIED"
            font_size = 164
            x = WINDOW_WIDTH // 2 - 400
            y = 200 
            self.base_gold = 0
            arcade.draw_text(
                text,
                x,
                y,
                arcade.color.WHITE,
                font_size,
                 bold=True
            )

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
        
        if self.show_door_popup:
            self.popup_timer = 10

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

        if self.show_controls:
            text = f"C = Attack \n  LSHIFT = Roll   \n  E = Open chest \n  K = Collect dividends from the kingdom"
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
    window = GameView()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
 