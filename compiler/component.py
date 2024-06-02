import pprint
from compiler.tool import CompilerError, CodeError, print_red, print_yellow, print_green, print_orange, PRINT_INDENT
import copy

TEMP_REG_0 = 'r10'
TEMP_REG_1 = 'r11'
TEMP_REG_2 = 'r12'
TEMP_REG_3 = 'r13'
TEMP_REG_4 = 'r14'
TEMP_REG_5 = 'r15'


class CComponent:
    def __init__(self, compiler):
        self.compiler = compiler
        self.lineno = compiler.current_lineno

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
        print(f'{self.__class__.__name__} {msg} scope_level = {len(self.compiler.scopes)} scope = ')
        pprint.pprint(self.compiler.scopes[-1], indent = 4)

    def get_scope_item(self, name):
        item = self.compiler.scopes[-1].current.get(name, None)
        if item is None:
            item = self.compiler.scopes[-1].outer.get(name, None)

        return item

    def add_to_scope(self, item):
        if item['name'] in self.compiler.scopes[-1].current:
            self.raise_code_error(f'[{item["name"]}] already defined')

        self.compiler.scopes[-1].current[item['name']] = item

        if item['type'] in ['var', 'array']:
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


class NoObject:
    def __init__(self, compiler = None):
        self.compiler = compiler

    def __repr__(self):
        return f'NoObject'

    def __bool__(self):
        return False

    def print_me(self, indent = 0):
        print(f'{" " * indent}NoObject')

    def __next__(self):
        return None

    def gen_asm(self, result_offset):
        raise CompilerError(f'NoObject gen_asm')


class TranslationUnit(CComponent):
    def __init__(self, compiler, eds: list):
        self.eds = eds
        super().__init__(compiler)

    def __str__(self):
        return 'wtf'

    def __repr__(self):
        return f'TranslationUnit {self.eds}'

    def get_text(self, indent = 0):
        return f'{" " * indent}TranslationUnit {[item.get_text(indent + 2) for item in self.eds]}'

    def print_me(self, indent = 0):
        print(f'\n{" " * indent}TranslationUnit len = {len(self.eds)}')
        for ed in self.eds:
            ed.print_me(indent + PRINT_INDENT)

    def gen_asm(self):
        self.write_asm(f'\n    .code\n\n')

        for ed in self.eds:
            ed.gen_asm(global_scope = True)

        self.write_asm(f'end')


class FunctionDefinition(CComponent):
    # declaration-specifiers declarator declaration-list? compound-statement

    # declaration-list? is unusual, replace with
    # declaration-specifiers declarator compound-statement

    def __init__(self, compiler, dss, declarator, cs, global_scope = False):
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
        print(f'{" " * indent}FunctionDefinition')
        print(f'{" " * (indent + PRINT_INDENT)}dss')
        for ds in self.dss:
            # if bi.hasattr('print_me'):
            if hasattr(ds, 'print_me'):
                ds.print_me(indent + 8)
            else:
                print(f'{" " * (indent + 8)}{ds}')

        print(f'{" " * (indent + PRINT_INDENT)}{self.declarator}')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.dl}')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.cs}')
        self.cs.print_me(indent + PRINT_INDENT)

    def gen_asm(self, global_scope = False):
        # for ds in self.dss:
        #     ds.gen_asm(f)

        # enter function
        self.compiler.current_function = self

        # make new scope
        self.enter_scope()

        # add self tp scope(can call self)
        self.add_to_scope({'name':self.name, 'type':'function'})

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
        self.write_asm(f'\n    leave ; force return\n    ret ; force return\n')

        self.write_asm(f'{self.name} endp\n\n')

        self.leave_scope(free_stack_variables = False) # function will free stack automatically

        # add to scope
        self.add_to_scope({'name':self.name, 'type':'function'})


