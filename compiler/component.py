from compiler.tool import CompilerError, CodeError, PRINT_INDENT
import pprint
import copy
import functools

TEMP_REG_0 = 'r10'
TEMP_REG_1 = 'r11'
TEMP_REG_2 = 'r12'
TEMP_REG_3 = 'r13'
TEMP_REG_4 = 'r14'
TEMP_REG_5 = 'r15'


class NoObject:
    print_on = True

    def __init__(self, compiler = None):
        self.compiler = compiler

    def __repr__(self):
        return f'NoObject'

    def __bool__(self):
        return False

    def print_me(self, indent = 0):
        if self.print_on:
            print(f'{" " * indent}NoObject')

    def __next__(self):
        return None

    def gen_asm(self, result_offset):
        raise CompilerError(f'NoObject gen_asm')


class CComponent:
    def __init__(self, compiler):
        self.compiler = compiler
        self.lineno = compiler.current_lineno
        
    def print(self, text):
        self.compiler.print_normal(text)

    def print_red(self, text):
        self.compiler.print_red(text)

    def print_yellow(self, text):
        self.compiler.print_yellow(text)

    def print_green(self, text):
        self.compiler.print_green(text)

    def print_orange(self, text):
        self.compiler.print_orange(text)

    def write_asm_data(self, code: str):
        self.compiler.asm_data.write(code)

    def write_asm(self, code: str):
        self.compiler.asm_code.write(code)

    def stack_alloc(self, size, comment):
        self.write_asm(f'    sub rsp, {size} ; {comment}\n')
        return self.compiler.add_function_stack_offset(size)
        
    def stack_free(self, size, comment):
        self.write_asm(f'    add rsp, {size} ; {comment}\n')
        return self.compiler.add_function_stack_offset(-size)

    def push_reg(self, reg, comment = ''):
        self.write_asm(f'    push {reg} ; {comment}\n')
        self.compiler.add_function_stack_offset(8)

    def pop_reg(self, reg, comment = ''):
        self.write_asm(f'    pop {reg} ; {comment}\n')
        self.compiler.add_function_stack_offset(-8)

    def print_current_scope(self, msg = ''):
        self.print(f'{self.__class__.__name__} {msg} scope_level = {len(self.compiler.scopes)} scope = ')
        pprint.pprint(self.compiler.scopes[-1], indent = 4)

    def get_scope_item(self, name):
        item = self.compiler.scopes[-1].current.get(name, None)
        if item is None:
            item = self.compiler.scopes[-1].outer.get(name, None)

        return item

    def add_to_scope(self, item, add_to_variable_stack_size = True):
        if item['name'] in self.compiler.scopes[-1].current:
            self.raise_code_error(f'[{item["name"]}] already defined')

        self.compiler.scopes[-1].current[item['name']] = item

        if add_to_variable_stack_size:
            if 'lv' in item or 'array_data' in item:
                if 'global' not in item:
                    self.compiler.scopes[-1].variable_stack_size += item['size']

    def enter_scope(self):
        self.write_asm(f'    ; enter_scope\n')
        self.compiler.enter_scope()

    def leave_scope(self, free_stack_variables = True):
        self.write_asm(f'    ; leave_scope\n')
        if free_stack_variables:
            data_size = self.compiler.scopes[-1].variable_stack_size
            if data_size > 0:
                self.stack_free(data_size, f'leave_scope. free stack variables. size = {data_size}')

        self.compiler.leave_scope()

    def raise_code_error(self, msg = ''):
        raise CodeError(f'line {self.lineno}: {msg}')

    def raise_compiler_error(self, msg = ''):
        raise CompilerError(f'line {self.lineno}: {msg}')

    def gen_asm_helper(func):
        @functools.wraps(func)
        def helper(self, *args, **kwargs):
            saved_lineno = self.compiler.current_lineno
            self.compiler.current_lineno = self.lineno

            ret = func(self, *args, **kwargs)

            self.compiler.current_lineno = saved_lineno
            return ret

        return helper

    def set_lv_value(self, left_data, right_data):
        if 'lv' not in left_data:
            self.raise_code_error(f'= needs lvalue')

        # left value to TEMP_REG_3
        if 'lv_address' in left_data:
            self.write_asm(f'    mov {TEMP_REG_3}, [rbp - {left_data["offset"]}] ; lv_address to {TEMP_REG_3}\n')
        else:
            if 'global' in left_data:
                self.write_asm(f'    lea {TEMP_REG_3}, {left_data["name"]} ; global left address to {TEMP_REG_3}\n')
            else:
                self.write_asm(f'    mov {TEMP_REG_3}, rbp ; rbp to {TEMP_REG_3}\n')
                self.write_asm(f'    sub {TEMP_REG_3}, {left_data["offset"]} ; local left address to {TEMP_REG_3}\n')

        # right value to TEMP_REG_4
        if 'value' in right_data:
            self.write_asm(f'    mov {TEMP_REG_4}, {right_data["value"]} ; right value to {TEMP_REG_4}\n')
        else:
            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {right_data["offset"]}] ; right address {TEMP_REG_4}\n')

            # if 'lv_address' in right_data:
            #    self.write_asm(f'    mov {TEMP_REG_4}, [{TEMP_REG_4}] ; get right value\n')

        # TEMP_REG_3 = left runtime address
        # TEMP_REG_4 = right value
        self.write_asm(f'    mov [{TEMP_REG_3}], {TEMP_REG_4} ; right value to left address\n')


class TypeSpecifier(CComponent):
    # void
    # char
    # short
    # int
    # long
    # float
    # double
    # signed
    # unsigned
    # struct-or-union-specifier
    # enum-specifier
    # typedef-name

    def __init__(self, compiler, type_data):
        super().__init__(compiler)
        self.type_data = type_data

    def __repr__(self):
        return f'TypeSpecifier {self.type_data}'

    def print_me(self, indent = 0):
        self.print(f'{" " * indent}TypeSpecifier')
        if hasattr(self.type_data, 'print_me'):
            self.type_data.print_me(indent + PRINT_INDENT)
        else:
            self.print(f'{" " * (indent + PRINT_INDENT)}{self.type_data}')


class Typedef(CComponent):
    def __init__(self, compiler, dss, dtr):
        super().__init__(compiler)
        self.dss = dss
        self.dtr = dtr
        self.name = dtr[1]['name']

    def __repr__(self):
        return f'{self.__class__.__name__} {self.name} {self.dss} {self.dtr}'

    def print_me(self, indent = 0):
        self.print(f'{" " * indent}{self.__class__.__name__}')
        self.print(f'{" " * (indent + PRINT_INDENT)}name = {self.name}')

        self.print(f'{" " * (indent + PRINT_INDENT)}dss =')

        for k in self.dss:
            self.print(f'{" " * (indent + PRINT_INDENT * 2)}{k} = {self.dss[k]}')

        self.print(f'{" " * (indent + PRINT_INDENT)}dtr =')
        self.print(f'{" " * (indent + PRINT_INDENT * 2)}{self.dtr}')


class StructUnion(CComponent):
    # struct-or-union identifier? { struct-declaration-list }
    # struct-or-union identifier

    # struct          S1          { int a, b; ... }
    # struct                      { int a, b; ... }
    # struct          S2

    # 1. define a full struct. with name that can be used later.
    # 2. disposable struct. use once.
    # 3. S2 must exist

    def __init__(self, compiler, tp, name, decls):
        super().__init__(compiler)
        self.tp = tp  # 'struct' or 'union'
        self.name = name
        self.decls = decls

        self.size = None
        self.members = {}

    def __repr__(self):
        return f'{self.__class__.__name__} {self.name} {self.decls} size = {self.size}'

    def print_me(self, indent = 0):
        self.print(f'{" " * indent}{self.tp}')
        self.print(f'{" " * (indent + PRINT_INDENT)}name = {self.name}')
        if self.decls:
            for decl in self.decls:
                # self.print_red(f'decl = {decl}')
                if hasattr(decl, 'print_me'):
                    decl.print_me(indent + PRINT_INDENT)
                else:
                    self.print(f'{" " * (indent + PRINT_INDENT)}{decl}')
        else:
            self.print(f'{" " * (indent + PRINT_INDENT)}NoObject()')

    @CComponent.gen_asm_helper
    def gen_asm(self):
        self.gen_struct_data()

    def gen_struct_data(self):
        self.print(f'gen_struct_data type = {self.tp}')

        if self.tp == 'struct':
            self.print_me()

            if self.decls: # case 1 case 2
                # gen data

                offset = 0

                for decl in self.decls:
                    self.print_red(decl)
                    # (['const', TypeSpecifier float], [(([], {'type': 'var', 'name': 'a'}), None), (([[], [], []], {'type': 'var', 'name': 'b'}), None)])

                    ts = None

                    for item in decl[0]:  # ['const', TypeSpecifier int, ...]
                        if isinstance(item, TypeSpecifier):
                            if item.type_data in ['int']:
                                ts = item.type_data
                            elif isinstance(item.type_data, StructUnion):
                                # find struct
                                struct = self.get_scope_item(item.type_data.name)
                                if struct is None:
                                    self.raise_code_error(f'[{item.type_data.name}] not found')

                                # not struct
                                if 'struct_data' not in struct:
                                    self.raise_code_error(f'[{item.type_data.name}] is not struct')

                                self.print_red(f'item = {item}')

                                ts = struct
                            else:
                                self.raise_code_error(f'no support for type [{item.type_data}]')

                    for item in decl[1]:
                        self.print_red(item)

                        array_size = 1
                        ranks = []
                        dim = 0

                        item_def = item[0][1]
                        name = item_def['name']

                        if 'array_data' in item_def:
                            dim = item_def['array_data']['dim']
                            for rank_exp in item_def['array_data']['ranks']:

                                result = rank_exp.gen_asm(None, set_result = False, need_global_const = True)

                                if 'value' not in result:
                                    self.raise_code_error(f'array rank must be const')

                                array_size *= result['value']
                                ranks.append(result['value'])

                        # c struct has no initializer(default value)
                        # take ([], {'type': 'var', 'name': 'a'})

                        # self.print_red(f'ts = {ts}')
                        # self.print_red(f'item = {item}')

                        if ts in ['int']:
                            member_data = copy.deepcopy(item_def)
                            member_data['data_type'] = ts

                            if len(item[0][0]) > 0:
                                member_data['pointer_data'] = copy.deepcopy(item[0][0])
                            member_data['offset'] = offset

                            if 'array_data' in item_def:
                                member_data['size'] = 8 * array_size
                            else:
                                member_data['size'] = 8

                            self.members[name] = member_data

                            offset += member_data['size']
                        elif isinstance(ts, dict):
                            # struct

                            """
                            ts = {'type': 'struct', 
                                'name': 'S1', 
                                'struct_data': {'a': {'type': 'var', 'name': 'a', 'pointer_data': [], 'offset': 0}, 
                                                'b': {'type': 'var', 'name': 'b', 'pointer_data': [[], [], []], 'offset': 8}, 
                                                'c': {'type': 'var', 'name': 'c', 'pointer_data': [], 'offset': 16}, 
                                                'd': {'type': 'var', 'name': 'd', 'pointer_data': [], 'offset': 24}}, 
                                'size': 32}
                            """

                            member_data = copy.deepcopy(item_def)
                            member_data['data_type'] = ts['name']
                            if len(item[0][0]) > 0:
                                member_data['pointer_data'] = copy.deepcopy(item[0][0])
                            member_data['offset'] = offset

                            if 'array_data' in item_def:
                                member_data['size'] = ts['size'] * array_size
                            else:
                                member_data['size'] = ts['size']

                            self.members[name] = member_data

                            offset += member_data['size']
                        else:
                            self.print_red(ts)
                            self.raise_code_error(f'no support for type [{ts}]')

                self.size = offset

                if self.name: # case 1
                    # add to type list
                    if self.get_scope_item(self.name) is not None:
                        self.raise_code_error(f'[{self.name}] already defined')

                    self.add_to_scope({'name': self.name, 'struct_data':self.members, 'size':self.size})
            else: # case 3
                # find struct type
                if self.get_scope_item(self.name) is None:
                    self.raise_code_error(f'[{self.name}] not defined')

                struct_data = self.get_scope_item(self.name)
                self.size = struct_data['size']

            # raise
        else:
            self.raise_code_error(f'no support')


