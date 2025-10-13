class Position:

    def __init__(self, x: int, y: int):

        self.X = x
        self.Y = y

    def __iter__(self):

        yield self.X
        yield self.Y


class Size:

    def __init__(self, width: int, height: int):

        self.WIDTH = width
        self.HEIGHT = height

    def __iter__(self):

        yield self.WIDTH
        yield self.HEIGHT


class Geometry:

    def __init__(self, x: int, y: int, width: int, height: int):

        self.X = x
        self.Y = y
        self.WIDTH = width
        self.HEIGHT = height

    def __iter__(self):

        yield self.X
        yield self.Y
        yield self.WIDTH
        yield self.HEIGHT


class WidgetGeometry:

    def __init__(self, x: int, y: int, width: int, height: int):

        self.POSITION = Position(x, y)
        self.SIZE = Size(width, height)
        self.GEOMETRY = Geometry(x, y, width, height)