class Declaration(CComponent):
    # declaration-specifiers init-declarator-list? ;

    # const int              a, b, *p, c = 666     ;
    # struct S1{int a;}      s1, s2 = {...}        ;
    # struct S2{int a, b;}                         ;
    # struct S3              s1, s2                ;
    # struct {int a, b;}     s1, s2                ;

    def __init__(self, compiler, dss, idl, global_scope = False):
        super().__init__(compiler)
        self.dss = dss
        self.idl = idl
        self.global_scope = global_scope

    def __repr__(self):
        return f'\nDeclaration {self.dss} {self.idl}'

    def get_text(self, indent):
        return f'\n{" " * indent}Declaration {self.dss} {self.idl}'

    def print_me(self, indent = 0):
        print(f'{" " * indent}Declaration')
        # print(f'{" " * (indent + PRINT_INDENT)}ds\n{" " * (indent + 8)}{self.ds}')
        print(f'{" " * (indent + PRINT_INDENT)}dss')
        for ds in self.dss:
            if hasattr(ds, 'print_me'):
                ds.print_me(indent + 8)
            else:
                print(f'{" " * (indent + 8)}{ds}')
        print(f'{" " * (indent + PRINT_INDENT)}idl')
        if self.idl:
            for idtr in self.idl:
                idtr.print_me(indent + 8)
        else:
            print(f'{" " * (indent + 8)}NoObject()')

    def gen_asm(self, global_scope = False):
        data_type = self.dss[0].type_data

        if isinstance(data_type, StructUnion):
            data_type.gen_struct_data()

        # todo: make new name
        # todo: global init/assignment/array
        if global_scope:
            #if not self.idl: # must struct for me

            # 8 bytes for all normal types for now
            data_size = 8
            if isinstance(data_type, StructUnion):
                print_red(data_type)
                data_size = data_type.size
                data_type = data_type.name

            if self.idl:
                for item in self.idl:
                    if not item.dtr[0]:
                        name = item.dtr[1]['name']
                        tp = item.dtr[1]['type']

                        if tp == 'var':
                            # print_red(self.dss)
                            # print_red(item)

                            is_const = False
                            for dss_item in self.dss[1]: # check const
                                if dss_item[0] == 'tq' and dss_item[1] == 'const':
                                    is_const = True

                            scope_item = {'type':tp, 'name':name, 'data_type':data_type, 'global':1, 'value':0}
                            if is_const:
                                scope_item['const'] = 1

                            if isinstance(item.init, AssignmentExpression):
                                init_data = item.init.gen_asm(None, need_global_const = True)
                                print_red(init_data)
                                if init_data['type'] == 'const':
                                    scope_item['value'] = init_data['value']

                            self.add_to_scope(scope_item)

                            if data_type in ['int']:
                                self.write_asm_data(f'{name} qword {scope_item["value"]}\n')
                            else:
                                # struct
                                self.write_asm_data(f'{name} byte {data_size} dup (0)\n')

                            continue

                        elif tp == 'array':
                            # a byte 10000 dup (0)

                            self.write_asm(f'    ; Declaration array {data_type} {name}\n')

                            array_size = 1
                            ranks = []

                            for rank_exp in item.dtr[1]['array_data']['ranks']:
                                # print_red(f'{rank_exp = }')

                                result = rank_exp.gen_asm(None, set_result = False, need_global_const = True)
                                if result['type'] != 'const':
                                    self.raise_code_error(f'array rank must be const')

                                array_size *= result['value']
                                ranks.append(result['value'])

                            scope_item = {'type':tp, 'data_type':data_type, 'size':data_size * array_size, 'name':name, 'global':1, 'dim':item.dtr[1]['array_data']['dim'], 'ranks':ranks}
                            self.add_to_scope(scope_item)

                            self.write_asm_data(f'{name} byte {data_size * array_size} dup (0) ; {data_type} array. {data_size} * {array_size}\n')
                            continue
                        elif tp == 'function':
                            self.write_asm_data(f'extern {name}:proc\n')
                            self.add_to_scope({'type':tp, 'name':name})
                            continue
                        else:
                            self.raise_code_error(f'Declaration unknown type {item.dtr}')

                    self.write_asm_data(f'    ; Declaration\n')
            else:
                self.raise_code_error(f'need variable')
        else:
            if data_type in ['int'] or isinstance(data_type, StructUnion):

                # 8 bytes for all normal types for now
                data_size = 8
                if isinstance(data_type, StructUnion):
                    print_red(data_type)
                    data_size = data_type.size
                    data_type = data_type.name

                for item in self.idl:
                    name = item.dtr[1]['name']
                    tp = item.dtr[1]['type']

                    if tp == 'var':  # declaration
                        # print(item.dtr[1][1])

                        # alloc for variable
                        offset = self.compiler.add_function_stack_offset(data_size)
                        self.write_asm(f'    sub rsp, {data_size} ; Declaration var {data_type} {name} offset = {offset}\n')

                        scope_item = {'type':'var', 'data_type':data_type, 'name':name, 'offset':offset, 'size':data_size}

                        if item.dtr[0]:  # pointer
                            scope_item['type'] = 'pointer'
                            scope_item['pointer_data'] = item.dtr[0]
                            # * = [[]]
                            # * *const * = [[], ['const'], []]

                        self.add_to_scope(scope_item)

                        # print_red(f'{name} item.init = {item.init}')
                        if isinstance(item.init, AssignmentExpression):
                            item.init.gen_asm(scope_item['offset'])
                            #item.init.gen_asm(need_global_const = True)

                    elif tp == 'array':
                        self.write_asm(f'    ; Declaration array {data_type} {name}\n')

                        # print_red(f'array data {item.dtr[1]["array_data"]}')
                        array_size = 1
                        ranks = []

                        for rank_exp in item.dtr[1]['array_data']['ranks']:
                            # print_red(f'{rank_exp = }')

                            result_offset = self.stack_alloc(8, f'Declaration array {data_type} {name} for exp')

                            result = rank_exp.gen_asm(result_offset, set_result = False)

                            self.stack_free(8, f'Declaration array {data_type} {name} for exp')

                            if result['type'] != 'const':
                                self.raise_code_error(f'array rank must be const')

                            array_size *= result['value']
                            ranks.append(result['value'])

                        # alloc for array
                        offset = self.compiler.add_function_stack_offset(data_size * array_size)
                        self.write_asm(f'    sub rsp, {data_size * array_size} ; Declaration array {data_type} {name} offset = {offset}\n')

                        scope_item = {'type':'array', 'data_type':data_type, 'size':data_size * array_size, 'name':name, 'offset':offset, 'dim':item.dtr[1]['array_data']['dim'], 'ranks':ranks}
                        self.add_to_scope(scope_item)
            elif isinstance(data_type, StructUnion):
                for item in self.idl:
                    name = item.dtr[1]['name']

                    print_red(item)
                    print_red(data_type.name)


                    raise
            else:
                raise CompilerError(f'no support for [{data_type}]')


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
        print(f'{" " * indent}TypeSpecifier')
        if hasattr(self.type_data, 'print_me'):
            self.type_data.print_me(indent + PRINT_INDENT)
        else:
            print(f'{" " * (indent + PRINT_INDENT)}{self.type_data}')


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
        self.tp = tp  # struct or union
        self.name = name
        self.decls = decls

        self.size = None
        self.members = {}

    def __repr__(self):
        return f'StructUnion {self.name} {self.decls} size = {self.size}'

    def print_me(self, indent = 0):
        print(f'{" " * indent}{self.tp}')
        print(f'{" " * (indent + PRINT_INDENT)}name = {self.name}')
        if self.decls:
            for decl in self.decls:
                # print_red(f'decl = {decl}')
                if hasattr(decl, 'print_me'):
                    decl.print_me(indent + PRINT_INDENT)
                else:
                    print(f'{" " * (indent + PRINT_INDENT)}{decl}')
        else:
            print(f'{" " * (indent + PRINT_INDENT)}NoObject()')

    def gen_asm(self):
        self.gen_struct_data()

    def gen_struct_data(self):
        print(f'gen_struct_data type = {self.tp}')

        if self.tp == 'struct':
            self.print_me()

            if self.decls: # case 1 case 2
                # gen data

                offset = 0

                for decl in self.decls:
                    print_red(decl)
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
                                if struct['type'] != 'struct':
                                    self.raise_code_error(f'[{item.type_data.name}] is not struct')
                                #print_red(struct)
                                print_red(f'item = {item}')
                                #raise
                                ts = struct
                            else:
                                self.raise_code_error(f'no support for type [{item.type_data}]')

                    for item in decl[1]:
                        print_red(item) # (([], {'type': 'var', 'name': 'a'}), None)

                        array_size = 1
                        ranks = []
                        dim = 0
                        if item[0][1]['type'] == 'array':
                            dim = item[0][1]['array_data']['dim']
                            for rank_exp in item[0][1]['array_data']['ranks']:
                                # print_red(f'{rank_exp = }')

                                result = rank_exp.gen_asm(None, set_result = False, need_global_const = True)
                                if result['type'] != 'const':
                                    self.raise_code_error(f'array rank must be const')

                                array_size *= result['value']
                                ranks.append(result['value'])

                        name = item[0][1]['name']

                        # c struct has no initializer(default value)
                        # take ([], {'type': 'var', 'name': 'a'})

                        # print_red(f'ts = {ts}')
                        # print_red(f'item = {item}')

                        if ts in ['int']:
                            member_data = copy.deepcopy(item[0][1])
                            member_data['data_type'] = ts
                            member_data['pointer_data'] = copy.deepcopy(item[0][0])
                            member_data['offset'] = offset

                            if item[0][1]['type'] == 'array':
                                member_data['size'] = 8 * array_size
                                member_data['ranks'] = ranks
                                member_data['dim'] = dim
                                member_data.pop('array_data')
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

                            member_data = copy.deepcopy(item[0][1])
                            member_data['data_type'] = ts['name']
                            member_data['pointer_data'] = copy.deepcopy(item[0][0])
                            member_data['offset'] = offset

                            if item[0][1]['type'] == 'array':
                                member_data['size'] = ts['size'] * array_size
                                member_data['ranks'] = ranks
                                member_data['dim'] = dim
                                member_data.pop('array_data')
                            else:
                                member_data['size'] = ts['size']

                            self.members[name] = member_data

                            offset += member_data['size']
                        else:
                            print_red(ts)
                            self.raise_code_error(f'no support for type [{ts}]')

                self.size = offset

                if self.name: # case 1
                    # add to type list
                    if self.get_scope_item(self.name) is not None:
                        self.raise_code_error(f'[{self.name}] already defined')

                    self.add_to_scope({'type': 'struct', 'name': self.name, 'struct_data':self.members, 'size':self.size})
            else: # case 3
                # find struct type
                if self.get_scope_item(self.name) is None:
                    self.raise_code_error(f'[{self.name}] not defined')

                struct_data = self.get_scope_item(self.name)
                self.size = struct_data['size']

            # raise
        else:
            self.raise_code_error(f'no support')