class AssignmentExpression(CComponent):
    # conditional-expression
    # unary-expression assignment-operator assignment-expression
    def __init__(self, compiler, ce = NoObject(), ue = NoObject(), opt = NoObject(), ae = NoObject()):
        super().__init__(compiler)
        self.ce = ce
        self.ue = ue
        self.opt = opt # = *= /= %= += -= <<= >>= &= ^= |=
        self.ae = ae

    def __repr__(self):
        return f'AssignmentExpression {self.ce, self.ue, self.opt, self.ae}'

    def print_me(self, indent):
        self.print(f'{" " * indent}AssignmentExpression')
        if self.ce:
            self.ce.print_me(indent + PRINT_INDENT)
        else:
            self.ue.print_me(indent + PRINT_INDENT)
            self.print(f'{" " * (indent + PRINT_INDENT)}{self.opt}')
            self.ae.print_me(indent + PRINT_INDENT)

    @CComponent.gen_asm_helper
    def gen_asm(self, my_result_offset = None, set_result = True, need_global_const = False, **kwargs):
        if self.ce:
            return self.ce.gen_asm(my_result_offset, set_result, need_global_const = need_global_const, **kwargs)
        else:
            self.write_asm(f'    ; AssignmentExpression get left_data\n')
            left_data = self.ue.gen_asm(my_result_offset)

            if 'lv' in left_data:
                # case 1: *p = 123;
                # case 2: abc = *p;
                # a = *b = *c
                # *a = *b = 1

                if self.opt == '=':
                    offset = self.stack_alloc(8, 'for AssignmentExpression')

                    self.write_asm(f'    ; AssignmentExpression get right_data\n')
                    right_data = self.ae.gen_asm(offset, fetch_lv_address_value = True)

                    self.print_red(f'left_data = {left_data}')
                    self.print_red(f'right_data = {right_data}')

                    self.set_lv_value(left_data, right_data)

                    if set_result:
                        if 'fetch_lv_address_value' in kwargs:
                            # value must be in TEMP_REG_4
                            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_4} ; save value to dest\n')
                        else:
                            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_3} ; save address to dest\n')

                    self.stack_free(8, 'for AssignmentExpression')

                    return left_data
                else:
                    self.raise_code_error(f'no support')
            else:
                self.raise_code_error(f'AssignmentExpression on wrong type [{left_data}]')


class Expression(CComponent):
    # assignment-expression
    # expression , assignment-expression

    def __init__(self, compiler, aes: list[AssignmentExpression]):
        super().__init__(compiler)
        self.aes = aes

    def __repr__(self):
        return f'Expression {self.aes}'

    def print_me(self, indent):
        self.print(f'{" " * indent}Expression len = {len(self.aes)}')
        for ae in self.aes:
            if hasattr(ae, 'print_me'):
                ae.print_me(indent + PRINT_INDENT)
            else:
                self.print(f'{" " * (indent + PRINT_INDENT)}{ae}')

    @CComponent.gen_asm_helper
    def gen_asm(self, my_result_offset = None, set_result = True, **kwargs):
        result = None

        for ae in self.aes:
            self.write_asm(f'\n    ; Expression start offset = {self.compiler.get_function_stack_offset()} my_result_offset = {my_result_offset}\n')
            result = ae.gen_asm(my_result_offset, set_result)
            self.write_asm(f'    ; Expression over offset = {self.compiler.get_function_stack_offset()}\n\n')

        return result


class Constant(CComponent):
    def __init__(self, compiler, data_type, const):
        super().__init__(compiler)
        self.data_type = data_type
        self.const = const

    def __repr__(self):
        return f'Constant({self.const})'

    def print_me(self, indent):
        self.print(f'{" " * indent}Constant')
        # self.dtr.print_me(indent + PRINT_INDENT)
        self.print(f'{" " * (indent + PRINT_INDENT)}{self.const}')
        # self.init.print_me(indent + PRINT_INDENT)


class Identifier(CComponent):
    def __init__(self, compiler, name: str):
        super().__init__(compiler)
        self.name = name

    def __repr__(self):
        return f'Identifier({self.name})'

    def __eq__(self, other):
        return self.name == other

    def print_me(self, indent):
        self.print(f'{" " * indent}Identifier({self.name})')


class PrimaryExpression(CComponent):
    # identifier
    # constant
    # string-literal
    # ( expression )

    def __init__(self, compiler, idf: Identifier = NoObject(), const: Constant = NoObject(), string = NoObject(), exp: Expression = NoObject()):
        super().__init__(compiler)
        self.idf = idf
        self.const = const
        self.string = string
        self.exp = exp

    def __repr__(self):
        return f'PrimaryExpression {self.idf, self.const, self.string, self.exp}'

    def print_me(self, indent):
        self.print(f'{" " * indent}PrimaryExpression')
        if self.idf:
            self.print(f'{" " * (indent + PRINT_INDENT)}{self.idf}')
        elif self.const:
            self.print(f'{" " * (indent + PRINT_INDENT)}{self.const}')
        elif self.string:
            self.print(f'{" " * (indent + PRINT_INDENT)}{self.string}')
        else:
            self.print(f'{" " * (indent + PRINT_INDENT)}{self.exp}')

    @CComponent.gen_asm_helper
    def gen_asm(self, result_offset = None, set_result = True, need_global_const = False):
        self.write_asm(f'    ; PrimaryExpression gen_asm\n')

        if need_global_const: # todo ( expression )
            if self.idf:
                scope_item = self.get_scope_item(self.idf.name)
                if scope_item is None:
                    self.raise_code_error(f'[{self.idf.name}] not defined')

                self.print_red(scope_item)
                if 'value' in scope_item:
                    const_item = scope_item.copy()
                    return const_item
                else:
                    self.raise_code_error(f'need_global_const')
            elif self.const:
                return {'value':self.const.const, 'data_type':'int'}
            else:
                self.raise_code_error(f'need_global_const')

        if self.idf:
            name = self.idf.name

            scope_item = self.get_scope_item(name)
            if scope_item is None:
                self.print_current_scope()
                self.raise_code_error(f'[{name}] not defined')

            self.print_red(scope_item)

            if set_result:
                if 'array_data' in scope_item:
                    if 'global' in scope_item:
                        self.write_asm(f'    lea {TEMP_REG_4}, {name} ; get array address [{name}]\n')
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move array address to result_offset {result_offset}\n')
                    else:
                        self.write_asm(f'    mov {TEMP_REG_4}, rbp ; get array address 1 {name}\n')
                        self.write_asm(f'    sub {TEMP_REG_4}, {scope_item["offset"]} ; get array address 2 {name}\n')
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move array address {name} to result_offset {result_offset}\n')
                elif 'function_data' in scope_item:
                    # elif scope_item['type'] == 'function':
                    self.write_asm(f'    lea {TEMP_REG_4}, {name}\n')
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move function {name} address to result_offset {result_offset}\n')
                elif True: # 'lv' in scope_item:
                    if 'global' in scope_item:
                        type_item = self.get_scope_item(scope_item['data_type']) # struct
                        if type_item and 'struct_data' in type_item:
                            pass
                        else:
                            self.write_asm(f'    mov {TEMP_REG_4}, {name} ; move global var {name}\n')
                            self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move global var {name} to result_offset {result_offset}\n')
                    else:
                        # todo: local struct
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {scope_item["offset"]}] ; move local var {name}\n')
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move local var {name} to result_offset {result_offset}\n')
                else:
                    self.raise_compiler_error(f'unknown obj [{scope_item}]')

            return scope_item
        elif self.const:
            if set_result:
                self.write_asm(f'    mov qword ptr [rbp - {result_offset}], {self.const.const} ; mov const\n')
            return {'value':self.const.const, 'data_type':'int'}
        elif self.string:
            if len(self.string) == 0:
                self.raise_code_error('empty string')

            # todo: very long string

            # put string in .data
            string_var_name = f'string_{self.compiler.item_id}'

            # escape \n
            final_string = '' # use "" in asm
            escape_again = False
            in_normal_string = False # like "ashdba
            i = 0
            while i < len(self.string):
                if self.string[i] != '\\':
                    if in_normal_string:
                        final_string += self.string[i] # just insert
                    else:
                        final_string += f'"{self.string[i]}' # start a ""
                        in_normal_string = True

                    i += 1
                else: # self.string[i] == '\\':
                    if i + 1 >= len(self.string):
                        self.raise_code_error(f'string escape error')

                    next_c = self.string[i + 1]

                    if next_c == 'n':
                        if in_normal_string:
                            final_string += '", 10, ' # close a "" add newline
                        else:
                            final_string += '10, ' # add newline
                    else:
                        pass

                    in_normal_string = False
                    i += 2

            if in_normal_string:
                final_string += '", 0'  # close a "" add 0
            else:
                final_string += ' 0'  # add 0

            self.write_asm_data(f'{string_var_name} byte {final_string}\n')
            self.compiler.item_id += 1

            if set_result:
                self.write_asm(f'    lea {TEMP_REG_4}, {string_var_name} ; load string {string_var_name}\n')
                self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; load string {string_var_name}\n')

            return {'data_type':'string', 'name':string_var_name, 'global':1}
        else:
            return self.exp.gen_asm(result_offset)


