class Trig:
    def __init__(self, velocity=127, length=1):
        self.velocity = velocity
        self.length = length

    def __str__(self):
        return 'Trig(velocity={}, length={})'.format(self.velocity, self.length)

