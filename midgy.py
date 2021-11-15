from string_with_arrows import *
import string

################################################
# Constants
################################################

DIGITS = "0123456789"
LETTERS = string.ascii_letters
LETTERS_DIGITS = LETTERS + DIGITS

################################################
# Errors
################################################

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.start = pos_start
        self.end = pos_end
        self.error_name = error_name
        self.details = details

    def __str__(self):
        result = f"{self.error_name}: {self.details}\n"
        result += f" -> File {self.start.file}, line {self.start.line + 1}"
        result += '\n\n' + string_with_arrows(self.start.ftext, self.start, self.end)
        return result


class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end,'Illegal Character', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end,'Invalid Syntax', details)

class RTError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end,'Runtime Error', details)
        self.context = context 

    def __str__(self):
        result = self.generate_traceback()
        result += f"{self.error_name}: {self.details}"
        result += '\n\n' + string_with_arrows(self.start.ftext, self.start, self.end)
        return result

    def generate_traceback(self):
        result = ''
        pos = self.start
        ctx = self.context
        while ctx:
            result = f" File {pos.file}, Line {str(pos.line)}, in {ctx.display_name}\n" + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return "Traceback (most recent call last):\n" + result

################################################
# Position
################################################

class Position:
    def __init__(self, idx, line, col, file, ftext ):
        self.idx = idx
        self.line = line
        self.col = col
        self.file = file
        self.ftext = ftext

    def advance(self, current_char=None):
        self.idx += 1
        self.col += 1

        if current_char == ' \n':
            self.line += 1
            self.col = 0
        return self

    def copy(self):
        return Position(self.idx, self.line, self.col, self.file, self.ftext)

################################################
# Tokens
################################################

TT_INT        = "INT"
TT_FLOAT      = "FLOAT"
TT_IDENTIFIER = "IDENTIFIER"
TT_KEYWORD    = "KEYWORD"
TT_EQ         = "EQ"
TT_PLUS       = "PLUS"
TT_MINUS      = "MINUS"
TT_MUL        = "MUL"
TT_DIV        = "DIV"
TT_LPAREN     = "LPAREN"
TT_RPAREN     = "RPAREN"
TT_POW        = "POW"
TT_EOF        = "EOF"

KEYWORDS = [
    "set",
]

class Token: 
    def __init__(self,type_, value=None, start=None, end=None):
        
        self.type = type_
        self.value = value

        if start: 
            self.start = start.copy()
            self.end = start.copy()
            self.end.advance()

        if end: self.end = end.copy()

    def __repr__(self):
        if self.value: return f"{self.type}:{self.value}"
        return f"{self.type}"

    def matches(self, type_, value):
        return self.type == type_ and self.value == value

####################################################
# Lexer
####################################################

class Lexer:
    def __init__(self,file, text):
        self.file = file
        self.text = text
        self.pos = Position(-1, 0, -1, file, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char in LETTERS:
                tokens.append(self.make_identifier())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, start=self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, start=self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TT_POW, start=self.pos))
                self.advance()
            elif self.current_char == '=':
                tokens.append(Token(TT_EQ, start=self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(TT_EOF, start=self.pos))
        return tokens, None
    
    def make_number(self):
        num_str = ''
        dot_count = 0  
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0: 
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    def make_identifier(self):
        id_str = ''
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()

        tok_type = TT_KEYWORD if id_str in KEYWORDS else TT_IDENTIFIER
        return Token(tok_type, id_str, pos_start, self.pos)



################################################
# NODES  
################################################

class NumberNode:
    def __init__(self, tok):
        self.tok = tok
        self.start = self.tok.start
        self.end = self.tok.end

    def __repr__(self):
        return f"{self.tok}"

class VarAccessNode:
    def __init__(self, var_name_tok):
        self.var_name_tok = var_name_tok

        self.start = self.var_name_tok.start
        self.end = self.var_name_tok.end

class VarAssignNode:
    def __init__(self,var_name_tok, value_node):
        self.var_name_tok = var_name_tok
        self.value_node = value_node

        self.start = self.var_name_tok.start
        self.end = self.value_node.end


class BinOpNode:
    def __init__(self, left, op_tok, right):
        self.left = left
        self.op_tok = op_tok
        self.right = right

        self.start = self.left.start 
        self.end = self.right.end

    def __repr__(self):
        return f"({self.left}, {self.op_tok}, {self.right})"

class UnaryOpNode:
    def __init__(self, op_tok, node):

        self.op_tok = op_tok
        self.node = node

        self.start = self.op_tok.start
        self.end = node.end

    def __repr__(self):
        return f"({self.op_tok}, {self.node})"

################################################
# Parse Result
################################################

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.adv_count = 0

    def register_adv(self):
        self.adv_count += 1

    def register(self, res):
        self.adv_count += res.adv_count
        if res.error: self.error = res.error
        return res.node



    def success(self, node):
        self.node = node
        return self
        

    def failure(self, error):
        if not self.error or self.adv_count == 0:
            self.error = error
        return self
################################################
# Parser  
################################################

class Parser:
    def __init__(self,tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(self.current_tok.start, self.current_tok.end, "Expected '+', '-', '*' or '/' "))
        return res


    def atom(self):
        res = ParseResult()
        tok = self.current_tok


        if tok.type in (TT_INT, TT_FLOAT):
            res.register_adv()
            self.advance()
            return res.success(NumberNode(tok))

        elif tok.type == TT_IDENTIFIER:
            res.register_adv()
            self.advance()
            return res.success(VarAccessNode(tok))

        elif tok.type == TT_LPAREN:
            res.register_adv()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type == TT_RPAREN:
                res.register_adv()
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(tok.start, tok.end, "Expected ')', got " + tok.value))

        return res.failure(InvalidSyntaxError(
            tok.start, tok.end,
            "Expected 'int', 'float', identifier, '+', '-', or '(', got " + str(tok.value)
        ))

    def power(self):
        return self.bin_op(self.atom, (TT_POW, ), self.factor)

    def factor(self):
        res = ParseResult()
        tok = self.current_tok
        
        if tok.type in (TT_PLUS, TT_MINUS):
            res.register_adv()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(tok, factor))

        return self.power()
    

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def expr(self):
        res = ParseResult()

        if self.current_tok.matches(TT_KEYWORD, 'set'):
            res.register_adv()
            self.advance()
            if self.current_tok.type != TT_IDENTIFIER:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start, self.current_tok.end,
                    "Expected identifier"
                ))
            var_name = self.current_tok
            res.register_adv()
            self.advance()
            if self.current_tok.type != TT_EQ:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.start, self.current_tok.end,
                    "Expected '='"
                ))
            res.register_adv()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            return res.success(VarAssignNode(var_name, expr))
        node = res.register(self.bin_op(self.term, (TT_PLUS, TT_MINUS)))

        if res.error: 
            return res.failure(InvalidSyntaxError(
            self.current_tok.start, self.current_tok.end,
            "Expected 'int', 'float', identifier,'set' '+', '-', or '(', got " + str(self.current_tok.value)
        ))
        else: return res.success(node)


    def bin_op(self, func_a, ops, func_b=None):
        if func_b == None: 
            func_b = func_a

        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res

        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.register_adv()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = BinOpNode(left, op_tok, right)
        
        return res.success(left)