class PostfixExpression(CComponent):
    # primary-expression
    # postfix-expression [ expression ] # array index
    # postfix-expression ( argument-expression-list? ) # function call
    # postfix-expression . identifier
    # postfix-expression -> identifier
    # postfix-expression ++
    # postfix-expression --

    def __init__(self, compiler, primary: PrimaryExpression, data):
        super().__init__(compiler)
        self.primary = primary
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'PostfixExpression {self.primary, self.data}'

    def print_me(self, indent):
        self.print(f'{" " * indent}PostfixExpression')
        self.primary.print_me(indent + PRINT_INDENT)
        self.print(f'{" " * (indent + PRINT_INDENT)}postfix data = {self.data}')

    @CComponent.gen_asm_helper
    def gen_asm(self, result_offset, set_result = True, need_global_const = False, **kwargs):
        self.write_asm(f'    ; PostfixExpression gen_asm\n')

        # if self.primary.idf:
        primary_item = self.primary.gen_asm(result_offset, set_result = True, need_global_const = need_global_const)
        self.print_red(primary_item)

        if need_global_const:
            if len(self.data) > 0:
                self.raise_code_error(f'need_global_const')

        current_obj = copy.deepcopy(primary_item) # avoid breaking original data

        for item in self.data:
            if item in ['++', '--']:
                if 'lv' not in current_obj:
                    self.raise_code_error(f'post {item} needs lvalue')

                if result_offset is None:
                    self.raise_compiler_error(f'post {item} must has result_offset')

                # if current_obj['name'] != 'wtf':
                #    raise

                if 'lv_address' in current_obj:
                    self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {result_offset}] ; get lv_address\n')
                    self.write_asm(f'    mov {TEMP_REG_5}, {TEMP_REG_4} ; copy address\n')
                    self.write_asm(f'    mov {TEMP_REG_4}, [{TEMP_REG_4}] ; get lvalue\n')
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; value to result\n')

                    # update lvalue
                    if item == '++':
                        self.write_asm(f'    inc qword ptr [{TEMP_REG_5}] ; {current_obj["name"]}++\n')
                    else:
                        self.write_asm(f'    dec qword ptr [{TEMP_REG_5}] ; {current_obj["name"]}--\n')
                else:
                    # get original value as result
                    # todo: global
                    self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {current_obj["offset"]}]\n')
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4}\n')

                    # current_obj = {'data_type':'int', 'offset':result_offset}

                    # update lvalue
                    if item == '++':
                        self.write_asm(f'    inc qword ptr [rbp - {current_obj["offset"]}] ; {current_obj["name"]}++\n')
                    else:
                        self.write_asm(f'    dec qword ptr [rbp - {current_obj["offset"]}] ; {current_obj["name"]}--\n')

                current_obj['offset'] = result_offset
                current_obj.pop('lv')
                current_obj.pop('lv_address', None)

            elif item[0] == '.':
                if 'lv' in current_obj:
                    self.print_red(f'{current_obj = }')

                    # get struct data

                    # struct S1 s1;
                    # s1.a = 123;
                    # current_obj = {'type': 'var', 'data_type': 'S1', 'name': 's1', 'offset': 24}
                    struct = self.get_scope_item(current_obj['data_type'])
                    if struct is None:
                        self.raise_code_error(f'[{current_obj["data_type"]}] not found')

                    # check struct
                    if 'struct_data' not in struct:
                        self.raise_code_error(f'. on non struct [{current_obj["data_type"]}]')

                    # check member
                    member_name = item[1].name
                    member_data = struct['struct_data'].get(member_name, None)
                    if member_data is None:
                        self.raise_code_error(f'[{member_name}] is not a member of {current_obj["data_type"]}')
                    member_data = copy.deepcopy(member_data) # avoid breaking original data

                    # get runtime address
                    if 'lv_address' in current_obj:
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {result_offset}] ; get struct address\n')
                        self.write_asm(f'    add {TEMP_REG_4}, {member_data["offset"]} ; get struct member address\n')
                    else:
                        if 'global' in current_obj:
                            self.write_asm(f'    lea {TEMP_REG_4}, {current_obj["name"]} ; get global struct address\n')
                            self.write_asm(f'    add {TEMP_REG_4}, {member_data["offset"]} ; get struct member address\n')
                        else:
                            self.write_asm(f'    mov {TEMP_REG_4}, rbp ; get local struct address\n')
                            self.write_asm(f'    sub {TEMP_REG_4}, {current_obj["offset"] - member_data["offset"]} ; get struct member address\n')

                    # set runtime address to result_offset
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; struct member address to result_offset\n')

                    # update to member
                    current_obj['data_type'] = member_data['data_type']
                    current_obj['offset'] = result_offset # member_data['offset']
                    current_obj['name'] = member_data['name']

                    if 'global' in current_obj: # force member to non-global
                        current_obj.pop('global')

                    if 'array_data' in member_data:
                        current_obj['array_data'] = member_data['array_data']
                        current_obj.pop('lv')
                        current_obj.pop('lv_address', None)
                    else:
                        current_obj['lv_address'] = 1

                    if 'pointer_data' in member_data:
                        current_obj['pointer_data'] = member_data['pointer_data']
                else:
                    self.raise_code_error(f'. on [{current_obj["type"]}]')

            elif item[0] == '->':
                if 'pointer_data' in current_obj:
                    # S1 *p2
                    # {'lv': 1, 'data_type': 'S1', 'name': 'p2', 'offset': 84880, 'size': 832, 'pointer_data': [[]]}

                    # get struct data

                    # struct S1 *p;
                    # p->a = 123;
                    # current_obj = {'type': 'pointer', 'data_type': 'S1', 'name': 'p', 'offset': 24}
                    struct = self.get_scope_item(current_obj['data_type'])
                    if struct is None:
                        self.raise_code_error(f'[{current_obj["data_type"]}] not found')

                    # not struct
                    if 'struct_data' not in struct:
                        self.raise_code_error(f'. on non struct [{current_obj["data_type"]}]')

                    # not member
                    member_name = item[1].name
                    member_data = struct['struct_data'].get(member_name, None)
                    if member_data is None:
                        self.raise_code_error(f'[{member_name}] is not a member of {current_obj["data_type"]}')

                    # get runtime address
                    if 'global' in current_obj:
                        self.write_asm(f'    mov {TEMP_REG_4}, {current_obj["name"]} ; get global pointer value\n')
                    else:
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {current_obj["offset"]}]; get pointer value\n')

                    self.write_asm(f'    add {TEMP_REG_4}, {member_data["offset"]} ; get member address\n')

                    # set address to result_offset
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; struct member address to result_offset\n')

                    # update to member
                    current_obj['data_type'] = member_data['data_type']
                    current_obj['offset'] = result_offset # member_data['offset']
                    current_obj['name'] = member_data['name']

                    if 'global' in current_obj:  # force member to non-global
                        current_obj.pop('global')

                    if 'array_data' in member_data:
                        current_obj['array_data'] = member_data['array_data']
                        current_obj.pop('lv')
                        current_obj.pop('lv_address', None)
                    else:
                        current_obj['lv_address'] = 1

                    if 'pointer_data' in member_data:
                        current_obj['pointer_data'] = member_data['pointer_data']
                else:
                    self.raise_code_error(f'. on [{current_obj["type"]}]')
            elif item[0] == 'array index':

                # stack layout
                # a[2][3][4]
                # [[[x, x, x, x], [x, x, x, x], [x, x, x, x]], [[x, x, x, x], [x, x, x, x], [x, x, x, x]]]

                # example
                # int arrrrrrr[3][222]
                # [[x, x, ...], [x, x, ...], [x, x, ...]]
                # current_obj = {'type': 'array', 'data_type': 'int', 'name': 'arrrrrrr', 'offset': 5336, 'dim': 2, 'ranks': [3, 222]}

                # arrrrrrr[exp]
                # sub_elements_count = 222
                # new_address = rbp - 5336 + exp * sub_elements_count
                # -> {'type': 'de_array', 'data_type': 'int', 'name': 'arrrrrrr', 'offset': 5336, 'dim': 1, 'ranks': [222]}
                # save new_address to result_offset

                if 'array_data' not in current_obj and 'pointer_data' not in current_obj:
                    self.raise_code_error(f'indexing on wrong type [{current_obj}]')

                if 'array_data' in current_obj:
                    pass # address already in result_offset
                elif 'pointer_data' in current_obj:
                    self.raise_compiler_error(f'no support yet')

                offset = self.stack_alloc(8, 'array index. for exp result')

                exp_data = item[1].gen_asm(offset, fetch_lv_address_value = True)
                self.print_red(exp_data)

                # check exp_data
                if exp_data['data_type'] not in ['int']:
                    self.raise_code_error(f'wrong type {exp_data["data_type"]} as array index')

                # get array[exp] address
                # sub_elements_count is known at compile time by array declaration
                sub_elements_count = 1
                for rank in current_obj['array_data']['ranks'][1:]:
                    sub_elements_count *= rank

                self.write_asm(f'    ; sub_elements_count = {sub_elements_count} is known at compile time by array declaration\n')

                # new_address = current_address + exp * sub_elements_count * element_size

                element_size = 8 # 8 for all simple data types for now

                data_type = current_obj['data_type']
                if data_type in ['int']:
                    pass
                else:
                    scope_item = self.get_scope_item(data_type)
                    if scope_item is None:
                        self.raise_code_error(f'[{data_type}] not defined')

                    element_size = scope_item['size']

                # exp * sub_elements_count * element_size
                self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}] ; get exp result\n')
                self.write_asm(f'    imul {TEMP_REG_4}, {sub_elements_count} ; exp * sub_elements_count\n')
                self.write_asm(f'    imul {TEMP_REG_4}, {element_size} ; * element_size {element_size}\n')

                # + current_address
                self.write_asm(f'    add {TEMP_REG_4}, [rbp - {result_offset}] ; + current_address\n')

                # save address
                # runtime value
                self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; save address\n')

                # case 1: arrrrrrr[3][222] arrrrrrr[1]
                # case 2: arrrrrrr[3]      arrrrrrr[1]
                if len(current_obj['array_data']['ranks']) >= 1:
                    # still array
                    current_obj['array_data']['ranks'] = current_obj['array_data']['ranks'][1:]
                    current_obj['array_data']['dim'] -= 1
                else:
                    self.raise_code_error(f'indexing on wrong data {current_obj}')

                # becomes lvalue
                if current_obj['array_data']['dim'] == 0:
                    current_obj.pop('array_data')
                    current_obj['lv'] = 1
                    current_obj['lv_address'] = 1

                current_obj['offset'] = result_offset

                # free
                self.stack_free(8, 'array index. for exp result')

            elif item[0] == 'function call':
                # check args
                args_count = len(item[1])

                if 'function_data' not in current_obj:
                    self.raise_code_error(f'call non-function [{current_obj}]')

                    self.print_red(current_obj)

                variable_arg_list = False
                def_args_count = len(current_obj['function_data']['args'])
                if def_args_count > 0:
                    if current_obj['function_data']['args'][-1] == '...':
                        variable_arg_list = True

                if variable_arg_list:
                    if args_count < (def_args_count - 1):
                        self.raise_code_error(f'function args not match [{current_obj["name"]}]')
                else:
                    if args_count != len(current_obj['function_data']['args']):
                        self.raise_code_error(f'function args not match [{current_obj["name"]}]')

                # save args count to {TEMP_REG_5}

                # stack
                #   {TEMP_REG_5}
                #   arg n
                #   ...
                #   arg 2
                #   arg 1

                self.write_asm(f'\n    ; start function call [{self.primary.idf.name}] offset = {self.compiler.get_function_stack_offset()}\n')

                # abi shadow
                # at lease 4
                abi_storage_args_count = args_count
                if abi_storage_args_count < 4:
                    abi_storage_args_count = 4

                # alignment
                # 1 for {TEMP_REG_5}
                align = ((1 + abi_storage_args_count) * 8 + self.compiler.get_function_stack_offset()) % 16
                if align not in [0, 8]:
                    self.raise_compiler_error(f'check alignment before call align = {align} not in [0, 8]')

                if align != 0:
                    self.stack_alloc(8, 'padding for function call')

                self.push_reg(TEMP_REG_5)
                self.write_asm(f'    mov {TEMP_REG_5}, {args_count}; {args_count = }\n')

                # space for args
                last_offset = self.stack_alloc(8 * abi_storage_args_count, 'alloc function call args')
                self.write_asm(f'    ; last_offset = {last_offset}\n')

                # gen_asm for each arg
                for ae in item[1]:
                    # self.print_red(f'arg = {ae}')
                    ae.print_me(0)
                    ae_data = ae.gen_asm(last_offset, fetch_lv_address_value = True)

                    last_offset -= 8

                # microsoft abi
                # rcx rdx r8 r9 stack...

                last_offset = self.compiler.get_function_stack_offset()
                for i in range(0, min(4, args_count)):
                    if i == 0:
                        self.write_asm(f'    mov rcx, [rbp - {last_offset}] ; arg {i}\n')
                    elif i == 1:
                        self.write_asm(f'    mov rdx, [rbp - {last_offset}] ; arg {i}\n')
                    elif i == 2:
                        self.write_asm(f'    mov r8, [rbp - {last_offset}] ; arg {i}\n')
                    elif i == 3:
                        self.write_asm(f'    mov r9, [rbp - {last_offset}] ; arg {i}\n')
                    last_offset -= 8

                self.write_asm(f'\n    call {self.primary.idf.name} ; {len(item[1])} args. offset = {self.compiler.get_function_stack_offset()}\n')
                self.write_asm(f'    ; call return. offset = {self.compiler.get_function_stack_offset()}\n')

                if set_result:
                    self.write_asm(f'    mov [rbp - {result_offset}], rax ; save call result\n')

                # clean
                self.stack_free(8 * abi_storage_args_count, 'free function call args')
                self.pop_reg(TEMP_REG_5)

                if align != 0:
                    self.stack_free(8, 'clean padding for function call')

                self.write_asm(f'\n    ; function call over [{self.primary.idf.name}]\n\n')

                current_obj['type'] = 'mem'
                current_obj['offset'] = result_offset

            else:
                self.raise_compiler_error(f'unknown postfix data {item}')

        if set_result:
            pass

        if 'fetch_lv_address_value' in kwargs:
            if 'lv_address' in current_obj:
                self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {result_offset}] ; get address\n')
                self.write_asm(f'    mov {TEMP_REG_4}, [{TEMP_REG_4}] ; fetch_lv_address_value\n')
                self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; save value\n')

        return current_obj


