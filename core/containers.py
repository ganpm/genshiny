class Position:

    def __init__(self, x: int, y: int):

        self.X = x
        self.Y = y

    def __iter__(self):

        yield self.X
        yield self.Y


class Size:

    def __init__(self, w: int, h: int):

        self.WIDTH = w
        self.HEIGHT = h

    def __iter__(self):

        yield self.WIDTH
        yield self.HEIGHT


class Geometry:

    def __init__(self, x: int, y: int, w: int, h: int):

        self.X = x
        self.Y = y
        self.WIDTH = w
        self.HEIGHT = h

    def __iter__(self):

        yield self.X
        yield self.Y
        yield self.WIDTH
        yield self.HEIGHT


class Box:

    def __init__(self, x: int = 0, y: int = 0, w: int = 0, h: int = 0):

        self.POSITION = Position(x, y)
        self.SIZE = Size(w, h)
        self.GEOMETRY = Geometry(x, y, w, h)