################################################
# Runtime Result
################################################

class RTResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, res):
        if res.error: self.error = res.error
        return res.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self
################################################
# Values
################################################

class Number:
    def __init__(self, value):
        self.value = value
        self.set_pos()
        self.set_context()

    def set_context(self, ctx=None):
        self.context = ctx
        return self

    def set_pos(self, pos_start=None, pos_end=None):
        self.start = pos_start
        self.end = pos_end
        return self

    def add(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None

    def subtract(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None

    def multiply(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None

    def divide(self, other):
        if other.value == 0:
            return None, RTError(
                other.start, other.end, "You cannot divide by zero",
                self.context
            )
        if isinstance(other, Number):
            return Number(self.value / other.value).set_context(self.context), None

    def power(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.start, self.end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return str(self.value)


################################################
# Context
################################################

class Context:
    def __init__(self, display_name, parent=None, parent_entry_pos=None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos
        self.symbol_table = None

################################################
# Symbol Table
################################################

class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.parent = None

    def get(self, name):
        value = self.symbols.get(name, None)
        if value == None and self.parent:
            return self.parent.get(name)
        return value

    def set(self, name, value):
        self.symbols[name] = value

    def remove(self, name):
        del self.symbols[name]


################################################
# Interpreter
################################################

class Interpreter:

    def visit(self, node, ctx):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, ctx)

    def no_visit_method(self, node, ctx):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    # visit BinOpNode Method 
    def visit_BinOpNode(self, node, ctx):
        res = RTResult()

        left = res.register(self.visit(node.left, ctx))
        if res.error: return res
        right = res.register(self.visit(node.right, ctx))
        if res.error: return res

        

        if node.op_tok.type == TT_PLUS:
            result, error = left.add(right)
        elif node.op_tok.type == TT_MINUS:
            result, error = left.subtract(right)
        elif node.op_tok.type == TT_MUL:
            result, error = left.multiply(right)
        elif node.op_tok.type == TT_DIV:
            result, error = left.divide(right)
        elif node.op_tok.type == TT_POW:
            result, error = left.power(right) 
        
        if error: 
            return res.failure(error)
        else: 
            return res.success(result.set_pos(node.start, node.end))



    # visit UnaryOpNode Method
    def visit_UnaryOpNode(self, node, ctx):
        res = RTResult()
        
        number = res.register(self.visit(node.node, ctx))
        if res.error: return res

        error = None

        if node.op_tok.type == TT_MINUS:
            number, error = number.multiply(Number(-1))

        if error:
            return res.failure(error)
        else: 
            return res.success(number.set_pos(node.start, node.end))



    # visit NumberNode Method
    def visit_NumberNode(self, node, ctx):
        return RTResult().success( 
            Number(node.tok.value).set_context(ctx).set_pos(node.start, node.end)
        )

    def visit_VarAccessNode(self, node, ctx):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = ctx.symbol_table.get(var_name)

        if not value:
            return res.failure(RTError(
                node.start, node.end,
                f"{var_name} is not defined", ctx
            ))
        value = value.copy().set_pos(node.start, node.end)
        return res.success(value)

    def visit_VarAssignNode(self, node, ctx):
        res = RTResult()
        var_name = node.var_name_tok.value
        value = res.register(self.visit(node.value_node, ctx))
        if res.error: return res
        ctx.symbol_table.set(var_name, value)
        return res.success(value)




################################################
# RUN  
################################################

gst = SymbolTable()
gst.set("null", Number(0))
def run(file, text):
    lexer = Lexer(file, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error
    # Generate AST -> Abstract Syntax Tree
    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    # Run program
    interpreter = Interpreter()
    ctx = Context('<program>')
    ctx.symbol_table = gst
    result = interpreter.visit(ast.node, ctx)

    return result.value, result.error