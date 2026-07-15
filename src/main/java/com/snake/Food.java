package com.snake;

import java.util.List;
import java.util.Random;

public class Food {
    private int x;
    private int y;
    private final Random random = new Random();

    public Food(int boardWidth, int boardHeight, List<int[]> snakeBody) {
        respawn(boardWidth, boardHeight, snakeBody);
    }

    public void respawn(int boardWidth, int boardHeight, List<int[]> snakeBody) {
        do {
            x = random.nextInt(boardWidth);
            y = random.nextInt(boardHeight);
        } while (isOnSnake(snakeBody));
    }

    private boolean isOnSnake(List<int[]> snakeBody) {
        for (int[] segment : snakeBody) {
            if (segment[0] == x && segment[1] == y) {
                return true;
            }
        }
        return false;
    }

    public int getX() { return x; }
    public int getY() { return y; }
}