class CompoundStatement(CComponent):
    # { block-item-list }

    def __init__(self, compiler, bil: list):
        super().__init__(compiler)
        self.bil = bil

    def __repr__(self):
        return f'CompoundStatement {self.bil}'

    def print_me(self, indent):
        print(f'{" " * indent}CompoundStatement len = {len(self.bil)}')
        for bi in self.bil:
            if hasattr(bi, 'print_me'):
                bi.print_me(indent + PRINT_INDENT)
            else:
                print(f'{" " * (indent + PRINT_INDENT)}{bi}')

    def gen_asm(self):
        self.enter_scope()

        for bi in self.bil:
            # Declaration or statement
            bi.gen_asm()

        self.leave_scope(free_stack_variables = True)


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
        print(f'{" " * indent}Statement len = {len(self.bil)}')
        for bi in self.bil:
            if hasattr(bi, 'print_me'):
                bi.print_me(indent + PRINT_INDENT)
            else:
                print(f'{" " * (indent + PRINT_INDENT)}{bi}')


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
        print(f'{" " * indent}LabeledStatement len = {self.data_count}')
        for item in self.data:
            if hasattr(item, 'print_me'):
                item.print_me(indent + PRINT_INDENT)
            else:
                print(f'{" " * (indent + PRINT_INDENT)}{item}')

    def gen_asm(self):
        if self.data[0] not in ['case', 'default']:
            self.write_asm(f'    {self.data[0].name}:\n')


class Expression(CComponent):
    # assignment-expression
    # expression , assignment-expression

    def __init__(self, compiler, aes: list):
        super().__init__(compiler)
        self.aes = aes

    def __repr__(self):
        return f'Expression {self.aes}'

    def print_me(self, indent):
        print(f'{" " * indent}Expression len = {len(self.aes)}')
        for ae in self.aes:
            # if bi.hasattr('print_me'):
            if hasattr(ae, 'print_me'):
                ae.print_me(indent + PRINT_INDENT)
            else:
                print(f'{" " * (indent + PRINT_INDENT)}{ae}')

    def gen_asm(self, my_result_offset = None, set_result = True):
        result = None

        for ae in self.aes:
            self.write_asm(f'\n    ; Expression start offset = {self.compiler.get_function_stack_offset()} my_result_offset = {my_result_offset}\n')
            result = ae.gen_asm(my_result_offset, set_result)
            self.write_asm(f'    ; Expression over offset = {self.compiler.get_function_stack_offset()}\n\n')

        return result

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
        print(f'{" " * indent}AssignmentExpression')
        if self.ce:
            self.ce.print_me(indent + PRINT_INDENT)
        else:
            self.ue.print_me(indent + PRINT_INDENT)
            print(f'{" " * (indent + PRINT_INDENT)}{self.opt}')
            self.ae.print_me(indent + PRINT_INDENT)

    def gen_asm(self, my_result_offset = None, set_result = True, need_global_const = False):
        if self.ce:
            return self.ce.gen_asm(my_result_offset, set_result, need_global_const = need_global_const)
        else:
            left_data = self.ue.gen_asm(my_result_offset)
            print_red(left_data)

            if left_data['type'] in ['var', 'pointer', 'de_pointer', 'de_array', 'member']:
                # case 1: *p = 123;
                # case 2: abc = *p;
                # a = *b = *c
                # *a = *b = 1

                if self.opt == '=':
                    offset = self.stack_alloc(8, 'for AssignmentExpression')

                    right_data = self.ae.gen_asm(offset)
                    # print_red(right_data)

                    # right_data to address
                    if right_data['type'] in ['de_pointer', 'de_array', 'member']:
                        if left_data['type'] in ['var', 'pointer']:
                            # a = *b
                            # p = b[1]
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                            self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_3} ; save value at address to dest\n')
                            if 'global' in left_data:
                                self.write_asm(f'    mov {left_data["name"]}, {TEMP_REG_3} ; save global value\n')
                        else:
                            # *a = *b
                            # *p = b[1]
                            # a[1] = *b
                            # a[1] = b[1]
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                            self.write_asm(f'    mov {TEMP_REG_5}, [rbp - {my_result_offset}]\n')
                            self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                            self.write_asm(f'    mov [{TEMP_REG_5}], {TEMP_REG_3} ; save value at address to address\n')
                    else:
                        if left_data['type'] in ['var', 'pointer']:
                            # a = 123
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')

                            if set_result:
                                self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_4} ; save value to dest\n')

                            if 'global' in left_data:
                                self.write_asm(f'    mov {left_data["name"]}, {TEMP_REG_4} ; save global value\n')
                            else:
                                self.write_asm(f'    mov [rbp - {left_data["offset"]}], {TEMP_REG_4} ; save global value\n')
                        else:
                            # *a = 123
                            # a[1] = 123
                            # a[2][3] = 123
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                            self.write_asm(f'    mov {TEMP_REG_5}, [rbp - {my_result_offset}] ; get dest address\n')
                            self.write_asm(f'    mov [{TEMP_REG_5}], {TEMP_REG_4} ; save value to address\n')

                    self.stack_free(8, 'for AssignmentExpression')

                    return left_data
                else:
                    self.raise_code_error(f'no support')
            else:
                self.raise_code_error(f'AssignmentExpression wrong ue type [{left_data["type"]}]')


