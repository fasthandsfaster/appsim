import random
from datetime import datetime

class Interpreter:
    def __init__(self, logger):
        self.logger = logger
        # Seed the random number generator once during initialization
        random.seed(str(datetime.now()))

    def handle_interpreter_parameter(self, exer_name, parameter):
        match exer_name:
            case "Horseshoe" | "Horseshoe2":
                if parameter == "timestamp":
                    return datetime.now()
                elif parameter == "path":
                    return random.choice(["TP_B_TO_A", "TP_A_TO_B"])
                else:
                    self.logger.debug(f'Exercise: {exer_name} parameter {parameter} unhandled:')
                    return None
            case _:
                self.logger.debug(f'Exercise: {exer_name} interpreter parameter handling undefined:')
                return None

# Example usage
if __name__ == "__main__":
    import logging
    logger = logging.getLogger()
    interpreter = Interpreter(logger)

    # Test the randomness
    for _ in range(10):
        print(interpreter.handle_interpreter_parameter("Horseshoe", "path"))