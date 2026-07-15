package com.snake;

import java.util.List;

public class Board {
    private final int width;
    private final int height;

    public Board(int width, int height) {
        this.width = width;
        this.height = height;
    }

    public String render(Snake snake, Food food, int score) {
        StringBuilder sb = new StringBuilder();

        // Move cursor to top-left
        sb.append("\033[H");

        // Top border
        sb.append("┌");
        sb.append("──".repeat(width));
        sb.append("┐\n");

        for (int y = 0; y < height; y++) {
            sb.append("│");
            for (int x = 0; x < width; x++) {
                if (isHead(snake, x, y)) {
                    sb.append("\033[32m██\033[0m"); // green head
                } else if (isBody(snake, x, y)) {
                    sb.append("\033[92m██\033[0m"); // light green body
                } else if (food.getX() == x && food.getY() == y) {
                    sb.append("\033[31m██\033[0m"); // red food
                } else {
                    sb.append("  ");
                }
            }
            sb.append("│\n");
        }

        // Bottom border
        sb.append("└");
        sb.append("──".repeat(width));
        sb.append("┘\n");

        sb.append(" Score: ").append(score).append("  |  WASD to move  |  Q to quit\n");

        return sb.toString();
    }

    private boolean isHead(Snake snake, int x, int y) {
        int[] head = snake.getHead();
        return head[0] == x && head[1] == y;
    }

    private boolean isBody(Snake snake, int x, int y) {
        List<int[]> body = snake.getBody();
        for (int i = 1; i < body.size(); i++) {
            if (body.get(i)[0] == x && body.get(i)[1] == y) {
                return true;
            }
        }
        return false;
    }

    public int getWidth() { return width; }
    public int getHeight() { return height; }
}