class ConditionalExpression(CComponent):
    # logical-or-expression
    # logical-or-expression ? expression : conditional-expression

    def __init__(self, compiler, loe, exp, ce):
        super().__init__(compiler)
        self.loe = loe
        self.exp = exp
        self.ce = ce

    def __repr__(self):
        return f'ConditionalExpression {self.loe, self.exp, self.ce}'

    def print_me(self, indent):
        print(f'{" " * indent}ConditionalExpression')
        self.loe.print_me(indent + PRINT_INDENT)
        self.exp.print_me(indent + PRINT_INDENT)
        self.ce.print_me(indent + PRINT_INDENT)

    def gen_asm(self, my_result_offset, set_result = True, need_global_const = False):
        if not self.exp:
            return self.loe.gen_asm(my_result_offset, set_result, need_global_const = need_global_const)
        else:
            self.loe.gen_asm(my_result_offset)
            self.write_asm(f'    ; ConditionalExpression test le result\n')
            self.exp.gen_asm()
            self.ce.gen_asm()


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
        print(f'{" " * indent}{self.__class__.__name__}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

    def set_opt(self, opt):
        self.opt = opt

    def get_const_result(self):
        return None

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
        pass

    def gen_asm(self, my_result_offset, set_result = True, need_global_const = False):
        if self.data_count == 1:
            return self.data[0].gen_asm(my_result_offset, set_result, need_global_const = need_global_const)

        offset = None
        if not need_global_const:
            print_red(self.data)
            self.push_reg(TEMP_REG_0, 'ChainExpression save')

            # space for exp results
            offset = self.compiler.get_function_stack_offset() + 8
            self.stack_alloc(8 * self.data_count, 'ChainExpression for exp result')

            result_offset = offset # for final result

        # check const
        # if some items are const, we can make some results at compile time?
        all_const = True

        # gen_asm for each
        for item in self.data:
            result = item.gen_asm(offset, need_global_const = need_global_const)

            if result['type'] != 'const':
                all_const = False
                if need_global_const:
                    self.raise_code_error(f'{self.__class__.__name__} need_global_const')

            if result['type'] in ['string']:
                # ok if just one item
                if self.data_count > 1:
                    self.raise_code_error(f'wtf on string [{result["name"]}]')
            elif result['type'] in ['de_pointer', 'de_array', 'member']:
                # get value from address
                self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                self.write_asm(f'    mov [rbp - {offset}], {TEMP_REG_3}\n')

            self.gen_asm_results.append(result)

            if not need_global_const:
                offset += 8

        print_red(f'gen_asm_results = {self.gen_asm_results}')

        if all_const:

            result = self.get_const_result()

            if not need_global_const:
                if set_result:
                    self.write_asm(f'    mov qword ptr [rbp - {my_result_offset}], {result} ; ChainExpression set result\n')

                # free
                self.stack_free(8 * self.data_count, 'ChainExpression for exp result')
                self.pop_reg(TEMP_REG_0, 'ChainExpression recover')

            return {'type':'const', 'value':result}

        self.sub_items_gen_asm(result_offset, my_result_offset, set_result)

        # free
        self.stack_free(8 * self.data_count, 'ChainExpression for exp result')
        self.pop_reg(TEMP_REG_0, 'ChainExpression recover')

        if self.data_count == 1:
            # print_red(gen_asm_results[0])
            return self.gen_asm_results[0]

        return {'type':'mem', 'offset':my_result_offset}


class LogicalOrExpression(ChainExpression):
    # logical-and-expression
    # logical-or-expression || logical-and-expression

    def __init__(self, compiler, data):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'LogicalOrExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        for index in range(self.data_count):
            if 1 == self.gen_asm_results[index]['value']:
                return 1

        return 0

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
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
            self.write_asm(f'    mov qword ptr [rbp - {my_result_offset}], 0\n    jmp {label_2_name}\n    {label_1_name}:\n')
            self.write_asm(f'        mov qword ptr [rbp - {my_result_offset}], 1\n    {label_2_name}:\n')


class LogicalAndExpression(ChainExpression):
    # inclusive-or-expression
    # logical-and-expression && inclusive-or-expression

    def __init__(self, compiler, data):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'LogicalAndExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        for index in range(self.data_count):
            if 0 == self.gen_asm_results[index]['value']:
                return 0

        return 1

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
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
            self.write_asm(f'    mov qword ptr [rbp - {my_result_offset}], 1\n    jmp {label_2_name}\n    {label_1_name}:\n')
            self.write_asm(f'        mov qword ptr [rbp - {my_result_offset}], 0\n    {label_2_name}:\n')


class InclusiveOrExpression(ChainExpression):
    # exclusive-or-expression
    # inclusive-or-expression | exclusive-or-expression

    def __init__(self, compiler, data):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'InclusiveOrExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            result |= self.gen_asm_results[index]['value']

        return result

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            '''
            and {TEMP_REG_0}, xxx
            '''
            self.write_asm(f'    or {TEMP_REG_0}, [rbp - {result_offset}]\n')

        if set_result:
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; InclusiveOrExpression set result\n')


class ExclusiveOrExpression(ChainExpression):
    # and-expression
    # exclusive-or-expression ^ and-expression

    def __init__(self, compiler, data):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'ExclusiveOrExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            result ^= self.gen_asm_results[index]['value']

        return result

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8
            '''
            and {TEMP_REG_0}, xxx
            '''
            self.write_asm(f'    xor {TEMP_REG_0}, [rbp - {result_offset}]\n')

        if set_result:
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; ExclusiveOrExpression set result\n')


class AndExpression(ChainExpression):
    # equality-expression
    # and-expression & equality-expression

    def __init__(self, compiler, data):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'AndExpression {self.data}'

    def get_const_result(self):
        # todo? not consistent with c
        result = self.gen_asm_results[0]['value']
        for index in range(1, self.data_count):
            result &= self.gen_asm_results[index]['value']

        return result

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            '''
            and {TEMP_REG_0}, xxx
            '''
            self.write_asm(f'    and {TEMP_REG_0}, [rbp - {result_offset}]\n')

        if set_result:
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; set result\n')


class EqualityExpression(ChainExpression):
    # relational-expression
    # equality-expression == relational-expression
    # equality-expression != relational-expression

    def __init__(self, compiler, data):
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

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
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
                raise CompilerError(f'wtf')

        if set_result:
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; EqualityExpression set result\n')


class RelationalExpression(ChainExpression):
    # shift-expression
    # relational-expression < shift-expression
    # relational-expression > shift-expression
    # relational-expression <= shift-expression
    # relational-expression >= shift-expression

    def __init__(self, compiler, data):
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

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
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
                raise CompilerError(f'wtf')

        if set_result:
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; RelationalExpression set result\n')


class ShiftExpression(ChainExpression):
    # additive-expression
    # shift-expression << additive-expression
    # shift-expression >> additive-expression

    def __init__(self, compiler, data):
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

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
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
                raise CompilerError(f'wtf')
            self.write_asm(f'    pop rcx\n')

        if set_result:
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; ShiftExpression set result\n')


class AdditiveExpression(ChainExpression):
    # multiplicative-expression
    # additive-expression + multiplicative-expression
    # additive-expression - multiplicative-expression

    def __init__(self, compiler, data):
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

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            if self.data[index].opt == '+':
                self.write_asm(f'    add {TEMP_REG_0}, [rbp - {result_offset}]\n')
            elif self.data[index].opt == '-':
                self.write_asm(f'    sub {TEMP_REG_0}, [rbp - {result_offset}]\n')
            else:
                raise CompilerError(f'wtf')

        if set_result:
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; AdditiveExpression set result\n')


class MultiplicativeExpression(ChainExpression):
    # cast-expression
    # multiplicative-expression * cast-expression
    # multiplicative-expression / cast-expression
    # multiplicative-expression % cast-expression

    def __init__(self, compiler, data):
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

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
        # first to {TEMP_REG_0}
        self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            # print_orange(f'MultiplicativeExpression item = {self.data[index]}')
            if self.data[index].opt == '*':
                if self.gen_asm_results[index]['type'] == 'const':
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
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; MultiplicativeExpression set result\n')


class CastExpression(CComponent):
    # unary-expression
    # ( type-name ) cast-expression

    def __init__(self, compiler, casts, ue):
        super().__init__(compiler)
        self.casts = casts
        self.ue = ue
        self.opt = None

    def set_opt(self, opt):
        self.opt = opt

    def __repr__(self):
        return f'CastExpression {self.casts, self.ue}'

    def print_me(self, indent):
        print(f'{" " * indent}CastExpression')
        print(f'{" " * (indent + PRINT_INDENT)}casts = {self.casts}')
        self.ue.print_me(indent + PRINT_INDENT)

    def gen_asm(self, result_offset, set_result = True, need_global_const = False):
        return self.ue.gen_asm(result_offset, set_result, need_global_const = need_global_const)


class UnaryExpression(CComponent):
    # postfix-expression
    # ++ unary-expression
    # -- unary-expression
    # unary-operator cast-expression
    # sizeof unary-expression
    # sizeof ( type-name )

    def __init__(self, compiler, pe = NoObject(), pp = NoObject(), ue = NoObject(), uo = NoObject(),
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
        print(f'{" " * indent}UnaryExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.pe, self.pp, self.ue, self.uo, self.cast, self.sizeof, self.tn}')
        if self.pe:
            self.pe.print_me(indent + PRINT_INDENT)
        elif self.pp:
            print(f'{" " * (indent + PRINT_INDENT)}{self.pp}')
            self.ue.print_me(indent + PRINT_INDENT)
        elif self.uo:
            print(f'{" " * (indent + PRINT_INDENT)}{self.uo}')
            self.cast.print_me(indent + PRINT_INDENT)
        elif self.sizeof:
            print(f'{" " * (indent + PRINT_INDENT)}sizeof')
            if self.ue:
                self.ue.print_me(indent + PRINT_INDENT)
            else:
                self.tn.print_me(indent + PRINT_INDENT)

    def gen_asm(self, result_offset, set_result = True, need_global_const = False):
        self.write_asm(f'    ; UnaryExpression gen_asm {self.uo}\n')

        if self.pe:
            return self.pe.gen_asm(result_offset, need_global_const = need_global_const)
        elif self.pp:
            if need_global_const:
                self.raise_code_error(f'{self.pp} need_global_const')

            data = self.ue.gen_asm(result_offset)
            if data['type'] == 'const':
                self.raise_code_error(f'prefix {self.pp} on const')
            elif data['type'] == 'mem':
                self.raise_code_error(f'prefix {self.pp} on mem')
            elif data['type'] == 'var':
                if self.pp == '++':
                    self.write_asm(f'    inc qword ptr [rbp - {data["offset"]}] ; ++\n')
                else:
                    self.write_asm(f'    dec qword ptr [rbp - {data["offset"]}] ; --\n')

                if set_result:
                    self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {data["offset"]}]\n')
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4}\n')
            elif data['type'] == 'pointer':
                raise

            return data
        elif self.uo:
            if need_global_const:
                self.raise_code_error(f'{self.uo} need_global_const')

            # ['&', '*', '+', '-', '~', '!']
            if self.uo == '-':
                data = self.cast.gen_asm(result_offset)

                # error
                if data['type'] not in ['const', 'var']:
                    self.raise_code_error(f"- on {data['type']}")

                # c std 6.5.3.3
                self.write_asm(f'    neg qword ptr [rbp - {result_offset}] ; negation\n')

                if data['type'] == 'const':
                    return {'type':'const', 'value':-data['value']}

                return {'type':'mem', 'offset':result_offset}
            elif self.uo == '&':
                # get address
                data = self.cast.gen_asm(result_offset, set_result = False)

                print_red(f'{data}')
                name = data['name']

                if data['type'] == 'var':
                    if 'global' in data:
                        if data['data_type'] in ['int']:
                            self.write_asm(f'    lea {TEMP_REG_4}, {name}\n')
                        else:
                            self.write_asm(f'    lea {TEMP_REG_4}, {name}\n')
                    else:
                        # local stack address
                        self.write_asm(f'    mov {TEMP_REG_4}, rbp\n')
                        self.write_asm(f'    sub {TEMP_REG_4}, {data["offset"]}\n')

                    if set_result:
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; save address\n')

                    return {'type':'mem', 'offset':result_offset}
                elif data['type'] in ['member', 'de_array', 'de_pointer']:
                    self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {result_offset}]\n')

                    if set_result:
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; save address\n')

                    return {'type':'mem', 'offset':result_offset}
                else:
                    self.raise_code_error(f'& on wrong type [{data["type"]}]')
            elif self.uo == '*':
                # indirection. dereferencing.

                data = self.cast.gen_asm(result_offset, set_result = False)
                print_red(f'dereference. data = {data}')
                # {'type': 'pointer', 'data_type': 'int', 'name': 'p', 'offset': 16, 'pointer_data': [[], []]}
                # int **p;

                if data['type'] != 'pointer':
                    self.raise_code_error(f'* on non-pointer')

                new_data = copy.deepcopy(data) # do not break original data

                pointer_item = new_data['pointer_data'].pop()
                if len(new_data['pointer_data']) == 0:
                    self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {new_data["offset"]}]; dereference. get pointer value\n')
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4}; dereference. address to temp\n')

                    new_data['type'] = 'de_pointer'
                    new_data['offset'] = result_offset

                else:
                    self.raise_code_error(f'wrong pointer_data')

                # print_red(f'after dereferencing. data = {data}')
                # print_red(f'after dereferencing. new_data = {new_data}')

                return new_data

            else:
                raise CompilerError(f'unknown unary-operator')

        raise CompilerError(f'UnaryExpression.gen_asm failed')


