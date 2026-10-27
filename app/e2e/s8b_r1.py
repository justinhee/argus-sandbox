import ast


def calculate(expression: str) -> float:
    return float(ast.literal_eval(expression))
