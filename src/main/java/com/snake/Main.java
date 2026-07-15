package com.snake;

import java.io.IOException;

public class Main {
    private static final int WIDTH = 20;
    private static final int HEIGHT = 15;
    private static final int TICK_MS = 150;

    private static volatile Direction inputDirection = Direction.RIGHT;
    private static volatile boolean running = true;

    public static void main(String[] args) throws Exception {
        enableRawMode();
        Runtime.getRuntime().addShutdownHook(new Thread(Main::disableRawMode));

        Snake snake = new Snake(WIDTH / 2, HEIGHT / 2);
        Food food = new Food(WIDTH, HEIGHT, snake.getBody());
        Board board = new Board(WIDTH, HEIGHT);
        int score = 0;

        // Input thread
        Thread inputThread = new Thread(() -> {
            try {
                while (running) {
                    int ch = System.in.read();
                    switch (ch) {
                        case 'w', 'W' -> inputDirection = Direction.UP;
                        case 's', 'S' -> inputDirection = Direction.DOWN;
                        case 'a', 'A' -> inputDirection = Direction.LEFT;
                        case 'd', 'D' -> inputDirection = Direction.RIGHT;
                        case 'q', 'Q' -> running = false;
                    }
                }
            } catch (IOException e) {
                running = false;
            }
        });
        inputThread.setDaemon(true);
        inputThread.start();

        // Clear screen
        System.out.print("\033[2J");
        System.out.flush();

        // Game loop
        while (running) {
            snake.setDirection(inputDirection);
            snake.move(false);

            // Check food
            int[] head = snake.getHead();
            if (head[0] == food.getX() && head[1] == food.getY()) {
                // Grow: add extra segment by moving again with grow=true undone
                // Simpler: just add a segment at the tail position
                snake.getBody().addLast(new int[]{-1, -1}); // will be overwritten next tick
                score += 10;
                food.respawn(WIDTH, HEIGHT, snake.getBody());
            }

            // Check collisions
            if (snake.collidesWithWall(WIDTH, HEIGHT) || snake.collidesWithSelf()) {
                break;
            }

            // Render
            System.out.print(board.render(snake, food, score));
            System.out.flush();

            Thread.sleep(TICK_MS);
        }

        // Game over
        disableRawMode();
        System.out.println("\n  GAME OVER! Final score: " + score);
    }

    private static void enableRawMode() {
        try {
            new ProcessBuilder("stty", "-icanon", "-echo", "min", "1")
                .inheritIO().start().waitFor();
        } catch (Exception e) {
            System.err.println("Warning: could not set raw terminal mode");
        }
    }

    private static void disableRawMode() {
        try {
            new ProcessBuilder("stty", "sane")
                .inheritIO().start().waitFor();
        } catch (Exception ignored) {}
    }
}