class PostfixExpression(CComponent):
    # primary-expression
    # postfix-expression [ expression ] # array index
    # postfix-expression ( argument-expression-list? ) # function call
    # postfix-expression . identifier
    # postfix-expression -> identifier
    # postfix-expression ++
    # postfix-expression --

    def __init__(self, compiler, primary, data):
        super().__init__(compiler)
        self.primary = primary
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'PostfixExpression {self.primary, self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}PostfixExpression')
        self.primary.print_me(indent + PRINT_INDENT)
        print(f'{" " * (indent + PRINT_INDENT)}postfix data = {self.data}')

    def gen_asm(self, result_offset, set_result = True, need_global_const = False):
        self.write_asm(f'    ; PostfixExpression gen_asm\n')

        if self.primary.idf:
            scope_item = self.primary.gen_asm(result_offset, set_result = set_result, need_global_const = need_global_const)

            if need_global_const:
                if len(self.data) > 0:
                    self.raise_code_error(f'need_global_const')

            # print_red(f'scope_item = {scope_item}')
            current_result = copy.deepcopy(scope_item) # {'type':'var', 'offset':scope_item['offset']}

            for item in self.data:
                if item in ['++', '--']:
                    if current_result['type'] == 'var':
                        # print_red(f'scope = {self.compiler.scope[-1]}')

                        if result_offset is None:
                            raise CompilerError(f'post {item} must has result_offset')

                        # get original value
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {scope_item["offset"]}]\n')
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4}\n')

                        current_result = {'type':'mem', 'offset':result_offset}

                        if item == '++':
                            self.write_asm(f'    inc qword ptr [rbp - {scope_item["offset"]}] ; {self.primary.idf.name}++\n')
                        else:
                            self.write_asm(f'    dec qword ptr [rbp - {scope_item["offset"]}] ; {self.primary.idf.name}--\n')

                    else:
                        self.raise_code_error(f'post {item} on non var')

                elif item[0] == '.':
                    if current_result['type'] in ['var', 'de_array', 'de_pointer', 'member']:
                        # print_red(current_result)
                        # print_red(item)

                        if current_result['type'] == 'member':
                            print_red(current_result)
                            print_red(item)
                            #self.raise_code_error(f'wtf')

                        # get struct data

                        # struct S1 s1;
                        # s1.a = 123;
                        # current_result = {'type': 'var', 'data_type': 'S1', 'name': 's1', 'offset': 24}
                        struct = self.get_scope_item(current_result['data_type'])
                        if struct is None:
                            self.raise_code_error(f'[{current_result["data_type"]}] not found')

                        # check struct
                        if struct['type'] != 'struct':
                            self.raise_code_error(f'. on non struct [{current_result["data_type"]}]')

                        # check member
                        member_name = item[1].name
                        member_data = struct['struct_data'].get(member_name, None)
                        if member_data is None:
                            self.raise_code_error(f'[{member_name}] is not a member of {current_result["data_type"]}')

                        if current_result['type'] in ['de_array', 'de_pointer']:
                            # runtime address
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {result_offset}] ; get struct address\n')
                            self.write_asm(f'    add {TEMP_REG_4}, {member_data["offset"]} ; get struct member address\n')
                        elif current_result['type'] in ['member']:
                            # a.b.c.d
                            # runtime address
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {result_offset}] ; get struct address\n')
                            self.write_asm(f'    add {TEMP_REG_4}, {member_data["offset"]} ; get struct member address\n')
                        else:
                            if 'global' in current_result:
                                self.write_asm(f'    lea {TEMP_REG_4}, {current_result["name"]} ; get global struct address\n')
                                self.write_asm(f'    add {TEMP_REG_4}, {member_data["offset"]}; get member address\n')
                            else: # stack
                                self.write_asm(f'    mov {TEMP_REG_4}, rbp\n')
                                self.write_asm(f'    sub {TEMP_REG_4}, {current_result["offset"] - member_data["offset"]} ; get struct member address\n')

                        # set address to result_offset
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; struct member address to result_offset\n')

                        # update to member
                        current_result['type'] = 'member'
                        current_result['data_type'] = member_data['data_type']
                        current_result['offset'] = member_data['offset']
                    else:
                        self.raise_code_error(f'. on [{current_result["type"]}]')

                elif item[0] == '->':
                    if current_result['type'] in ['pointer']:
                        # print_red(current_result)
                        # print_red(item)

                        # get struct data

                        # struct S1 *p;
                        # p->a = 123;
                        # current_result = {'type': 'pointer', 'data_type': 'S1', 'name': 'p', 'offset': 24}
                        struct = self.get_scope_item(current_result['data_type'])
                        if struct is None:
                            self.raise_code_error(f'[{current_result["data_type"]}] not found')

                        # not struct
                        if struct['type'] != 'struct':
                            self.raise_code_error(f'. on non struct [{current_result["data_type"]}]')

                        # not member
                        member_name = item[1].name
                        member_data = struct['struct_data'].get(member_name, None)
                        if member_data is None:
                            self.raise_code_error(f'[{member_name}] is not a member of {current_result["data_type"]}')

                        if 'global' in current_result:
                            self.write_asm(f'    mov {TEMP_REG_4}, {current_result["name"]} ; get global pointer value\n')
                        else:
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {current_result["offset"]}]; get pointer value\n')

                        self.write_asm(f'    add {TEMP_REG_4}, {member_data["offset"]} ; get member address\n')

                        # set address to result_offset
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; struct member address to result_offset\n')

                        # update to member
                        current_result['type'] = 'member'
                        current_result['data_type'] = member_data['data_type']
                        current_result['offset'] = member_data['offset']
                    else:
                        self.raise_code_error(f'. on [{current_result["type"]}]')
                elif item[0] == 'array index':

                    # stack layout
                    # a[2][3][4]
                    # [[[x, x, x, x], [x, x, x, x], [x, x, x, x]], [[x, x, x, x], [x, x, x, x], [x, x, x, x]]]

                    # example
                    # int arrrrrrr[3][222]
                    # [[x, x, ...], [x, x, ...], [x, x, ...]]
                    # current_result = {'type': 'array', 'data_type': 'int', 'name': 'arrrrrrr', 'offset': 5336, 'dim': 2, 'ranks': [3, 222]}

                    # arrrrrrr[exp]
                    # sub_elements_count = 222
                    # new_address = rbp - 5336 + exp * sub_elements_count
                    # -> {'type': 'de_array', 'data_type': 'int', 'name': 'arrrrrrr', 'offset': 5336, 'dim': 1, 'ranks': [222]}
                    # save new_address to result_offset

                    # print_red(item)

                    if current_result['type'] not in ['array', 'pointer', 'de_array']:
                        self.raise_code_error(f'indexing on non array [{current_result}]')

                    if current_result['type'] == 'array':
                        # set init array address as current_address
                        # it is runtime address
                        if 'global' in current_result:
                            self.write_asm(f'    lea {TEMP_REG_4}, {current_result["name"]} ; runtime address to result_offset {result_offset}\n')
                            self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; runtime address to result_offset {result_offset}\n')
                        else:
                            self.write_asm(f'    mov {TEMP_REG_4}, rbp\n')
                            self.write_asm(f'    sub {TEMP_REG_4}, {current_result["offset"]} ; runtime address to {TEMP_REG_4}\n')
                            self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; runtime address to result_offset {result_offset}\n')

                    offset = self.stack_alloc(8, 'array index. for exp result')

                    exp_data = item[1].gen_asm(offset)
                    print_red(exp_data)

                    # check exp_data
                    if exp_data['type'] not in ['var', 'const', 'mem']:
                        self.raise_code_error(f'wrong type {exp_data["type"]} as array index')

                    # get array[exp] address
                    # sub_elements_count is known at compile time by array declaration
                    sub_elements_count = 1
                    for rank in current_result['ranks'][1:]:
                        sub_elements_count *= rank

                    self.write_asm(f'    ; sub_elements_count = {sub_elements_count} is known at compile time by array declaration\n')

                    # new_address = current_address + exp * sub_elements_count * element_size

                    element_size = 8 # 8 for all simple data types for now

                    data_type = current_result['data_type']
                    if data_type in []:
                        pass
                    else:
                        scope_item = self.get_scope_item(data_type)
                        if scope_item is None:
                            self.raise_code_error(f'[data_type] not defined')

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
                    if len(current_result['ranks']) >= 1:
                        # still array
                        current_result['ranks'] = current_result['ranks'][1:]
                        current_result['dim'] -= 1
                    else:
                        self.raise_code_error(f'indexing on wrong data')

                    current_result['type'] = 'de_array'

                    # free
                    self.stack_free(8, 'array index. for exp result')

                elif item[0] == 'function call':
                    # print_red(item)
                    # print_red(item[1])
                    # print_red(len(item[1]))

                    # print_yellow(f'arg item = {item}')
                    args_count = len(item[1])

                    # save args count to {TEMP_REG_5}

                    # stack
                    #   {TEMP_REG_5}
                    #   arg n
                    #   ...
                    #   arg 2
                    #   arg 1

                    self.write_asm(f'\n    ; start function call offset = {self.compiler.get_function_stack_offset()}\n')

                    # abi shadow
                    # at lease 4
                    abi_storage_args_count = args_count
                    if abi_storage_args_count < 4:
                        abi_storage_args_count = 4

                    # alignment
                    # 1 for {TEMP_REG_5}
                    align = ((1 + abi_storage_args_count) * 8 + self.compiler.get_function_stack_offset()) % 16
                    if align not in [0, 8]:
                        raise CompilerError(f'check alignment before call align = {align} not in [0, 8]')

                    if align != 0:
                        self.stack_alloc(8, 'padding for function call')

                    self.push_reg(TEMP_REG_5)
                    self.write_asm(f'    mov {TEMP_REG_5}, {args_count}; {args_count = }\n')

                    # space for args
                    last_offset = self.stack_alloc(8 * abi_storage_args_count, 'alloc function call args')
                    self.write_asm(f'    ; last_offset = {last_offset}\n')

                    # gen_asm for each arg
                    for ae in item[1]:
                        # print_red(f'arg = {ae}')
                        ae.print_me(0)
                        ae_data = ae.gen_asm(last_offset)

                        if ae_data['type'] in ['const', 'var', 'mem', 'string', 'pointer']:
                            pass
                        elif ae_data['type'] in ['de_pointer', 'de_array', 'member']:
                            # get value from address
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {last_offset}]\n')
                            self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                            self.write_asm(f'    mov [rbp - {last_offset}], {TEMP_REG_3}\n')
                        elif ae_data['type'] in ['array']:
                            # get address value
                            pass
                        else:
                            self.raise_code_error(f'wrong arg type {ae_data["type"]}')

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

                    self.write_asm(f'\n    ; function call over\n\n')

                else:
                    raise CompilerError(f'unknown postfix data {item}')

            if set_result:
                pass

            return current_result
        elif self.primary.const:
            if self.data_count > 0:
                self.raise_code_error(f'postfix on const')

            return self.primary.gen_asm(result_offset, set_result, need_global_const = need_global_const)

        elif self.primary.string:
            # "13ef"[0]; legal but ...

            if need_global_const:
                self.raise_code_error(f'need_global_const')

            if self.data_count > 0:
                self.raise_code_error(f'postfix on string')

            return self.primary.gen_asm(result_offset, set_result)
        else:
            return self.primary.exp.gen_asm(result_offset, set_result)


