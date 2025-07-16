import arcade
import os

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Arcade 3.x Background"

class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
        self.background_list = arcade.SpriteList()

    def setup(self):
        background_path = os.path.join(os.path.dirname(__file__), "cave_background.png")
        bg = arcade.Sprite(background_path)
        bg.center_x = WINDOW_WIDTH // 2
        bg.center_y = WINDOW_HEIGHT // 2
        bg.width = WINDOW_WIDTH
        bg.height = WINDOW_HEIGHT
        self.background_list.append(bg)

    def on_draw(self):
        self.clear()
        self.background_list.draw()

def main():
    game = MyGame()
    game.setup()
    arcade.run()

if __name__ == "__main__":
    main()
