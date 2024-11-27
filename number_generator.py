import random

class NumberGenerator:
    def __init__(self):
        self.used_numbers = set()

    def generate_number(self):
        while True:
            new_number = ''.join([str(random.randint(0, 9)) for _ in range(9)])
            if new_number not in self.used_numbers:
                self.used_numbers.add(new_number)
                return new_number

    def reset(self):
        self.used_numbers.clear()