class PrimaryExpression(CComponent):
    # identifier
    # constant
    # string-literal
    # ( expression )

    def __init__(self, compiler, idf = NoObject(), const = NoObject(), string = NoObject(), exp = NoObject()):
        super().__init__(compiler)
        self.idf = idf
        self.const = const
        self.string = string
        self.exp = exp

    def __repr__(self):
        return f'PrimaryExpression {self.idf, self.const, self.string, self.exp}'

    def print_me(self, indent):
        print(f'{" " * indent}PrimaryExpression')
        if self.idf:
            print(f'{" " * (indent + PRINT_INDENT)}{self.idf}')
        elif self.const:
            print(f'{" " * (indent + PRINT_INDENT)}{self.const}')
        elif self.string:
            print(f'{" " * (indent + PRINT_INDENT)}{self.string}')
        else:
            print(f'{" " * (indent + PRINT_INDENT)}{self.exp}')

    def gen_asm(self, result_offset = None, set_result = True, need_global_const = False):
        self.write_asm(f'    ; PrimaryExpression gen_asm\n')

        if need_global_const:
            if self.idf:
                scope_item = self.get_scope_item(self.idf.name)
                if scope_item is None:
                    self.raise_code_error(f'[{self.idf.name}] not defined')

                if scope_item['type'] in ['var'] and 'const' in scope_item and 'global' in scope_item:
                    const_item = scope_item.copy()
                    const_item['type'] = 'const'
                    return const_item
                else:
                    self.raise_code_error(f'need_global_const')
            elif self.const:
                return {'type':'const', 'value':self.const.const}
            else:
                self.raise_code_error(f'need_global_const')

        if self.idf:
            name = self.idf.name

            scope_item = self.get_scope_item(name)
            if scope_item is None:
                self.print_current_scope()
                self.raise_code_error(f'[{name}] not defined')

            if set_result:
                if scope_item['type'] in ['array']: # get array address
                    if 'global' in scope_item:
                        self.write_asm(f'    lea {TEMP_REG_4}, {name} ; get array address [{name}]\n')
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move array address to result_offset {result_offset}\n')
                    else:
                        self.write_asm(f'    mov {TEMP_REG_4}, rbp ; get array address{name}\n')
                        self.write_asm(f'    sub {TEMP_REG_4}, {scope_item["offset"]} ; get array address {name}\n')
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move array address {name} to result_offset {result_offset}\n')
                elif scope_item['type'] in ['var', 'pointer']:
                    if 'global' in scope_item:
                        type_item = self.get_scope_item(scope_item['data_type'])
                        if type_item and type_item['type'] == 'struct':
                            pass
                        else:
                            self.write_asm(f'    mov {TEMP_REG_4}, {name} ; move var {name}\n')
                            self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move var {name} to result_offset {result_offset}\n')
                    else:
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {scope_item["offset"]}] ; move var {name}\n')
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move var {name} to result_offset {result_offset}\n')
                elif scope_item['type'] == 'function':
                    self.write_asm(f'    lea {TEMP_REG_4}, {name}\n')
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move function {name} address to result_offset {result_offset}\n')
                else:
                    raise CompilerError(f'set unknown type [{scope_item["type"]}] to result')

            return scope_item
        elif self.const:
            if set_result:
                self.write_asm(f'    mov qword ptr [rbp - {result_offset}], {self.const.const} ; mov const\n')
            return {'type':'const', 'value':self.const.const}
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

            return {'type':'string', 'name':string_var_name}
        else:
            return self.exp.gen_asm()

        raise CompilerError(f'PrimaryExpression return None')


