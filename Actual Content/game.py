import arcade
import os
import random

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "TITLE"

TILE_SCALING = 1
PLAYER_JUMP_SPEED = 20
GRAVITY = 1

speed_stat = 10
UPDATES_PER_FRAME = 7

RIGHT_FACING = 0
LEFT_FACING = 1

CHARACTER_SCALING = 1

#All available
item_pool = ["SpeedUp", "Nothing!"]
#Collected items
item_list = []

class PlayerCharacter(arcade.Sprite):
    def __init__(self, idle_texture_pair, walk_texture_pairs, jump_texture_pair, fall_texture_pair, land_texture_pair):
        self.character_face_direction = RIGHT_FACING
        self.cur_texture = 0
        self.was_on_ground_last_frame = True
        self.land_frame_timer = 0

        self.idle_texture_pair = idle_texture_pair
        self.walk_textures = walk_texture_pairs
        self.jump_texture_pair = jump_texture_pair
        self.fall_texture_pair = fall_texture_pair
        self.land_texture_pair = land_texture_pair
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
            self.land_frame_timer = 0.15  # seconds to hold landing frame
            self.was_on_ground_last_frame = True
            return

        # If landing timer is active, keep showing fall2
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

        arcade.set_background_color(arcade.color.ZINNWALDITE_BROWN)
        #Setting up all player sprite frames

        character = os.path.join(os.path.dirname(__file__), "Characters/Player/knight")

        idle = arcade.load_texture(f"{character}_idle.png")
        self.idle_texture_pair = idle, idle.flip_left_right()

        self.walk_texture_pairs = []
        for i in range(1,11):
            texture = arcade.load_texture(f"{character}{i}.png")
            self.walk_texture_pairs.append((texture, texture.flip_left_right()))

        jump = arcade.load_texture(f"{character}_jump.png")
        self.jump_texture_pair = jump, jump.flip_left_right()

        fall = arcade.load_texture(f"{character}_fall.png")
        land = arcade.load_texture(f"{character}_land.png")
        self.fall_texture_pair = (fall, fall.flip_left_right())
        self.land_texture_pair = (land, land.flip_left_right())
        
        #Player attack animation frames
        self.slash_textures = []
        for i in range(1, 10): 
            path = os.path.join(os.path.dirname(__file__), f"Projectiles/slash{i}.png")
            tex = arcade.load_texture(path)
            self.slash_textures.append(tex)

        self.active_slashes = arcade.SpriteList()


        self.show_popup = False
        self.popup_timer = 0



        
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
            self.land_texture_pair
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
        self.camera.use()

        self.scene.draw()
        self.gui_camera.use()


        if self.show_popup:
            text = "Chest Collected"
            font_size = 24

            # Estimate width manually or place it near center
            x = WINDOW_WIDTH // 2 - 100  # Adjust as needed
            y = 40  # Bottom of the screen

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

        if self.show_popup:
            self.popup_timer -= delta_time
            if self.popup_timer <= 0:
                self.show_popup = False

    def reset_player_position(self):
        self.player.center_x = WINDOW_WIDTH / 2
        self.player.center_y = WINDOW_HEIGHT / 2
        self.player.change_x = 0
        self.player.change_y = 0

    def on_key_press(self, key, modifiers):
        speed_stat = 5
        if key == arcade.key.E:
            # Check for chests the player is touching
            chest_hit_list = arcade.check_for_collision_with_list(self.player, self.scene["Chests"])
            for chest in chest_hit_list:
                chest.remove_from_sprite_lists()

                selected_item = random.choice(item_pool)
                item_list.append(selected_item)
                print(item_list)

                #Pop up menu 
                self.show_popup = True
                self.popup_timer = 5.0  
                
        # Jump
        elif key in (arcade.key.UP, arcade.key.W, arcade.key.SPACE):
            if self.physics_engine.can_jump():
                self.player.change_y = PLAYER_JUMP_SPEED
                

        # Move left/right
        elif key in (arcade.key.LEFT, arcade.key.A) or key in (arcade.key.RIGHT, arcade.key.D):

            for item in item_list:
                if item == "SpeedUp":
                    speed_stat +=3

            if key in (arcade.key.LEFT, arcade.key.A):
                self.player.change_x = -speed_stat

            elif key in (arcade.key.RIGHT, arcade.key.D):
                self.player.change_x = speed_stat

        # Quit
        elif key in (arcade.key.ESCAPE, arcade.key.Q):
            arcade.close_window()

        #   Melee Attack
        elif key == arcade.key.C:
            print("ow")


    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.D):
            self.player.change_x = 0


def main():
    window = GameView()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
 