import re

MATH_PATTERN = re.compile(r'(\d+[\.,]?\d*)\s*(mal|plus|minus|durch|\*|\+|\-|/)\s*(\d+[\.,]?\d*)', re.IGNORECASE)

def try_direct_calculation(text):
    match = MATH_PATTERN.search(text)
    if not match:
        return None
    a, op, b = match.groups()
    a = float(a.replace(',', '.'))
    b = float(b.replace(',', '.'))
    
    op_map = {
        'mal': lambda x, y: x * y, '*': lambda x, y: x * y,
        'plus': lambda x, y: x + y, '+': lambda x, y: x + y,
        'minus': lambda x, y: x - y, '-': lambda x, y: x - y,
        'durch': lambda x, y: x / y, '/': lambda x, y: x / y
    }
    try:
        res = op_map[op.lower()](a, b)
        return int(res) if res.is_integer() else res
    except ZeroDivisionError:
        return 'Fehler: Division durch Null!'