class ExpressionStatement(CComponent):
    # expression? ;

    def __init__(self, compiler, exp: Expression):
        super().__init__(compiler)
        self.exp = exp

    def __repr__(self):
        return f'ExpressionStatement {self.exp}'

    def print_me(self, indent):
        print(f'{" " * indent}ExpressionStatement')
        self.exp.print_me(indent + PRINT_INDENT)

    def gen_asm(self):
        if self.exp:
            result_offset = self.stack_alloc(8, 'ExpressionStatement alloc for exp result')

            result = self.exp.gen_asm(result_offset)

            self.stack_free(8, 'ExpressionStatement free exp result')

            return result

        raise CompilerError(f'wtf ExpressionStatement')


class SelectionStatement(CComponent):
    # if ( expression ) statement
    # if ( expression ) statement else statement
    # switch ( expression ) statement

    def __init__(self, compiler, switch = NoObject(), exp = NoObject(), stmt_1 = NoObject(), stmt_2 = NoObject()):
        super().__init__(compiler)
        self.switch = switch
        self.exp = exp
        self.stmt_1 = stmt_1
        self.stmt_2 = stmt_2

    def __repr__(self):
        return f'SelectionStatement {self.switch} {self.exp} {self.stmt_1} {self.stmt_2}'

    def print_me(self, indent):
        print(f'{" " * indent}SelectionStatement {self.switch}')
        print(f'{" " * indent}{self.exp}')
        print(f'{" " * indent}{self.stmt_1}')
        print(f'{" " * indent}{self.stmt_2}')

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

        raise CompilerError(f'wtf SelectionStatement')


