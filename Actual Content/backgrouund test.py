import arcade
import os

WIDTH = 800
HEIGHT = 600
TITLE = "Test Background"

class MyGame(arcade.Window):
    def __init__(self):
        super().__init__(WIDTH, HEIGHT, TITLE)
        self.background = None

    def setup(self):
        path = os.path.join(os.path.dirname(__file__), "cave_background.png")
        if os.path.exists(path):
            self.background = arcade.Sprite(path, scale=1.0)
            self.background.center_x = WIDTH // 2
            self.background.center_y = HEIGHT // 2
        else:
            print("Image missing!")

    def on_draw(self):
        self.clear()
        if self.background:
            self.background.draw()

def main():
    window = MyGame()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()