package com.snake;

import com.googlecode.lanterna.input.KeyStroke;
import com.googlecode.lanterna.input.KeyType;
import com.googlecode.lanterna.terminal.DefaultTerminalFactory;
import com.googlecode.lanterna.screen.Screen;
import com.googlecode.lanterna.screen.TerminalScreen;
import com.googlecode.lanterna.terminal.Terminal;
import com.googlecode.lanterna.TextColor;
import com.googlecode.lanterna.TextCharacter;

public class Main {
    private static final int WIDTH = 20;
    private static final int HEIGHT = 15;
    private static final int TICK_MS = 150;

    public static void main(String[] args) throws Exception {
        Terminal terminal = new DefaultTerminalFactory().createTerminal();
        Screen screen = new TerminalScreen(terminal);
        screen.startScreen();
        screen.setCursorPosition(null); // hide cursor

        Snake snake = new Snake(WIDTH / 2, HEIGHT / 2);
        Food food = new Food(WIDTH, HEIGHT, snake.getBody());
        int score = 0;
        boolean grow = false;
        Direction inputDirection = Direction.RIGHT;

        while (true) {
            // Poll input (non-blocking)
            KeyStroke key = screen.pollInput();
            if (key != null) {
                if (key.getKeyType() == KeyType.Escape ||
                    (key.getKeyType() == KeyType.Character && (key.getCharacter() == 'q' || key.getCharacter() == 'Q'))) {
                    break;
                }
                switch (key.getKeyType()) {
                    case ArrowUp -> inputDirection = Direction.UP;
                    case ArrowDown -> inputDirection = Direction.DOWN;
                    case ArrowLeft -> inputDirection = Direction.LEFT;
                    case ArrowRight -> inputDirection = Direction.RIGHT;
                    default -> {}
                }
            }

            snake.setDirection(inputDirection);
            snake.move(grow);
            grow = false;

            // Check collisions
            if (snake.collidesWithWall(WIDTH, HEIGHT) || snake.collidesWithSelf()) {
                break;
            }

            // Check food
            int[] head = snake.getHead();
            if (head[0] == food.getX() && head[1] == food.getY()) {
                grow = true;
                score += 10;
                food.respawn(WIDTH, HEIGHT, snake.getBody());
            }

            // Draw
            screen.clear();
            drawBoard(screen, snake, food, score);
            screen.refresh();

            Thread.sleep(TICK_MS);
        }

        // Game over screen
        screen.clear();
        String msg = "GAME OVER! Score: " + score + "  (Press any key)";
        for (int i = 0; i < msg.length(); i++) {
            screen.setCharacter(i + 2, HEIGHT / 2 + 1, new TextCharacter(msg.charAt(i),
                TextColor.ANSI.WHITE, TextColor.ANSI.BLACK));
        }
        screen.refresh();
        screen.readInput(); // wait for keypress

        screen.stopScreen();
        terminal.close();
    }

    private static void drawBoard(Screen screen, Snake snake, Food food, int score) {
        // Offsets for centering
        int ox = 1;
        int oy = 1;

        // Top border
        screen.setCharacter(ox, oy, tc('┌'));
        for (int x = 1; x <= WIDTH * 2; x++) {
            screen.setCharacter(ox + x, oy, tc('─'));
        }
        screen.setCharacter(ox + WIDTH * 2 + 1, oy, tc('┐'));

        // Rows
        for (int y = 0; y < HEIGHT; y++) {
            screen.setCharacter(ox, oy + 1 + y, tc('│'));
            for (int x = 0; x < WIDTH; x++) {
                char c1 = ' ', c2 = ' ';
                TextColor fg = TextColor.ANSI.WHITE;
                TextColor bg = TextColor.ANSI.BLACK;

                if (isHead(snake, x, y)) {
                    c1 = '█'; c2 = '█';
                    fg = TextColor.ANSI.GREEN;
                } else if (isBody(snake, x, y)) {
                    c1 = '█'; c2 = '█';
                    fg = TextColor.ANSI.GREEN_BRIGHT;
                } else if (food.getX() == x && food.getY() == y) {
                    c1 = '█'; c2 = '█';
                    fg = TextColor.ANSI.RED;
                }

                screen.setCharacter(ox + 1 + x * 2, oy + 1 + y, new TextCharacter(c1, fg, bg));
                screen.setCharacter(ox + 2 + x * 2, oy + 1 + y, new TextCharacter(c2, fg, bg));
            }
            screen.setCharacter(ox + WIDTH * 2 + 1, oy + 1 + y, tc('│'));
        }

        // Bottom border
        screen.setCharacter(ox, oy + HEIGHT + 1, tc('└'));
        for (int x = 1; x <= WIDTH * 2; x++) {
            screen.setCharacter(ox + x, oy + HEIGHT + 1, tc('─'));
        }
        screen.setCharacter(ox + WIDTH * 2 + 1, oy + HEIGHT + 1, tc('┘'));

        // Score line
        String info = " Score: " + score + "  |  Arrows: move  |  Q: quit";
        for (int i = 0; i < info.length(); i++) {
            screen.setCharacter(ox + i, oy + HEIGHT + 2, tc(info.charAt(i)));
        }
    }

    private static TextCharacter tc(char c) {
        return new TextCharacter(c, TextColor.ANSI.WHITE, TextColor.ANSI.BLACK);
    }

    private static boolean isHead(Snake snake, int x, int y) {
        int[] head = snake.getHead();
        return head[0] == x && head[1] == y;
    }

    private static boolean isBody(Snake snake, int x, int y) {
        var body = snake.getBody();
        for (int i = 1; i < body.size(); i++) {
            if (body.get(i)[0] == x && body.get(i)[1] == y) return true;
        }
        return false;
    }
}
