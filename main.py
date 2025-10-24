from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os

# Import your full HyperCalc code here (copy-paste everything before "if __name__ == '__main__':")
# For brevity, only the minimal SafeEvaluator is shown here.
import math, cmath
import ast
from decimal import Decimal, getcontext
getcontext().prec = 50

_ALLOWED_FUNCS = {
    'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan, 'atan2': math.atan2,
    'sinh': math.sinh, 'cosh': math.cosh, 'tanh': math.tanh,
    'log': math.log, 'log10': math.log10, 'exp': math.exp, 'sqrt': math.sqrt,
    'floor': math.floor, 'ceil': math.ceil, 'fabs': math.fabs, 'gamma': math.gamma,
    'deg': math.degrees, 'rad': math.radians, 'abs': abs, 'round': round,
    'csin': cmath.sin, 'ccos': cmath.cos, 'ctan': cmath.tan,
    'clog': cmath.log, 'cexp': cmath.exp, 'csqrt': cmath.sqrt,
    'phase': cmath.phase, 'polar': cmath.polar,
}
_ALLOWED_CONSTS = {
    'pi': math.pi, 'tau': math.tau, 'e': math.e, 'j': 1j,
    'inf': float('inf'), 'nan': float('nan')
}

class SafeEvaluator(ast.NodeVisitor):
    def __init__(self, variables=None):
        self.vars = dict(_ALLOWED_CONSTS)
        if variables:
            self.vars.update(variables)
    def eval(self, expr: str):
        node = ast.parse(expr, mode='eval')
        return self.visit(node.body)
    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add):   return left + right
        if isinstance(op, ast.Sub):   return left - right
        if isinstance(op, ast.Mult):  return left * right
        if isinstance(op, ast.Div):   return left / right
        if isinstance(op, ast.Pow):   return left ** right
        raise ValueError("Unsupported binary operator")
    def visit_Name(self, node):
        if node.id in self.vars:
            return self.vars[node.id]
        raise ValueError(f"Unknown name: {node.id}")
    def visit_Num(self, node): return node.n
    def visit_Constant(self, node): return node.value
    def visit_Call(self, node):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls allowed")
        fname = node.func.id
        if fname in _ALLOWED_FUNCS:
            func = _ALLOWED_FUNCS[fname]
            args = [self.visit(a) for a in node.args]
            kwargs = {kw.arg: self.visit(kw.value) for kw in node.keywords}
            return func(*args, **kwargs)
        raise ValueError(f"Function '{fname}' not allowed")
    def generic_visit(self, node):
        raise ValueError(f"Unsupported syntax: {type(node).__name__}")

class EvalRequest(BaseModel):
    expr: str

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.post("/api/eval")
async def eval_expr(req: EvalRequest):
    try:
        se = SafeEvaluator()
        result = se.eval(req.expr)
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}

# (Optional) health check endpoint
@app.get("/api/ping")
def ping():
    return {"ok": True}