class UnaryExpression(CComponent):
    # postfix-expression
    # ++ unary-expression
    # -- unary-expression
    # unary-operator cast-expression
    # sizeof unary-expression
    # sizeof ( type-name )

    def __init__(self, compiler, pe: PostfixExpression = NoObject(), pp = NoObject(), ue = NoObject(), uo = NoObject(),
                 cast = NoObject(), sizeof = NoObject(), tn = NoObject()):
        super().__init__(compiler)
        self.pe = pe
        self.pp = pp
        self.ue = ue
        self.uo = uo
        self.cast = cast
        self.sizeof = sizeof
        self.tn = tn

    def __repr__(self):
        return f'UnaryExpression {self.pe, self.pp, self.ue, self.uo, self.cast, self.sizeof, self.tn}'

    def print_me(self, indent):
        self.print(f'{" " * indent}UnaryExpression')
        # self.print(f'{" " * (indent + PRINT_INDENT)}{self.pe, self.pp, self.ue, self.uo, self.cast, self.sizeof, self.tn}')
        if self.pe:
            self.pe.print_me(indent + PRINT_INDENT)
        elif self.pp:
            self.print(f'{" " * (indent + PRINT_INDENT)}{self.pp}')
            self.ue.print_me(indent + PRINT_INDENT)
        elif self.uo:
            self.print(f'{" " * (indent + PRINT_INDENT)}{self.uo}')
            self.cast.print_me(indent + PRINT_INDENT)
        elif self.sizeof:
            self.print(f'{" " * (indent + PRINT_INDENT)}sizeof')
            if self.ue:
                self.ue.print_me(indent + PRINT_INDENT)
            else:
                self.tn.print_me(indent + PRINT_INDENT)

    @CComponent.gen_asm_helper
    def gen_asm(self, result_offset, set_result = True, need_global_const = False, **kwargs):
        self.write_asm(f'    ; UnaryExpression gen_asm {self.uo}\n')

        if self.pe:
            data = self.pe.gen_asm(result_offset, need_global_const = need_global_const, **kwargs)
            self.print_red(data)
            return data
        elif self.pp:
            if need_global_const:
                self.raise_code_error(f'{self.pp} need_global_const')

            data = self.ue.gen_asm(result_offset)

            if 'lv' not in data:
                self.print_red(data)
                self.raise_code_error(f'prefix {self.pp} needs lvalue')

            if 'pointer_data' in data or 'array_data' in data:
                self.raise_code_error(f'no support yet')

            if 'lv_address' in data:
                self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {result_offset}] ; get lv_address\n')

                # update lvalue
                if self.pp == '++':
                    self.write_asm(f'    inc qword ptr [{TEMP_REG_4}] ; ++{data["name"]}\n')
                else:
                    self.write_asm(f'    dec qword ptr [{TEMP_REG_4}] ; --{data["name"]}\n')

                if set_result:
                    if 'fetch_lv_address_value' in kwargs:
                        self.write_asm(f'    mov {TEMP_REG_4}, [{TEMP_REG_4}]\n')

                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4}\n')
            else:
                if self.pp == '++':
                    self.write_asm(f'    inc qword ptr [rbp - {data["offset"]}] ; ++{data["name"]}\n')
                else:
                    self.write_asm(f'    dec qword ptr [rbp - {data["offset"]}] ; --{data["name"]}\n')

                if set_result:
                    self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {data["offset"]}]\n')
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4}\n')

            data['offset'] = result_offset
            data.pop('lv')
            data.pop('lv_address', None)


            return data
        elif self.uo:
            if need_global_const:
                self.raise_code_error(f'{self.uo} need_global_const')

            # ['&', '*', '+', '-', '~', '!']
            if self.uo == '-':
                data = self.cast.gen_asm(result_offset)

                # error
                # if data['type'] not in ['const', 'var']:
                #     self.raise_code_error(f"- on {data['type']}")

                # c std 6.5.3.3
                self.write_asm(f'    neg qword ptr [rbp - {result_offset}] ; negation\n')

                if 'value' in data:
                    data['value'] = -data['value']
                    return data

                return {'data_type':'int', 'offset':result_offset}
            elif self.uo == '&':
                # int arr2[100][100];
                # arr2[1], &arr2[1], &arr2[1][0] same address

                # get runtime address
                data = self.cast.gen_asm(result_offset)

                self.print_red(f'{data}')
                name = data['name']

                if 'lv' not in data:
                    self.raise_code_error(f'& needs lvalue')

                # get runtime address
                if 'lv_address' in data:
                    pass # already ok
                else:
                    if 'global' in data:
                        self.write_asm(f'    lea {TEMP_REG_4}, {name}\n')
                    else:
                        self.write_asm(f'    mov {TEMP_REG_4}, rbp\n')
                        self.write_asm(f'    sub {TEMP_REG_4}, {data["offset"]}\n')

                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; save address\n')

                # todo: pointer_data
                # &a becomes a pointer
                return {'data_type':'int', 'offset':result_offset, 'pointer_data':[[]], 'lv_address':1}

            elif self.uo == '*':
                # indirection. dereferencing.

                data = self.cast.gen_asm(result_offset, set_result = False)
                self.print_red(f'dereference. data = {data}')
                # {'type': 'pointer', 'data_type': 'int', 'name': 'p', 'offset': 16, 'pointer_data': [[], []]}
                # int **p;

                if 'pointer_data' not in data:
                    self.raise_code_error(f'* on non-pointer')

                new_data = copy.deepcopy(data) # do not break original data

                pointer_item = new_data['pointer_data'].pop()
                if len(new_data['pointer_data']) == 0:
                    new_data['lv'] = 1
                    new_data['lv_address'] = 1
                    new_data.pop('pointer_data')

                self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {new_data["offset"]}]; dereference. get pointer value\n')

                if 'lv_address' in new_data and 'fetch_lv_address_value' in kwargs:
                    self.write_asm(f'    mov {TEMP_REG_4}, [{TEMP_REG_4}]\n')

                self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4}; dereference. address to temp\n')

                new_data['offset'] = result_offset

                return new_data

            else:
                self.raise_compiler_error(f'unknown unary-operator')

        self.raise_compiler_error(f'UnaryExpression.gen_asm failed')


class CastExpression(CComponent):
    # unary-expression
    # ( type-name ) cast-expression

    def __init__(self, compiler, casts, ue: UnaryExpression):
        super().__init__(compiler)
        self.casts = casts
        self.ue = ue
        self.opt = None

    def set_opt(self, opt):
        self.opt = opt

    def __repr__(self):
        return f'CastExpression {self.casts, self.ue}'

    def print_me(self, indent):
        self.print(f'{" " * indent}CastExpression')
        self.print(f'{" " * (indent + PRINT_INDENT)}casts = {self.casts}')
        self.ue.print_me(indent + PRINT_INDENT)

    @CComponent.gen_asm_helper
    def gen_asm(self, result_offset, set_result = True, need_global_const = False, **kwargs):
        return self.ue.gen_asm(result_offset, set_result, need_global_const = need_global_const, **kwargs)


