package com.snake;

import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;

public class Snake {
    private final LinkedList<int[]> body = new LinkedList<>();
    private Direction direction = Direction.RIGHT;

    public Snake(int startX, int startY) {
        body.add(new int[]{startX, startY});
        body.add(new int[]{startX - 1, startY});
        body.add(new int[]{startX - 2, startY});
    }

    public void setDirection(Direction newDir) {
        if (!direction.isOpposite(newDir)) {
            direction = newDir;
        }
    }

    public void move(boolean grow) {
        int[] head = body.getFirst();
        int newX = head[0];
        int newY = head[1];

        switch (direction) {
            case UP -> newY--;
            case DOWN -> newY++;
            case LEFT -> newX--;
            case RIGHT -> newX++;
        }

        body.addFirst(new int[]{newX, newY});
        if (!grow) {
            body.removeLast();
        }
    }

    public boolean collidesWithSelf() {
        int[] head = body.getFirst();
        for (int i = 1; i < body.size(); i++) {
            if (body.get(i)[0] == head[0] && body.get(i)[1] == head[1]) {
                return true;
            }
        }
        return false;
    }

    public boolean collidesWithWall(int width, int height) {
        int[] head = body.getFirst();
        return head[0] < 0 || head[0] >= width || head[1] < 0 || head[1] >= height;
    }

    public int[] getHead() { return body.getFirst(); }
    public List<int[]> getBody() { return body; }
    public Direction getDirection() { return direction; }
}