class IterationStatement(CComponent):
    # while ( expression ) statement
    # do statement while ( expression ) ;
    # for ( expression? ; expression? ; expression? ) statement
    # for ( declaration expression? ; expression? ) statement

    def __init__(self, compiler, loop_type: int, declaration = NoObject(), exp_1 = NoObject(), exp_2 = NoObject(), exp_3 = NoObject(), stmt = NoObject()):
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
        print(f'{" " * indent}IterationStatement loop_type = {self.loop_type}')
        self.declaration.print_me(indent + PRINT_INDENT)
        self.exp_1.print_me(indent + PRINT_INDENT)
        self.exp_2.print_me(indent + PRINT_INDENT)
        self.exp_3.print_me(indent + PRINT_INDENT)
        self.stmt.print_me(indent + PRINT_INDENT)

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

    def __init__(self, compiler, cmd, idf = NoObject(), exp = NoObject()):
        super().__init__(compiler)
        self.cmd = cmd
        self.idf = idf
        self.exp = exp

    def __repr__(self):
        return f'JumpStatement {self.cmd, self.idf, self.exp}'

    def print_me(self, indent):
        print(f'{" " * indent}JumpStatement')
        if self.cmd == 'goto':
            print(f'{" " * (indent + PRINT_INDENT)}goto {self.idf.name}')
        elif self.cmd == 'return':
            self.exp.print_me(indent + PRINT_INDENT)
        else:
            print(f'{" " * (indent + PRINT_INDENT)}{self.cmd}')

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
                offset = self.stack_alloc(8, 'JumpStatement for exp result')
                data = self.exp.gen_asm(offset) # todo: add result_reg?

                self.write_asm(f'    mov rax, [rbp - {offset}] ; set return value\n')

                self.stack_free(8, 'JumpStatement for exp result')
            else:
                self.write_asm(f'    xor rax, rax ; set return value = 0\n')

            self.write_asm(f'\n    leave\n    ret\n')
        else:
            raise CompilerError(f'JumpStatement unknow {self.cmd}')


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
        print(f'{" " * indent}InitDeclarator')
        print(f'{" " * (indent + PRINT_INDENT)}dtr = {self.dtr}')
        self.init.print_me(indent + PRINT_INDENT)


class Constant(CComponent):
    def __init__(self, compiler, data_type, const):
        super().__init__(compiler)
        self.data_type = data_type
        self.const = const

    def __repr__(self):
        return f'Constant({self.const})'

    def print_me(self, indent):
        print(f'{" " * indent}Constant')
        # self.dtr.print_me(indent + PRINT_INDENT)
        print(f'{" " * (indent + PRINT_INDENT)}{self.const}')
        # self.init.print_me(indent + PRINT_INDENT)


class Identifier(CComponent):
    def __init__(self, compiler, name):
        super().__init__(compiler)
        self.name = name

    def __repr__(self):
        return f'Identifier({self.name})'

    def __eq__(self, other):
        return self.name == other

    def print_me(self, indent):
        print(f'{" " * indent}Identifier({self.name})')
