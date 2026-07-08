import re
import ast
import operator
import json

def safe_eval(expr):
    """Sichere Auswertung von Mathe-Strings ohne kritisches eval()"""
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg
    }
    try:
        node = ast.parse(expr, mode='eval')
        def _eval(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            elif isinstance(node, ast.BinOp):
                return allowed_operators[type(node.op)](_eval(node.left), _eval(node.right))
            elif isinstance(node, ast.UnaryOp):
                return allowed_operators[type(node.op)](_eval(node.operand))
            else:
                raise ValueError("Unsupported operation")
        return _eval(node.body)
    except Exception:
        return None

def try_direct_calculation(text):
    """Regex Fast-Path für einfache Aufgaben direkt aus dem Voice-Loop"""
    text = text.lower().replace("mal", "*").replace("plus", "+").replace("minus", "-").replace("geteilt durch", "/").replace(":", "/")
    match = re.search(r'(\d+(?:\.\d+)?)\s*([\+\-\*\/])\s*(\d+(?:\.\d+)?)', text)
    if match:
        expr = f"{match.group(1)} {match.group(2)} {match.group(3)}"
        res = safe_eval(expr)
        return res if res is not None else None
    return None

def get_ollama_tools():
    """Definiert das JSON-Schema für Ollamas natives Tool-Calling"""
    return [{
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Führt mathematische Berechnungen aus. Nutze dies IMMER für Mathe-Fragen statt das Ergebnis zu raten.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Der mathematische Ausdruck (z.B. '2 + 2' oder '15 * 23')"
                    }
                },
                "required": ["expression"]
            }
        }
    }]

def execute_tool(name, arguments_json):
    """Führt das Tool aus, wenn Ollama es anfordert"""
    if name == "calculate":
        try:
            args = arguments_json if isinstance(arguments_json, dict) else json.loads(arguments_json)
            expr = args.get("expression", "")
            res = safe_eval(expr)
            return str(res) if res is not None else "Fehler: Ungültiger mathematischer Ausdruck."
        except Exception as e:
            return f"Fehler bei Tool-Ausführung: {str(e)}"
    return "Fehler: Unbekanntes Tool."

if __name__ == "__main__":
    # Schneller Selbsttest
    print("Test Fast-Path:", try_direct_calculation("was ist 15 mal 23"))
    print("Test Safe-Eval:", safe_eval("15 * 23"))
