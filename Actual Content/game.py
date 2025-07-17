import arcade
import os
import random

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "TITLE"

TILE_SCALING = 1
PLAYER_JUMP_SPEED = 20
jump_stat = 20
GRAVITY = 1

speed_stat = 10
UPDATES_PER_FRAME = 7

RIGHT_FACING = 0
LEFT_FACING = 1

CHARACTER_SCALING = 1


speed_stat = 10
jump_stat = 20
dmg_stat = 1
gold_stat = 0

#All available 
item_pool = ["SpeedUp", "DmgUp", "JumpUp"]
#Collected items
item_list = []

class PlayerCharacter(arcade.Sprite):
    def __init__(self, idle_texture_pair, walk_texture_pairs, jump_texture_pair, fall_texture_pair, land_texture_pair, roll_texture_pairs):
        self.character_face_direction = RIGHT_FACING
        self.cur_texture = 0

        self.roll_texture_pairs = roll_texture_pairs
        self.cur_roll_frame = 0

        self.was_on_ground_last_frame = True
        self.land_frame_timer = 0

        
        self.walk_textures = walk_texture_pairs
        self.idle_texture_pair = idle_texture_pair
        self.jump_texture_pair = jump_texture_pair
        self.fall_texture_pair = fall_texture_pair
        self.land_texture_pair = land_texture_pair
        self.roll_textures = roll_texture_pairs

        self.was_on_ground_last_frame = True

        super().__init__(self.idle_texture_pair[0], scale=CHARACTER_SCALING)

    def update_animation(self, delta_time: float = 1 / 60):

        if self.change_x < 0:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0:
            self.character_face_direction = RIGHT_FACING


        if self.change_y > 0:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return

        on_ground = self.change_y == 0
        # Just landed = start landing animation
        if on_ground and not self.was_on_ground_last_frame:
            self.texture = self.land_texture_pair[self.character_face_direction]
            self.land_frame_timer = 0.15  
            self.was_on_ground_last_frame = True
            return
        # If landing timer is active, keep showing landing texture
        if self.land_frame_timer > 0:
            self.land_frame_timer -= delta_time
            self.texture = self.land_texture_pair[self.character_face_direction]
            return

        # Falling
        if self.change_y < 0:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            self.was_on_ground_last_frame = False
            return

        # Idle
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return
        
        self.cur_texture += 1
        if self.cur_texture >= 8 * UPDATES_PER_FRAME:
            self.cur_texture = 0
        frame = self.cur_texture // UPDATES_PER_FRAME
        direction = self.character_face_direction
        self.texture = self.walk_textures[frame][direction]

        if hasattr(self, "is_rolling") and self.is_rolling:
            total_frames = len(self.roll_texture_pairs)
            frame = self.cur_roll_frame // UPDATES_PER_FRAME
            if frame >= total_frames:
                frame = total_frames - 1  # Stay on last frame if rolled too far
            self.texture = self.roll_texture_pairs[frame][self.character_face_direction]
            self.cur_roll_frame += 1
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

        self.is_rolling = False
        self.roll_timer = 0
        self.can_roll = True
        self.roll_cooldown_timer = 0
        self.roll_direction = 0

        arcade.set_background_color(arcade.color.ZINNWALDITE_BROWN)
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


        
        #Player attack animation frames
        self.slash_textures = []
        for i in range(1, 10): 
            path = os.path.join(os.path.dirname(__file__), f"Projectiles/slash{i}.png")
            texture = arcade.load_texture(path)
            self.slash_textures.append(texture)

        self.active_slashes = arcade.SpriteList()


        self.show_collected_popup = False
        self.popup_timer = 0


        background_path = os.path.join(os.path.dirname(__file__), "cave_background.png")
        bg = arcade.Sprite(background_path)
        bg.center_x = WINDOW_WIDTH // 2
        bg.center_y = WINDOW_HEIGHT // 2
        bg.width = WINDOW_WIDTH
        bg.height = WINDOW_HEIGHT
        self.background_list = arcade.SpriteList()
        self.background_list.append(bg)



        
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
            }
        }
        map_path = os.path.join(os.path.dirname(__file__), "stage_1.tmx")
        self.tile_map = arcade.load_tilemap(map_path, scaling=TILE_SCALING, layer_options=layer_options)

        self.scene = arcade.Scene.from_tilemap(self.tile_map)


        self.player_sprite_list = arcade.SpriteList()


        self.player = PlayerCharacter(
            self.idle_texture_pair,
            self.walk_texture_pairs,
            self.jump_texture_pair,
            self.fall_texture_pair,
            self.land_texture_pair,
            self.roll_textures
        )
        self.player.center_x = WINDOW_WIDTH / 2
        self.player.center_y = WINDOW_HEIGHT / 2
        self.player_sprite_list.append(self.player)
        self.scene.add_sprite_list_before("Player", "Foreground")
        self.scene.add_sprite("Player", self.player)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, walls=self.scene["Platforms"], gravity_constant=GRAVITY
        )

        self.camera = arcade.Camera2D(zoom=0.4)
        self.gui_camera = arcade.Camera2D()



    def on_draw(self):
        self.clear()
        self.background_list.draw()
        self.camera.use()


        self.scene.draw()
        self.gui_camera.use()


        if self.show_collected_popup:
            text = f"{item_list[-1]} Collected"
            font_size = 24
            x = WINDOW_WIDTH // 2 - 100 
            y = 40 

            arcade.draw_text(
                text,
                x,
                y,
                arcade.color.WHITE,
                font_size,
                bold=True
            )


    def on_update(self, delta_time):
        self.physics_engine.update()
        self.player_sprite_list.update()
        self.player.update_animation(delta_time)

        if arcade.check_for_collision_with_list(self.player, self.scene["Obstacles"]):
            self.reset_player_position()

        self.camera.position = self.player.position

        if self.show_collected_popup:
            self.popup_timer -= delta_time
            if self.popup_timer <= 0:
                self.show_collected_popup = False

        # Rolling
        self.player.is_rolling = self.is_rolling
        if self.is_rolling:
            self.roll_timer -= delta_time
            roll_speed = 10
            self.player.change_x = self.roll_direction * roll_speed

            if self.roll_timer <= 0:
                self.is_rolling = False
                self.player.is_rolling = False
                self.player.cur_roll_frame = 0  # Reset animation
                self.player.change_x = 0
                self.roll_cooldown_timer = 0
                self.can_roll = False

        if not self.can_roll and not self.is_rolling:
            self.roll_cooldown_timer -= delta_time
            if self.roll_cooldown_timer <= 0:
                self.can_roll = True

        

    def reset_player_position(self):
        self.player.center_x = WINDOW_WIDTH / 2
        self.player.center_y = WINDOW_HEIGHT / 2
        self.player.change_x = 0
        self.player.change_y = 0

    def on_key_press(self, key, modifiers):
        speed_stat = 10
        jump_stat = 20
        dmg_stat = 1
        
        if key == arcade.key.E:
            # Check for chests the player is touching
            chest_hit_list = arcade.check_for_collision_with_list(self.player, self.scene["Chests"])
            for chest in chest_hit_list:
                if gold_stat >= 20:
                    gold_stat -= 20
                    chest.remove_from_sprite_lists()

                    selected_item = random.choice(item_pool)
                    item_list.append(selected_item)
                    print(item_list)

                    if selected_item == "SpeedUp":
                        print("SPEED UP!")
                    elif selected_item == "DmgUp":
                        print("DMG UP!")
                    elif selected_item == "JumpUp":
                        print("JUMP UP!")

                    #Pop up menu 
                    self.show_collected_popup = True
                    self.popup_timer = 5.0  
                elif gold_stat < 20:
                    print("Not enough GOLD!")
                    
                
        # Jump
        elif key in (arcade.key.UP, arcade.key.W, arcade.key.SPACE) and not self.is_rolling:
            if self.physics_engine.can_jump():
                jump_stat = 20
                for item in item_list:
                    if item == "JumpUp":
                        jump_stat +=3
                self.player.change_y = jump_stat
                

        # Move left/right
        elif key in (arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D) and not self.is_rolling:
            for item in item_list:
                if item == "SpeedUp":
                    speed_stat += 3
            if key in (arcade.key.LEFT, arcade.key.A):
                self.player.change_x = -speed_stat
            elif key in (arcade.key.RIGHT, arcade.key.D):
                self.player.change_x = speed_stat


        elif key == arcade.key.LSHIFT and self.can_roll and not self.is_rolling:
            self.is_rolling = True
            self.roll_timer = 0.5

            if self.player.character_face_direction == RIGHT_FACING:
                self.roll_direction = 1
            else:
                self.roll_direction = -1

        # Quit
        elif key in (arcade.key.ESCAPE, arcade.key.Q):
            arcade.close_window()

        #   Melee Attack
        elif key == arcade.key.C:
            for item in item_list:
                if item == "DmgUp":
                    damage_stat += 1

        
        
            


    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A, arcade.key.RIGHT, arcade.key.D, arcade.key.LSHIFT):
            if not self.is_rolling: 
                self.player.change_x = 0


def main():
    window = GameView()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
 