'''
caller makes space at my_result_offset

gen_asm(self, my_result_offset):
    choose a reg like {TEMP_REG_0}
    push {TEMP_REG_0}
    make slots for subitems results
    gen_asm(slot) for each subitem
    calc results, may use {TEMP_REG_0}.
    save final result in my_result_offset
    free space
    pop {TEMP_REG_0}
'''


class ChainExpression(CComponent):
    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)
        self.gen_asm_results = []
        self.opt = None

    def print_me(self, indent):
        self.print(f'{" " * indent}{self.__class__.__name__}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

    def set_opt(self, opt):
        self.opt = opt

    def get_const_result(self):
        return None

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        pass

    @CComponent.gen_asm_helper
    def gen_asm(self, final_result_offset, set_result = True, need_global_const = False, **kwargs):
        if self.data_count == 1:
            return self.data[0].gen_asm(final_result_offset, set_result, need_global_const = need_global_const, **kwargs)

        offset = None
        temp_result_offset = None
        if not need_global_const:
            self.print_red(self.data)
            self.push_reg(TEMP_REG_0, 'ChainExpression save')

            # space for exp results
            offset = self.compiler.get_function_stack_offset() + 8
            self.stack_alloc(8 * self.data_count, 'ChainExpression for exp result')

            temp_result_offset = offset # for final result

        # check const
        # if some items are const, we can make some results at compile time?
        all_known_value = True

        # gen_asm for each
        for item in self.data:
            result = item.gen_asm(offset, need_global_const = need_global_const, fetch_lv_address_value = True)

            if 'value' not in result:
                all_known_value = False
                if need_global_const:
                    self.raise_code_error(f'{self.__class__.__name__} need_global_const')

            self.print_red(result)

            self.gen_asm_results.append(result)

            if not need_global_const:
                offset += 8

        self.print_red(f'gen_asm_results = {self.gen_asm_results}')

        if all_known_value:

            result = self.get_const_result()

            if not need_global_const:
                if set_result:
                    self.write_asm(f'    mov qword ptr [rbp - {final_result_offset}], {result} ; ChainExpression set result\n')

                # free
                self.stack_free(8 * self.data_count, 'ChainExpression for exp result')
                self.pop_reg(TEMP_REG_0, 'ChainExpression recover')

            return {'value':result, 'data_type':'int'}

        self.sub_items_gen_asm(temp_result_offset, final_result_offset, set_result)

        # free
        self.stack_free(8 * self.data_count, 'ChainExpression for exp result')
        self.pop_reg(TEMP_REG_0, 'ChainExpression recover')

        if self.data_count == 1:
            return self.gen_asm_results[0]

        return {'data_type':'int', 'offset':final_result_offset}


class MultiplicativeExpression(ChainExpression):
    # cast-expression
    # multiplicative-expression * cast-expression
    # multiplicative-expression / cast-expression
    # multiplicative-expression % cast-expression

    def __init__(self, compiler, data: list[CastExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'MultiplicativeExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            if self.data[index].opt == '*':
                result *= self.gen_asm_results[index]['value']
            elif self.data[index].opt == '/':
                result = result // self.gen_asm_results[index]['value']
            elif self.data[index].opt == '%':
                result = result % self.gen_asm_results[index]['value']

        return result

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            if self.data[index].opt == '*':
                if 'value' in self.gen_asm_results[index]:
                    self.write_asm(f'    imul {TEMP_REG_0}, {self.gen_asm_results[index]["value"]}\n')
                else:
                    self.write_asm(f'    imul {TEMP_REG_0}, [rbp - {result_offset}]\n')
            elif self.data[index].opt == '/':
                # 32-bit int
                # edx:eax / dword ptr [rbp - {result_offset}]
                # quotient in eax, remainder in edx.

                # todo: corner case?
                self.write_asm(f'    push rdx\n')
                self.write_asm(f'    push rax\n')
                self.write_asm(f'    mov rdx, {TEMP_REG_0} ; set edx\n')
                self.write_asm(f'    shr rdx, 32\n')
                self.write_asm(f'    mov rax, {TEMP_REG_0} ; set eax\n')
                self.write_asm(f'    and rax, right_32f\n')  # 0xffffffff
                self.write_asm(f'    div dword ptr [rbp - {result_offset}]\n')
                self.write_asm(f'    mov {TEMP_REG_0}, rax\n')  # save result to {TEMP_REG_0}
                self.write_asm(f'    pop rax\n')
                self.write_asm(f'    pop rdx\n')
            elif self.data[index].opt == '%':
                # todo: corner case?
                self.write_asm(f'    push rdx\n')
                self.write_asm(f'    push rax\n')
                self.write_asm(f'    mov rdx, {TEMP_REG_0} ; set edx\n')
                self.write_asm(f'    shr rdx, 32\n')
                self.write_asm(f'    mov rax, {TEMP_REG_0} ; set eax\n')
                self.write_asm(f'    and rax, right_32f\n')  # 0xffffffff
                self.write_asm(f'    div dword ptr [rbp - {result_offset}]\n')
                self.write_asm(f'    mov {TEMP_REG_0}, rdx\n')  # save result to {TEMP_REG_0}
                self.write_asm(f'    pop rax\n')
                self.write_asm(f'    pop rdx\n')

        if set_result:
            self.write_asm(f'    mov [rbp - {final_result_offset}], {TEMP_REG_0} ; MultiplicativeExpression set result\n')


class AdditiveExpression(ChainExpression):
    # multiplicative-expression
    # additive-expression + multiplicative-expression
    # additive-expression - multiplicative-expression

    def __init__(self, compiler, data: list[MultiplicativeExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'AdditiveExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            if self.data[index].opt == '+':
                result += self.gen_asm_results[index]['value']
            elif self.data[index].opt == '-':
                result -= self.gen_asm_results[index]['value']

        return result

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            if self.data[index].opt == '+':
                self.write_asm(f'    add {TEMP_REG_0}, [rbp - {result_offset}]\n')
            elif self.data[index].opt == '-':
                self.write_asm(f'    sub {TEMP_REG_0}, [rbp - {result_offset}]\n')
            else:
                self.raise_compiler_error(f'wtf')

        if set_result:
            self.write_asm(f'    mov [rbp - {final_result_offset}], {TEMP_REG_0} ; AdditiveExpression set result\n')


class ShiftExpression(ChainExpression):
    # additive-expression
    # shift-expression << additive-expression
    # shift-expression >> additive-expression

    def __init__(self, compiler, data: list[AdditiveExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'ShiftExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            if self.data[index].opt == '<<':
                result <<= self.gen_asm_results[index]['value']
            elif self.data[index].opt == '>>':
                result >>= self.gen_asm_results[index]['value']

        return result

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            # shift at most 8bit?

            self.write_asm(f'    push rcx\n')
            self.write_asm(f'    mov rcx, [rbp - {result_offset}]\n')
            if self.data[index].opt == '<<':
                self.write_asm(f'    shl {TEMP_REG_0}, cl\n')
            elif self.data[index].opt == '>>':
                self.write_asm(f'    shr {TEMP_REG_0}, cl\n')
            else:
                self.raise_compiler_error(f'wtf')
            self.write_asm(f'    pop rcx\n')

        if set_result:
            self.write_asm(f'    mov [rbp - {final_result_offset}], {TEMP_REG_0} ; ShiftExpression set result\n')


class RelationalExpression(ChainExpression):
    # shift-expression
    # relational-expression < shift-expression
    # relational-expression > shift-expression
    # relational-expression <= shift-expression
    # relational-expression >= shift-expression

    def __init__(self, compiler, data: list[ShiftExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'RelationalExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            if self.data[index].opt == '<':
                if result < self.gen_asm_results[index]['value']:
                    result = 1
                else:
                    result = 0
            elif self.data[index].opt == '>':
                if result > self.gen_asm_results[index]['value']:
                    result = 1
                else:
                    result = 0
            elif self.data[index].opt == '<=':
                if result <= self.gen_asm_results[index]['value']:
                    result = 1
                else:
                    result = 0
            elif self.data[index].opt == '>=':
                if result >= self.gen_asm_results[index]['value']:
                    result = 1
                else:
                    result = 0

        return result

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            label_1_name = f'cmp_label_{self.compiler.item_id}'
            self.compiler.item_id += 1
            label_2_name = f'cmp_label_{self.compiler.item_id}'
            self.compiler.item_id += 1

            if self.data[index].opt == '<':
                '''
                cmp {TEMP_REG_0}, xxx
                jl label_1
                mov {TEMP_REG_0}, 0
                jmp label_2
                label_1:
                    mov {TEMP_REG_0}, 1
                label_2:
                '''

                self.write_asm(f'    cmp {TEMP_REG_0}, [rbp - {result_offset}]\n    jl {label_1_name}\n    mov {TEMP_REG_0}, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov {TEMP_REG_0}, 1\n    {label_2_name}:\n')
            elif self.data[index].opt == '>':
                self.write_asm(f'    cmp {TEMP_REG_0}, [rbp - {result_offset}]\n    jg {label_1_name}\n    mov {TEMP_REG_0}, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov {TEMP_REG_0}, 1\n    {label_2_name}:\n')
            elif self.data[index].opt == '<=':
                self.write_asm(f'    cmp {TEMP_REG_0}, [rbp - {result_offset}]\n    jle {label_1_name}\n    mov {TEMP_REG_0}, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov {TEMP_REG_0}, 1\n    {label_2_name}:\n')
            elif self.data[index].opt == '>=':
                self.write_asm(f'    cmp {TEMP_REG_0}, [rbp - {result_offset}]\n    jge {label_1_name}\n    mov {TEMP_REG_0}, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov {TEMP_REG_0}, 1\n    {label_2_name}:\n')
            else:
                self.raise_compiler_error(f'wtf')

        if set_result:
            self.write_asm(f'    mov [rbp - {final_result_offset}], {TEMP_REG_0} ; RelationalExpression set result\n')


class EqualityExpression(ChainExpression):
    # relational-expression
    # equality-expression == relational-expression
    # equality-expression != relational-expression

    def __init__(self, compiler, data: list[RelationalExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'EqualityExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            if self.data[index].opt == '==':
                if result < self.gen_asm_results[index]['value']:
                    result = 1
                else:
                    result = 0
            elif self.data[index].opt == '!=':
                if result > self.gen_asm_results[index]['value']:
                    result = 1
                else:
                    result = 0

        return result

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            label_1_name = f'cmp_label_{self.compiler.item_id}'
            self.compiler.item_id += 1
            label_2_name = f'cmp_label_{self.compiler.item_id}'
            self.compiler.item_id += 1

            if self.data[index].opt == '==':
                '''
                cmp {TEMP_REG_0}, xxx
                je label_1
                mov {TEMP_REG_0}, 0
                jmp label_2
                label_1:
                    mov {TEMP_REG_0}, 1
                label_2:
                '''

                self.write_asm(f'    cmp {TEMP_REG_0}, [rbp - {result_offset}]\n    je {label_1_name}\n    mov {TEMP_REG_0}, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov {TEMP_REG_0}, 1\n    {label_2_name}:\n')
            elif self.data[index].opt == '!=':
                self.write_asm(f'    cmp {TEMP_REG_0}, [rbp - {result_offset}]\n    jne {label_1_name}\n    mov {TEMP_REG_0}, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov {TEMP_REG_0}, 1\n    {label_2_name}:\n')
            else:
                self.raise_compiler_error(f'wtf')

        if set_result:
            self.write_asm(f'    mov [rbp - {final_result_offset}], {TEMP_REG_0} ; EqualityExpression set result\n')


class AndExpression(ChainExpression):
    # equality-expression
    # and-expression & equality-expression

    def __init__(self, compiler, data: list[EqualityExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'AndExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            result &= self.gen_asm_results[index]['value']

        return result

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            '''
            and {TEMP_REG_0}, xxx
            '''
            self.write_asm(f'    and {TEMP_REG_0}, [rbp - {result_offset}]\n')

        if set_result:
            self.write_asm(f'    mov [rbp - {final_result_offset}], {TEMP_REG_0} ; set result\n')


class ExclusiveOrExpression(ChainExpression):
    # and-expression
    # exclusive-or-expression ^ and-expression

    def __init__(self, compiler, data: list[AndExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'ExclusiveOrExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            result ^= self.gen_asm_results[index]['value']

        return result

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8
            '''
            and {TEMP_REG_0}, xxx
            '''
            self.write_asm(f'    xor {TEMP_REG_0}, [rbp - {result_offset}]\n')

        if set_result:
            self.write_asm(f'    mov [rbp - {final_result_offset}], {TEMP_REG_0} ; ExclusiveOrExpression set result\n')


class InclusiveOrExpression(ChainExpression):
    # exclusive-or-expression
    # inclusive-or-expression | exclusive-or-expression

    def __init__(self, compiler, data: list[ExclusiveOrExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'InclusiveOrExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            result |= self.gen_asm_results[index]['value']

        return result

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            '''
            and {TEMP_REG_0}, xxx
            '''
            self.write_asm(f'    or {TEMP_REG_0}, [rbp - {result_offset}]\n')

        if set_result:
            self.write_asm(f'    mov [rbp - {final_result_offset}], {TEMP_REG_0} ; InclusiveOrExpression set result\n')


class LogicalAndExpression(ChainExpression):
    # inclusive-or-expression
    # logical-and-expression && inclusive-or-expression

    def __init__(self, compiler, data: list[InclusiveOrExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'LogicalAndExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        for index in range(self.data_count):
            if 0 == self.gen_asm_results[index]['value']:
                return 0

        return 1

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # todo use loop in asm
        """
            cmp v1 0
            je cmp_and_fail

            cmp v2 0
            je cmp_and_fail

            ...

            cmp vx 0
            je cmp_and_fail

            mov {TEMP_REG_0}, 1
            jmp cmp_done

            cmp_and_fail:
                mov {TEMP_REG_0}, 0
            cmp_done:
        """

        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        label_1_name = f'cmp_and_fail_{self.compiler.item_id}'
        self.compiler.item_id += 1
        label_2_name = f'cmp_done_{self.compiler.item_id}'
        self.compiler.item_id += 1

        for index in range(0, self.data_count):
            self.write_asm(f'    cmp qword ptr [rbp - {result_offset}], 0\n    je {label_1_name}\n')
            result_offset += 8

        # set result
        if set_result:
            self.write_asm(f'    mov qword ptr [rbp - {final_result_offset}], 1\n    jmp {label_2_name}\n    {label_1_name}:\n')
            self.write_asm(f'        mov qword ptr [rbp - {final_result_offset}], 0\n    {label_2_name}:\n')


class LogicalOrExpression(ChainExpression):
    # logical-and-expression
    # logical-or-expression || logical-and-expression

    def __init__(self, compiler, data: list[LogicalAndExpression]):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'LogicalOrExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        for index in range(self.data_count):
            if 1 == self.gen_asm_results[index]['value']:
                return 1

        return 0

    def sub_items_gen_asm(self, result_offset, final_result_offset, set_result = True):
        # todo use loop in asm
        """
            cmp v1 0
            jne cmp_or_ok

            cmp v2 0
            jne cmp_or_ok

            ...

            cmp vx 0
            jne cmp_or_ok

            mov {TEMP_REG_0}, 0
            jmp cmp_done

            cmp_or_ok:
                mov {TEMP_REG_0}, 1
            cmp_done:
        """

        label_1_name = f'cmp_or_ok_{self.compiler.item_id}'
        self.compiler.item_id += 1
        label_2_name = f'cmp_done_{self.compiler.item_id}'
        self.compiler.item_id += 1

        for index in range(0, self.data_count):
            self.write_asm(f'    cmp qword ptr [rbp - {result_offset}], 0\n    jne {label_1_name}\n')
            result_offset += 8

        if set_result:
            self.write_asm(f'    mov qword ptr [rbp - {final_result_offset}], 0\n    jmp {label_2_name}\n    {label_1_name}:\n')
            self.write_asm(f'        mov qword ptr [rbp - {final_result_offset}], 1\n    {label_2_name}:\n')


class ConditionalExpression(CComponent):
    # logical-or-expression
    # logical-or-expression ? expression : conditional-expression

    def __init__(self, compiler, loe: LogicalOrExpression, exp: Expression, ce):
        super().__init__(compiler)
        self.loe = loe
        self.exp = exp
        self.ce = ce

    def __repr__(self):
        return f'ConditionalExpression {self.loe, self.exp, self.ce}'

    def print_me(self, indent):
        self.print(f'{" " * indent}ConditionalExpression')
        self.loe.print_me(indent + PRINT_INDENT)
        self.exp.print_me(indent + PRINT_INDENT)
        self.ce.print_me(indent + PRINT_INDENT)

    @CComponent.gen_asm_helper
    def gen_asm(self, my_result_offset, set_result = True, need_global_const = False, **kwargs):
        if not self.exp:
            return self.loe.gen_asm(my_result_offset, set_result, need_global_const = need_global_const, **kwargs)
        else:
            self.raise_compiler_error(f'no support yes')
            self.loe.gen_asm(my_result_offset)
            self.write_asm(f'    ; ConditionalExpression test le result\n')
            self.exp.gen_asm()
            self.ce.gen_asm()


class ExpressionStatement(CComponent):
    # expression? ;

    def __init__(self, compiler, exp: Expression):
        super().__init__(compiler)
        self.exp = exp

    def __repr__(self):
        return f'ExpressionStatement {self.exp}'

    def print_me(self, indent):
        self.print(f'{" " * indent}ExpressionStatement')
        self.exp.print_me(indent + PRINT_INDENT)

    @CComponent.gen_asm_helper
    def gen_asm(self):
        if self.exp:
            result_offset = self.stack_alloc(8, 'ExpressionStatement alloc for exp result')

            result = self.exp.gen_asm(result_offset)

            self.stack_free(8, 'ExpressionStatement free exp result')

            return result

        self.raise_compiler_error(f'wtf ExpressionStatement')


class SelectionStatement(CComponent):
    # if ( expression ) statement
    # if ( expression ) statement else statement
    # switch ( expression ) statement

    def __init__(self, compiler, switch = NoObject(), exp: Expression = NoObject(), stmt_1 = NoObject(), stmt_2 = NoObject()):
        super().__init__(compiler)
        self.switch = switch
        self.exp = exp
        self.stmt_1 = stmt_1
        self.stmt_2 = stmt_2

    def __repr__(self):
        return f'SelectionStatement {self.switch} {self.exp} {self.stmt_1} {self.stmt_2}'

    def print_me(self, indent):
        self.print(f'{" " * indent}SelectionStatement {self.switch}')
        self.print(f'{" " * indent}{self.exp}')
        self.print(f'{" " * indent}{self.stmt_1}')
        self.print(f'{" " * indent}{self.stmt_2}')

    @CComponent.gen_asm_helper
    def gen_asm(self):
        if not self.switch:
            result_offset = self.stack_alloc(8, 'SelectionStatement for exp result')

            self.exp.gen_asm(result_offset)

            label_1_name = f'if_not_{self.compiler.item_id}'
            self.compiler.item_id += 1

            label_2_name = f'if_over_{self.compiler.item_id}'
            self.compiler.item_id += 1

            '''
            cmp exp, 0
            je if_not
            stmt_1
            jmp if_over
            if_not:
                stmt_2
            if_over:
            '''

            self.write_asm(f'    cmp qword ptr [rbp - {result_offset}], 0\n    je {label_1_name}\n')
            self.stmt_1.gen_asm()
            self.write_asm(f'    jmp {label_2_name}\n')
            self.write_asm(f'    {label_1_name}:\n')
            if self.stmt_2:
                self.stmt_2.gen_asm()
            self.write_asm(f'    {label_2_name}:\n')

            self.stack_free(8, 'SelectionStatement for exp result')

            return

        self.raise_compiler_error(f'wtf SelectionStatement')


class IterationStatement(CComponent):
    # while ( expression ) statement
    # do statement while ( expression ) ;
    # for ( expression? ; expression? ; expression? ) statement
    # for ( declaration expression? ; expression? ) statement

    def __init__(self, compiler, loop_type: int, declaration = NoObject(), exp_1: Expression = NoObject(), exp_2: Expression = NoObject(), exp_3: Expression = NoObject(), stmt = NoObject()):
        super().__init__(compiler)
        self.loop_type = loop_type
        self.declaration = declaration
        self.exp_1 = exp_1
        self.exp_2 = exp_2
        self.exp_3 = exp_3
        self.stmt = stmt

    def __repr__(self):
        return f'IterationStatement {self.loop_type} {self.declaration} {self.exp_1} {self.exp_2} {self.exp_3} {self.stmt}'

    def print_me(self, indent):
        self.print(f'{" " * indent}IterationStatement loop_type = {self.loop_type}')
        self.declaration.print_me(indent + PRINT_INDENT)
        self.exp_1.print_me(indent + PRINT_INDENT)
        self.exp_2.print_me(indent + PRINT_INDENT)
        self.exp_3.print_me(indent + PRINT_INDENT)
        self.stmt.print_me(indent + PRINT_INDENT)

    @CComponent.gen_asm_helper
    def gen_asm(self):
        self.write_asm(f'\n    ; IterationStatement gen_asm\n')

        self.enter_scope()

        if self.loop_type == 0: # while
            '''
            loop_start:
            exp
            cmp exp, 0
            je loop_over
            stmt
            jmp loop_start
            
            loop_over:
            '''

            result_offset = self.stack_alloc(8, 'IterationStatement for exp result')

            label_1_name = f'loop_start_{self.compiler.item_id}'
            self.compiler.item_id += 1

            label_2_name = f'loop_over_{self.compiler.item_id}'
            self.compiler.item_id += 1

            self.write_asm(f'    {label_1_name}:\n')
            self.exp_1.gen_asm(result_offset)
            self.write_asm(f'    cmp qword ptr [rbp - {result_offset}], 0\n    je {label_2_name}\n')
            self.stmt.gen_asm()
            self.write_asm(f'    jmp {label_1_name}\n')
            self.write_asm(f'    {label_2_name}:\n')

            self.stack_free(8, 'IterationStatement for exp result')
        elif self.loop_type == 1: # do while
            '''
            loop_start:
            stmt
            exp
            cmp exp, 0
            je loop_over
            jmp loop_start
            
            loop_over:
            '''

            result_offset = self.stack_alloc(8, 'IterationStatement for exp result')

            label_1_name = f'loop_start_{self.compiler.item_id}'
            self.compiler.item_id += 1

            label_2_name = f'loop_over_{self.compiler.item_id}'
            self.compiler.item_id += 1

            self.write_asm(f'    {label_1_name}:\n')
            self.stmt.gen_asm()
            self.exp_1.gen_asm(result_offset)
            self.write_asm(f'    cmp qword ptr [rbp - {result_offset}], 0\n    je {label_2_name}\n')
            self.write_asm(f'    jmp {label_1_name}\n')
            self.write_asm(f'    {label_2_name}:\n')

            self.stack_free(8, 'IterationStatement for exp result')
        elif self.loop_type == 2: # for loop
            '''
            declaration or exp_1
            
            loop_start:
            exp_2
            cmp exp_2, 0
            je loop_over
            stmt
            exp_3
            jmp loop_start
            
            loop_over:
            '''

            if self.declaration:
                self.declaration.gen_asm()
            elif self.exp_1:
                self.exp_1.gen_asm()

            result_offset = self.stack_alloc(8, 'IterationStatement alloc for exp result')

            label_1_name = f'loop_start_{self.compiler.item_id}'
            self.compiler.item_id += 1

            label_2_name = f'loop_over_{self.compiler.item_id}'
            self.compiler.item_id += 1

            self.write_asm(f'    {label_1_name}:\n')

            if self.exp_2:
                self.exp_2.gen_asm(result_offset)
                self.write_asm(f'    cmp qword ptr [rbp - {result_offset}], 0 ; for loop compare\n    je {label_2_name}\n')
            else:
                # forever
                pass

            self.stmt.gen_asm()

            if self.exp_3:
                self.exp_3.gen_asm(result_offset)

            self.write_asm(f'    jmp {label_1_name}\n')
            self.write_asm(f'    {label_2_name}:\n')

            self.stack_free(8, 'IterationStatement free exp result')
        else:
            raise

        self.leave_scope(free_stack_variables = True)


class JumpStatement(CComponent):
    # goto identifier ;
    # continue ;
    # break ;
    # return expression? ;

    def __init__(self, compiler, cmd, idf: Identifier = NoObject(), exp: Expression = NoObject()):
        super().__init__(compiler)
        self.cmd = cmd
        self.idf = idf
        self.exp = exp

    def __repr__(self):
        return f'JumpStatement {self.cmd, self.idf, self.exp}'

    def print_me(self, indent):
        self.print(f'{" " * indent}JumpStatement')
        if self.cmd == 'goto':
            self.print(f'{" " * (indent + PRINT_INDENT)}goto {self.idf.name}')
        elif self.cmd == 'return':
            self.exp.print_me(indent + PRINT_INDENT)
        else:
            self.print(f'{" " * (indent + PRINT_INDENT)}{self.cmd}')

    @CComponent.gen_asm_helper
    def gen_asm(self, my_result_offset = None):
        if self.cmd == 'goto':
            # label must in current function
            self.write_asm(f'    jmp {self.idf.name}\n')
        elif self.cmd == 'continue':
            self.write_asm(f'    ;continue\n')
        elif self.cmd == 'break':
            self.write_asm(f'    ;break\n')
        elif self.cmd == 'return':
            if self.exp:
                # set return value
                result_offset = self.stack_alloc(8, 'JumpStatement for exp result')
                data = self.exp.gen_asm(result_offset) # todo: add result_reg?

                if 'lv_address' in data:
                    self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {result_offset}] ; get lv_address\n')
                    self.write_asm(f'    mov rax, [{TEMP_REG_4}] ; set return value\n')
                else:
                    self.write_asm(f'    mov rax, [rbp - {result_offset}] ; set return value\n')

                self.stack_free(8, 'JumpStatement for exp result')
            else:
                self.write_asm(f'    xor rax, rax ; set return value = 0\n')

            self.write_asm(f'\n    leave\n    ret\n')
        else:
            self.raise_compiler_error(f'JumpStatement unknow {self.cmd}')


class Statement(CComponent):
    # labeled-statement
    # compound-statement
    # expression-statement
    # selection-statement
    # iteration-statement
    # jump-statement

    def __init__(self, compiler, bil: list):
        super().__init__(compiler)
        self.bil = bil

    def __repr__(self):
        return f'Statement {self.bil}'

    def print_me(self, indent):
        self.print(f'{" " * indent}Statement len = {len(self.bil)}')
        for bi in self.bil:
            if hasattr(bi, 'print_me'):
                bi.print_me(indent + PRINT_INDENT)
            else:
                self.print(f'{" " * (indent + PRINT_INDENT)}{bi}')


class LabeledStatement(CComponent):
    # identifier : statement
    # case constant-expression : statement
    # default : statement

    def __init__(self, compiler, data: list):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'LabeledStatement {self.data}'

    def print_me(self, indent):
        self.print(f'{" " * indent}LabeledStatement len = {self.data_count}')
        for item in self.data:
            if hasattr(item, 'print_me'):
                item.print_me(indent + PRINT_INDENT)
            else:
                self.print(f'{" " * (indent + PRINT_INDENT)}{item}')

    @CComponent.gen_asm_helper
    def gen_asm(self):
        if self.data[0] not in ['case', 'default']:
            self.write_asm(f'    {self.data[0].name}:\n')


class InitDeclarator(CComponent):
    # declarator
    # declarator = initializer

    def __init__(self, compiler, dtr, init):
        super().__init__(compiler)
        self.dtr = dtr
        self.init = init

    def __repr__(self):
        return f'InitDeclarator {self.dtr} {self.init}'

    def print_me(self, indent):
        self.print(f'{" " * indent}InitDeclarator')
        self.print(f'{" " * (indent + PRINT_INDENT)}dtr = {self.dtr}')
        self.init.print_me(indent + PRINT_INDENT)


class Declaration(CComponent):
    # declaration-specifiers init-declarator-list? ;

    # const int              a, b, *p, c = 666     ;
    # struct S1{int a;}      s1, s2 = {...}        ;
    # struct S2{int a, b;}                         ;
    # struct S3              s1, s2                ;
    # struct {int a, b;}     s1, s2                ;

    def __init__(self, compiler, dss, idl: list[InitDeclarator], global_scope = False):
        super().__init__(compiler)
        self.dss = dss
        self.idl = idl
        self.global_scope = global_scope

    def __repr__(self):
        return f'\nDeclaration {self.dss} {self.idl}'

    def get_text(self, indent):
        return f'\n{" " * indent}Declaration {self.dss} {self.idl}'

    def print_me(self, indent = 0):
        self.print(f'{" " * indent}Declaration')
        self.print(f'{" " * (indent + PRINT_INDENT)}dss')
        for k in self.dss:
            self.print(f'{" " * (indent + 8)}{k} = {self.dss[k]}')
        self.print(f'{" " * (indent + PRINT_INDENT)}idl')
        if self.idl:
            for idtr in self.idl:
                idtr.print_me(indent + 8)
        else:
            self.print(f'{" " * (indent + 8)}NoObject()')

    @CComponent.gen_asm_helper
    def gen_asm(self, global_scope = False):
        # if typedef
        if self.dss['storage_class_specifier'] == 'typedef':
            for idtr in self.idl:
                if idtr.init:
                    self.raise_code_error(f'can not do init on typedef')

                '''
                Declaration
                    dss
                        storage_class_specifier = Identifier(typedef)
                        type_specifier = TypeSpecifier [int float ... or StructUnion or Typedef]
                        type_qualifier = set()
                        function_spec = None
                        alignment_spec = None
                    idl
                        InitDeclarator
                          dtr = [[], {'name': 'WTF'}]
                          NoObject
                        InitDeclarator
                          dtr = [[], {'name': 'WTFFffff'}]
                          NoObject
                '''

                dss = copy.deepcopy(self.dss)
                dtr = copy.deepcopy(idtr.dtr)

                self.print_me()

                if isinstance(dss['type_specifier'].type_data, Typedef):
                    # if Typedef of Typedef. merge
                    dss['type_specifier'].type_data.print_me()
                    type_name = dss['type_specifier'].type_data.name

                    scope_item = self.get_scope_item(type_name)

                    if scope_item is None:
                        self.raise_code_error(f'[{type_name}] unknown')

                    if 'typedef' not in scope_item:
                        self.raise_code_error(f'[{type_name}] unknown')

                    self.print_red(scope_item)
                    scope_item['data'].print_me()

                    new_scope_item = copy.deepcopy(scope_item)

                    # merge
                    new_scope_item['data'].dss['type_qualifier'].update(dss['type_qualifier'])
                    if len(dtr[0]) > 0: # pointer
                        new_scope_item['data'].dtr[0] = dtr[0] + new_scope_item['data'].dtr[0]

                    new_scope_item['name'] = idtr.dtr[1]['name']
                else:
                    # just save this typedef info to scope
                    new_scope_item = {'name':idtr.dtr[1]['name'],
                                  'typedef':1,
                                  'data':Typedef(self.compiler, dss, dtr)}

                self.add_to_scope(new_scope_item)

            return

        data_size = 8  # 8 bytes for all normal types for now
        data_type = self.dss['type_specifier'].type_data

        # if Typedef, merge Typedef to current. like expand the Typedef data.
        if isinstance(data_type, Typedef):
            self.print_red(data_type)
            data_type.print_me()
            self.print_me()

            scope_typedef = self.get_scope_item(data_type.name)
            if scope_typedef is None:
                self.raise_code_error(f'[{data_type.name}] not defined')

            if 'typedef' not in scope_typedef:
                self.raise_code_error(f'[{data_type.name}] not defined')

            typedef = scope_typedef['data']

            self.print_red(f'{typedef = }')

            self.dss['type_qualifier'].update(typedef.dss['type_qualifier'])
            self.dss['type_specifier'] = typedef.dss['type_specifier']

            # merge pointer
            if len(typedef.dtr[0]) > 0:
                for idtr in self.idl:
                    idtr.dtr[0] += typedef.dtr[0]

            data_type = self.dss['type_specifier'].type_data

        if isinstance(data_type, StructUnion):
            self.print_red(data_type)
            data_type.gen_struct_data()
            data_size = data_type.size
            data_type = data_type.name

        #
        # todo: make new name

        if self.idl:
            for item in self.idl:
                self.print_red(f'item = {item}')
                self.print_red(item.dtr[1])

                dtr = item.dtr[1]
                name = dtr['name']

                if 'array_data' not in dtr and 'function_data' not in dtr:
                    scope_item = {'lv':1, 'name':name, 'data_type':data_type}

                    # if const
                    if 'const' in self.dss['type_qualifier']:
                        scope_item['const'] = 1

                    # if pointer
                    # * = [[]]
                    # * *const * = [[], ['const'], []]
                    if len(item.dtr[0]) > 0:
                        data_size = 8
                        scope_item['pointer_data'] = item.dtr[0]

                    scope_item['size'] = data_size

                    if global_scope:
                        scope_item['global'] = 1
                    else:
                        # alloc for variable
                        offset = self.compiler.add_function_stack_offset(data_size)
                        self.write_asm(f'    sub rsp, {data_size} ; Declaration var {data_type} {name} offset = {offset}\n')
                        scope_item['offset'] = offset

                    if global_scope:
                        if isinstance(item.init, AssignmentExpression):
                            # todo: global function pointer ...
                            init_data = item.init.gen_asm(None, need_global_const = True)
                            self.print_red(init_data)
                            if 'value' in init_data:
                                scope_item['value'] = init_data['value']

                        self.add_to_scope(scope_item)

                        if data_type in ['int']:
                            value = 0
                            if 'value' in scope_item:
                                value = scope_item["value"]
                            self.write_asm_data(f'{name} qword {value}\n')
                        else:
                            # struct
                            self.write_asm_data(f'{name} byte {data_size} dup (0)\n')
                    else:
                        self.add_to_scope(scope_item)

                        if isinstance(item.init, AssignmentExpression):
                            item.init.gen_asm(scope_item['offset'])
                elif 'array_data' in dtr:
                    self.write_asm(f'    ; Declaration array {data_type} {name}\n')

                    array_size = 1
                    ranks = []
                    dim = dtr['array_data']['dim']

                    for rank_exp in dtr['array_data']['ranks']:
                        # result_offset = self.stack_alloc(8, f'Declaration array {data_type} {name} for exp')

                        result = rank_exp.gen_asm(None, set_result = False, need_global_const = True)

                        # self.stack_free(8, f'Declaration array {data_type} {name} for exp')

                        if 'value' not in result:
                            self.raise_code_error(f'array rank must be const')

                        array_size *= result['value']
                        ranks.append(result['value'])

                    if global_scope:
                        scope_item = {'data_type':data_type, 'size':data_size * array_size, 'name':name, 'global':1, 'array_data':{'dim':dim, 'ranks':ranks}}
                        self.add_to_scope(scope_item)

                        # a byte 10000 dup (0)
                        self.write_asm_data(f'{name} byte {data_size * array_size} dup (0) ; global {data_type} array. {data_size} * {array_size}\n')
                    else:
                        # array on stack
                        offset = self.compiler.add_function_stack_offset(data_size * array_size)
                        self.write_asm(f'    sub rsp, {data_size * array_size} ; Declaration local array {data_type} {name} offset = {offset}\n')

                        scope_item = {'data_type':data_type, 'size':data_size * array_size, 'name':name, 'offset':offset, 'array_data':{'dim':dim, 'ranks':ranks}}
                        self.add_to_scope(scope_item)
                elif 'function_data' in dtr:  # function declaration
                    self.write_asm_data(f'extern {name}:proc\n')

                    # ([], {'name': 'print', 'function_data': ([((TypeSpecifier char, []), ([[]], {'name': 's'}))], None)})
                    self.print_red(f'{item = }')

                    args_data = []
                    if len(dtr['function_data']) > 0:
                        for arg in dtr['function_data'][0]:
                            arg_info = {'data_type':arg[0]['type_specifier'].type_data, 'name':arg[1][1]['name']}
                            if len(arg[1][0]) > 0:
                                arg_info['pointer_data'] = arg[1][0]

                            args_data.append(arg_info)

                        if dtr['function_data'][1] == '...':
                            args_data.append('...')

                    function_data = {'data_type':self.dss['type_specifier'].type_data, 'args':args_data}
                    self.add_to_scope({'name':name, 'function_data':function_data})

        return


class CompoundStatement(CComponent):
    # { block-item-list }

    def __init__(self, compiler, bil: list[Declaration | Statement]):
        super().__init__(compiler)
        self.bil = bil

    def __repr__(self):
        return f'CompoundStatement {self.bil}'

    def print_me(self, indent):
        self.print(f'{" " * indent}CompoundStatement len = {len(self.bil)}')
        for bi in self.bil:
            if hasattr(bi, 'print_me'):
                bi.print_me(indent + PRINT_INDENT)
            else:
                self.print(f'{" " * (indent + PRINT_INDENT)}{bi}')

    @CComponent.gen_asm_helper
    def gen_asm(self):
        self.enter_scope()

        for bi in self.bil:
            # Declaration or statement
            bi.gen_asm()

        self.leave_scope(free_stack_variables = True)


class FunctionDefinition(CComponent):
    # declaration-specifiers declarator declaration-list? compound-statement

    # declaration-list? is unusual, replace with
    # declaration-specifiers declarator compound-statement

    def __init__(self, compiler, dss, declarator, cs: CompoundStatement, global_scope = False):
        super().__init__(compiler)
        self.dss = dss
        self.declarator = declarator
        # self.dl = dl
        self.cs = cs

        self.name = self.declarator[1]['name']

        self.global_scope = global_scope

        # use offset to trace function stack usage
        # can be used as variable location at compile time
        # can be used to evaluate stack alignment
        self.offset = 0

    def __repr__(self):
        return f'\nFunctionDefinition {self.dss} {self.declarator} {self.cs}'

    def get_text(self, indent):
        return f'\n{" " * indent}FunctionDefinition {self.dss} {self.declarator} {self.cs}'

    def print_me(self, indent):
        self.print(f'{" " * indent}FunctionDefinition')
        self.print(f'{" " * (indent + PRINT_INDENT)}dss')
        for k in self.dss:
            self.print(f'{" " * (indent + 8)}{k} = {self.dss[k]}')

        self.print(f'{" " * (indent + PRINT_INDENT)}declarator = {self.declarator}')
        # self.print(f'{" " * (indent + PRINT_INDENT)}{self.dl}')
        self.cs.print_me(indent + PRINT_INDENT)

    @CComponent.gen_asm_helper
    def gen_asm(self, global_scope = False):
        '''
        int f(int g, int * wtf, const int yyy)

        dss =
          TypeSpecifier
            int
          []

        declarator = ([],
            {'name': 'f',
                'function_data': (
                [
                    (
                        (TypeSpecifier int, []),
                        ([], {'name': 'g'})
                    ),
                    (
                        (TypeSpecifier int, []),
                        ([[]], {'name': 'wtf'})
                    ),
                    (
                        (TypeSpecifier int, [('tq', 'const')]),
                        ([], {'name': 'yyy'})
                    )
                ],
                None) # for ...
            }
        )
        '''

        self.print_red(f'self.declarator = {pprint.pformat(self.declarator)}')

        # stack after call

        #  n * 8 + 8     arg n 8bytes
        #                ...
        #  24            arg 2 8bytes
        #  16            arg 1 8bytes
        #  8             return address
        #  0             old rbp           <- rsp = rbp

        # make function_data
        offset = -16 # - is up
        args_data = []
        if len(self.declarator[1]['function_data']) > 0:
            for arg in self.declarator[1]['function_data'][0]:
                arg_info = {'lv':1, 'offset':offset, 'data_type':arg[0]['type_specifier'].type_data, 'name':arg[1][1]['name']}
                if len(arg[1][0]) > 0:
                    arg_info['pointer_data'] = arg[1][0]

                args_data.append(arg_info)
                offset -= 8

            if self.declarator[1]['function_data'][1] == '...':
                args_data.append('...')

        function_data = {'data_type':self.dss['type_specifier'].type_data, 'args':args_data}

        self.print_red(function_data)

        # enter function
        self.compiler.current_function = self

        # make new scope
        self.enter_scope()

        # add self tp scope(can call self)
        scope_item = {'name':self.name, 'function_data':function_data}

        self.add_to_scope(copy.deepcopy(scope_item))
        for arg in args_data:
            self.add_to_scope(copy.deepcopy(arg), add_to_variable_stack_size = False)

        self.write_asm(f'{self.name} proc ; FunctionDefinition\n')

        # Standard Entry Sequence
        self.write_asm(f'    push rbp ; Standard Entry Sequence\n    mov rbp, rsp ; Standard Entry Sequence\n')

        # microsoft abi.
        # 16-aligned before call.
        # 16-aligned after push rbp.

        # 16 aligned -----
        #     8 bytes return address
        #     8 bytes rbp              <- rsp = rbp (self.offset = 0)

        # self.offset = 0 by default
        # use self.offset to trace function stack usage

        self.cs.gen_asm()

        # force return
        self.write_asm(f'\n    leave ; force return\n    ret 0; force return\n')

        self.write_asm(f'{self.name} endp\n\n')

        self.leave_scope(free_stack_variables = False) # function will free stack automatically

        # add to scope
        self.add_to_scope(copy.deepcopy(scope_item))


class TranslationUnit(CComponent):
    def __init__(self, compiler, eds: list[Declaration | FunctionDefinition]):
        self.eds = eds
        super().__init__(compiler)

    def __str__(self):
        return 'wtf'

    def __repr__(self):
        return f'TranslationUnit {self.eds}'

    def get_text(self, indent = 0):
        return f'{" " * indent}TranslationUnit {[item.get_text(indent + 2) for item in self.eds]}'

    def print_me(self, indent = 0):
        self.print(f'\n{" " * indent}TranslationUnit len = {len(self.eds)}')
        for ed in self.eds:
            ed.print_me(indent + PRINT_INDENT)

    @CComponent.gen_asm_helper
    def gen_asm(self):
        self.write_asm(f'\n    .code\n\n')

        for ed in self.eds:
            ed.gen_asm(global_scope = True)

        self.write_asm(f'end')