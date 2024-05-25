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

    def write_asm_data(self, code: str):
        self.compiler.asm_data.write(code)

    def write_asm(self, code: str):
        self.compiler.asm_code.write(code)


class NoObject:
    def __init__(self, compiler = None):
        self.compiler = compiler

    def __repr__(self):
        return f'NoObject'

    def __bool__(self):
        return False

    def print_me(self, indent):
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

        # insert to scope
        for ed in self.eds:
            # scope.append(scope[-1])
            ed.gen_asm(global_scope = True)
            # print(ed)
            for item in ed.get_name():
                item['global'] = 1
                self.compiler.scope[-1][item['name']] = item
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

        self.compiler.current_function = self

        self.compiler.scope.append(self.compiler.scope[-1].copy())

        # add self tp scope
        self.compiler.scope[-1][self.name] = {'name':self.name, 'type':'function'}

        print(f'FunctionDefinition {self.name} scope = {self.compiler.scope[-1]}')

        self.write_asm(f'{self.name} proc ; FunctionDefinition \n')

        # Standard Entry Sequence
        self.write_asm(f'    push rbp\n    mov rbp, rsp\n')

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
        self.write_asm(f'\n    leave\n    ret\n')

        self.write_asm(f'{self.name} endp\n\n')

        self.compiler.scope.pop()

    def get_name(self):
        # return [self.declarator[1][1][0].name]
        return [{'name':self.name, 'type':'function'}]


class Declaration(CComponent):
    # declaration-specifiers init-declarator-list? ;

    def __init__(self, compiler, dss, idl, global_scope = False):
        super().__init__(compiler)
        self.dss = dss
        self.idl = idl
        self.global_scope = global_scope

    def __repr__(self):
        return f'\nDeclaration {self.dss} {self.idl}'

    def get_text(self, indent):
        return f'\n{" " * indent}Declaration {self.dss} {self.idl}'

    def print_me(self, indent):
        print(f'{" " * indent}Declaration')
        # print(f'{" " * (indent + PRINT_INDENT)}ds\n{" " * (indent + 8)}{self.ds}')
        print(f'{" " * (indent + PRINT_INDENT)}dss')
        for ds in self.dss:
            # if bi.hasattr('print_me'):
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

    def get_name(self):
        names = []

        if not self.idl:
            # print(self.dss[0].type_data.name)
            if self.dss[0].type_data.tp == 'struct':
                # names.append(('struct', self.dss[0].type_data.name.name))
                names.append({'type':'struct', 'name':self.dss[0].type_data.name.name})
                return names

        for initd in self.idl:
            print(initd)
            print(initd.dtr)
            print(initd.dtr[1]['name'])
            # names.append((initd.dtr[1][0], initd.dtr[1][1][0].name))
            names.append({'type':initd.dtr[1]['type'], 'name':initd.dtr[1]['name']})
            # print(ds.type_data)
            # names.append(ds.type_data)
        return names

    def gen_asm(self, global_scope = False):
        print(f'Declaration scope = {self.compiler.scope[-1]}')

        # todo: make new name
        if global_scope:
            data_type = self.dss[0].type_data
            if self.idl:
                for initd in self.idl:
                    # if isinstance(self.dss..type_data, Identifier):
                    #    pass
                    # print(initd)
                    if not initd.dtr[0]:
                        name = initd.dtr[1]['name']

                        if initd.dtr[1]['type'] == 'var':
                            if data_type == 'int':
                                self.write_asm_data(f'{name} dword 0\n')
                                continue
                        elif initd.dtr[1]['type'] == 'array':
                            if data_type == 'int':
                                self.write_asm_data(f'{name} dword 0\n')
                                continue
                        elif initd.dtr[1]['type'] == 'function':
                            self.write_asm_data(f'extern {name}:proc\n')
                            continue

                    self.write_asm_data(f'    ; Declaration\n')
        else:
            if self.dss[0].type_data == 'int':
                for item in self.idl:
                    name = item.dtr[1]['name']

                    if item.dtr[1]['type'] == 'var':  # declaration
                        # print(item.dtr[1][1])
                        # self.write_asm(f'    ; Declaration var {self.dss[0].type_data} {item.dtr[1][1][0].name}\n')
                        offset = self.compiler.add_function_stack_offset(8)
                        self.write_asm(f'    sub rsp, 8 ; Declaration var {self.dss[0].type_data} {name} offset = {offset}\n')

                        scope_item = {'type':'var', 'data_type':self.dss[0].type_data, 'name':name, 'offset':offset}

                        if item.dtr[0]:  # pointer
                            scope_item['type'] = 'pointer'
                            scope_item['pointer_data'] = item.dtr[0]
                            # * = [[]]
                            # * *const * = [[], ['const'], []]

                        # self.compiler.scope[-1].append({'type':self.dss[0].type_data, 'name':item.dtr[1][1][0].name, 'offset':self.compiler.get_function_stack_offset()})
                        self.compiler.scope[-1][scope_item['name']] = scope_item

                        print_red(f'{name} item.init = {item.init}')
                        if isinstance(item.init, AssignmentExpression):
                            item.init.gen_asm(scope_item['offset'])

                    elif item.dtr[1]['type'] == 'array':
                        self.write_asm(f'    ; Declaration array {self.dss[0].type_data} {name}\n')

                        print_red(f'array data {item.dtr[1]["array_data"]}')
                        array_size = 1
                        ranks = []

                        for rank_exp in item.dtr[1]['array_data']['ranks']:
                            print_red(f'{rank_exp = }')


                            self.write_asm(f'    sub rsp, 8 ; Declaration array {self.dss[0].type_data} {name} for exp\n')
                            result_offset = self.compiler.add_function_stack_offset(8)

                            result = rank_exp.gen_asm(result_offset, set_result = False)

                            # free
                            self.write_asm(f'    add rsp, 8 ; Declaration array {self.dss[0].type_data} {name} for exp\n')
                            self.compiler.add_function_stack_offset(-8)

                            print_red(f'{result = }')
                            # if result['type'] != 'const':
                            #     raise CompilerError(f'value in [] must be const')

                            if result['type'] != 'const':
                                raise CodeError(f'array rank must be const')

                            array_size *= result['value']
                            ranks.append(result['value'])

                        offset = self.compiler.add_function_stack_offset(8 * array_size)
                        self.write_asm(f'    sub rsp, {8 * array_size} ; Declaration array {self.dss[0].type_data} {name} offset = {offset}\n')

                        scope_item = {'type':'array', 'data_type':self.dss[0].type_data, 'name':name, 'offset':offset, 'dim':item.dtr[1]['array_data']['dim'], 'ranks':ranks}
                        # self.compiler.scope[-1].append({'type':self.dss[0].type_data, 'name':item.dtr[1][1][0].name, 'offset':self.compiler.get_function_stack_offset()})
                        self.compiler.scope[-1][scope_item['name']] = scope_item


            else:
                raise CompilerError('no support 1')
                self.write_asm(f'    ; Declaration {self.dss[0].type_data}\n')


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

    def print_me(self, indent):
        print(f'{" " * indent}TypeSpecifier')
        if hasattr(self.type_data, 'print_me'):
            self.type_data.print_me(indent + PRINT_INDENT)
        else:
            print(f'{" " * (indent + PRINT_INDENT)}{self.type_data}')


class StructUnion(CComponent):
    # struct-or-union identifier? { struct-declaration-list }
    # struct-or-union identifier

    def __init__(self, compiler, tp, name, decls):
        super().__init__(compiler)
        self.tp = tp  # struct or union
        self.name = name
        self.decls = decls

    def __repr__(self):
        return f'StructUnion {self.name} {self.decls}'

    def print_me(self, indent):
        print(f'{" " * indent}{self.tp.name}')
        print(f'{" " * (indent + PRINT_INDENT)}name = {self.name}')
        if self.decls:
            for decl in self.decls:
                # if bi.hasattr('print_me'):
                if hasattr(decl, 'print_me'):
                    decl.print_me(indent + PRINT_INDENT)
                else:
                    print(f'{" " * (indent + PRINT_INDENT)}{decl}')
        else:
            print(f'{" " * (indent + PRINT_INDENT)}NoObject()')


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
            # if bi.hasattr('print_me'):
            if hasattr(bi, 'print_me'):
                bi.print_me(indent + PRINT_INDENT)
            else:
                print(f'{" " * (indent + PRINT_INDENT)}{bi}')

    def gen_asm(self):
        for bi in self.bil:
            #print_red(f'bi = {bi}')

            # Declaration or statement
            if isinstance(bi, Declaration):
                bi.gen_asm()
            else:
                # self.write_asm(f'    sub rsp, 8 ; alloc space for statement result\n')
                # result_offset = self.compiler.add_function_stack_offset(8)

                bi.gen_asm()

                # self.write_asm(f'    add rsp, 8 ; free space for statement result\n')
                # self.compiler.add_function_stack_offset(-8)


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
            # if bi.hasattr('print_me'):
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
            # if bi.hasattr('print_me'):
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
        print(f'Expression gen_asm scope = {self.compiler.scope}')

        result = None

        for ae in self.aes:
            # self.write_asm(f'    ; Expression\n')
            # print_yellow(item)
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
            # print(f'{" " * (indent + PRINT_INDENT)}{self.ce}')
            self.ce.print_me(indent + PRINT_INDENT)
        else:
            # print(f'{" " * (indent + PRINT_INDENT)}{self.ue}')
            self.ue.print_me(indent + PRINT_INDENT)
            print(f'{" " * (indent + PRINT_INDENT)}{self.opt}')
            self.ae.print_me(indent + PRINT_INDENT)

    def gen_asm(self, my_result_offset, set_result = True):
        print(f'AssignmentExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')
        if self.ce:
            return self.ce.gen_asm(my_result_offset, set_result)
        else:
            # self.write_asm(f'    sub rsp 8; space for unary-expression\n')
            # self.compiler.add_function_stack_offset(8)
            ue_data = self.ue.gen_asm(my_result_offset, set_result = False)
            if ue_data['type'] in ['var', 'pointer']:
                # '=', '*=', '/=', '%=', '+=', '-=', '<<=', '>>=', '&=', '^=', '|='
                # v1 = xxx
                if self.opt == '=':
                    self.ae.gen_asm(ue_data['offset'])

                    return ue_data
            elif ue_data['type'] == 'de_pointer':
                # case 1: *p = 123;
                # case 2: abc = *p;
                # a = *b = *c
                # *a = *b = 1

                if self.opt == '=':
                    self.write_asm(f'    sub rsp, 8 ; for AssignmentExpression\n')
                    offset = self.compiler.add_function_stack_offset(8)

                    ae_data = self.ae.gen_asm(offset)
                    # print_red(ae_data)

                    # ae_data to address
                    if ae_data['type'] == 'de_pointer':
                        # *a = *b
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                        self.write_asm(f'    mov {TEMP_REG_5}, [rbp - {ue_data["offset"]}]\n')
                        self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                        self.write_asm(f'    mov [{TEMP_REG_5}], {TEMP_REG_3} ; save value at address to address\n')
                    elif ae_data['type'] == 'de_array':
                        # *p = b[1]
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                        self.write_asm(f'    mov {TEMP_REG_5}, [rbp - {my_result_offset}]\n')
                        self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                        self.write_asm(f'    mov [{TEMP_REG_5}], {TEMP_REG_3} ; save value at address to address\n')
                    else:
                        # *a = 123
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                        self.write_asm(f'    mov {TEMP_REG_5}, [rbp - {ue_data["offset"]}]\n')
                        self.write_asm(f'    mov [{TEMP_REG_5}], {TEMP_REG_4} ; save value to address\n')

                    # free
                    self.write_asm(f'    add rsp, 8 ; for AssignmentExpression\n')
                    self.compiler.add_function_stack_offset(-8)

                    return ue_data
                raise
            elif ue_data['type'] == 'de_array':
                if self.opt == '=':
                    self.write_asm(f'    sub rsp, 8 ; for AssignmentExpression\n')
                    offset = self.compiler.add_function_stack_offset(8)

                    ae_data = self.ae.gen_asm(offset)
                    # print_red(ae_data)

                    # ae_data to address
                    if ae_data['type'] == 'de_pointer':
                        # a[1] = *b
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                        self.write_asm(f'    mov {TEMP_REG_5}, [rbp - {my_result_offset}]\n')
                        self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                        self.write_asm(f'    mov [{TEMP_REG_5}], {TEMP_REG_3} ; save value at address to address\n')
                    elif ae_data['type'] == 'de_array':
                        # a[1] = b[1]
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                        self.write_asm(f'    mov {TEMP_REG_5}, [rbp - {my_result_offset}]\n')
                        self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                        self.write_asm(f'    mov [{TEMP_REG_5}], {TEMP_REG_3} ; save value at address to address\n')
                    else:
                        # a[1] = 123
                        # a[2][3] = 123
                        self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                        self.write_asm(f'    mov {TEMP_REG_5}, [rbp - {my_result_offset}]; get dest address\n')
                        self.write_asm(f'    mov [{TEMP_REG_5}], {TEMP_REG_4} ; save value to address\n')

                    # free
                    self.write_asm(f'    add rsp, 8 ; for AssignmentExpression\n')
                    self.compiler.add_function_stack_offset(-8)

                    return ue_data
                raise
            else:
                raise CodeError(f'AssignmentExpression wrong ue type {ue_data["type"]}')

            print_red(ue_data)

            raise
            return {'type':'mem', 'offset':ue_data['offset']}


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
        # print(f'{" " * (indent + PRINT_INDENT)}{self.loe}')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.exp}')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.ce}')
        self.loe.print_me(indent + PRINT_INDENT)
        self.exp.print_me(indent + PRINT_INDENT)
        self.ce.print_me(indent + PRINT_INDENT)

    def gen_asm(self, my_result_offset, set_result = True):
        print(f'ConditionalExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')
        if not self.exp:
            return self.loe.gen_asm(my_result_offset, set_result)
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
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

    def set_opt(self, opt):
        self.opt = opt

    def get_const_result(self):
        return None

    def sub_items_gen_asm(self, result_offset, my_result_offset, set_result = True):
        pass

    def gen_asm(self, my_result_offset, set_result = True):
        print(f'ChainExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        if self.data_count == 1:
            # if isinstance(self.data[0], tuple):
            #     return self.data[0][1].gen_asm(my_result_offset, set_result)
            # else:
            return self.data[0].gen_asm(my_result_offset, set_result)

        # save {TEMP_REG_0}
        self.write_asm(f'    push {TEMP_REG_0} ; save {TEMP_REG_0}\n')
        self.compiler.add_function_stack_offset(8)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; ChainExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # check const
        # if some items are const, we can make some results at compile time?
        all_const = True

        # gen_asm for each
        for item in self.data:
            # print_red(f'item = {item}')
            # if isinstance(item, tuple):
            #     result = item[1].gen_asm(offset)
            # else:
            result = item.gen_asm(offset)

            if result['type'] in ['string']:
                # ok if just one item
                if self.data_count > 1:
                    raise CodeError(f'wtf on string [{result["name"]}]')
            elif result['type'] in ['de_pointer', 'de_array']:
                # get value from address
                self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}]\n')
                self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                self.write_asm(f'    mov [rbp - {offset}], {TEMP_REG_3}\n')

            if result['type'] != 'const':
                all_const = False

            self.gen_asm_results.append(result)
            offset += 8

        print_red(f'gen_asm_results = {self.gen_asm_results}')

        if all_const:

            result = self.get_const_result()

            if set_result:
                self.write_asm(f'    mov qword ptr [rbp - {my_result_offset}], {result} ; ChainExpression set result\n')

            # free
            self.write_asm(f'    add rsp, {8 * self.data_count} ; ChainExpression\n')
            self.compiler.add_function_stack_offset(-8 * self.data_count)
            self.write_asm(f'    pop {TEMP_REG_0} ; ChainExpression recover {TEMP_REG_0}\n')
            self.compiler.add_function_stack_offset(-8)

            return {'type':'const', 'value':result}

        # first to {TEMP_REG_0}
        # self.write_asm(f'    mov {TEMP_REG_0}, [rbp - {result_offset}] ; MultiplicativeExpression get first result\n')

        self.sub_items_gen_asm(result_offset, my_result_offset, set_result)

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; ChainExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)
        self.write_asm(f'    pop {TEMP_REG_0} ; ChainExpression recover {TEMP_REG_0}\n')
        self.compiler.add_function_stack_offset(-8)

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

    def print_me1(self, indent):
        print(f'{" " * indent}LogicalOrExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

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

        # set result
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

    def print_me1(self, indent):
        print(f'{" " * indent}LogicalAndExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

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

    def print_me1(self, indent):
        print(f'{" " * indent}InclusiveOrExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

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

        # set result
        if set_result:
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; InclusiveOrExpression set result\n')


class ExclusiveOrExpression(ChainExpression):
    # and-expression
    # exclusive-or-expression ^ and-expression

    def __init__(self, compiler, data):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'ExclusiveOrExpression {self.data}'

    def print_me1(self, indent):
        print(f'{" " * indent}ExclusiveOrExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

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

        # set result
        if set_result:
            self.write_asm(f'    mov [rbp - {my_result_offset}], {TEMP_REG_0} ; ExclusiveOrExpression set result\n')


class AndExpression(ChainExpression):
    # equality-expression
    # and-expression & equality-expression

    def __init__(self, compiler, data):
        super().__init__(compiler, data)

    def __repr__(self):
        return f'AndExpression {self.data}'

    def print_m1e(self, indent):
        print(f'{" " * indent}AndExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

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

        # set result
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

    def print_me1(self, indent):
        print(f'{" " * indent}EqualityExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        for item in self.data:
            if hasattr(item, 'print_me'):
                item.print_me(indent + PRINT_INDENT)
            else:
                print(f'{" " * (indent + PRINT_INDENT)}{item}')

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

        # set result
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

    def print_me1(self, indent):
        print(f'{" " * indent}RelationalExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

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

        # set result
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

    def print_me1(self, indent):
        print(f'{" " * indent}ShiftExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        for item in self.data:
            item.print_me(indent + PRINT_INDENT)

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

        # set result
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

    def print_me1(self, indent):
        print(f'{" " * indent}AdditiveExpression')
        print(f'{" " * (indent + PRINT_INDENT)}{self.data}')

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

        # set result
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

    def print_me1(self, indent):
        print(f'{" " * indent}MultiplicativeExpression')
        print(f'{" " * (indent + PRINT_INDENT)}{self.data}')

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

        # set result
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
        # print(f'{" " * (indent + PRINT_INDENT)}{self.ue}')
        self.ue.print_me(indent + PRINT_INDENT)

    def gen_asm(self, result_offset, set_result = True):
        print(f'CastExpression gen_asm {result_offset = } scope = {self.compiler.scope}')
        # print(self.ue)
        return self.ue.gen_asm(result_offset, set_result)


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

    def gen_asm(self, result_offset, set_result = True):
        print(f'UnaryExpression gen_asm {result_offset = } scope = {self.compiler.scope}')
        self.write_asm(f'    ; UnaryExpression gen_asm {self.uo}\n')

        if self.pe:
            return self.pe.gen_asm(result_offset)
        elif self.pp:
            data = self.ue.gen_asm(result_offset)
            if data['type'] == 'const':
                raise CodeError(f'prefix {self.pp} on const')
            elif data['type'] == 'mem':
                raise CodeError(f'prefix {self.pp} on mem')
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
            # ['&', '*', '+', '-', '~', '!']
            if self.uo == '-':
                data = self.cast.gen_asm(result_offset)

                # error
                if data['type'] not in ['const', 'var']:
                    raise CodeError(f"- on {data['type']}")

                # c std 6.5.3.3
                self.write_asm(f'    neg qword ptr [rbp - {result_offset}] ; negation\n')

                if data['type'] == 'const':
                    return {'type':'const', 'value':-data['value']}

                return {'type':'mem', 'offset':result_offset}
            elif self.uo == '&':
                # get address
                data = self.cast.gen_asm(result_offset, set_result = False)

                print_red(f'{data}')

                if data['type'] == 'var':
                    self.write_asm(f'    mov {TEMP_REG_4}, rbp\n')
                    self.write_asm(f'    sub {TEMP_REG_4}, {data["offset"]}\n')

                    if set_result:
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; save address\n')

                    return {'type':'mem', 'offset':result_offset}
                else:
                    raise
            elif self.uo == '*':
                # indirection. dereferencing.

                data = self.cast.gen_asm(result_offset, set_result = False)
                print_red(f'dereference. data = {data}')
                # {'type': 'pointer', 'data_type': 'int', 'name': 'p', 'offset': 16, 'pointer_data': [[], []]}
                # int **p;

                if data['type'] != 'pointer':
                    raise CodeError(f'* on non-pointer')

                new_data = copy.deepcopy(data) # do not break original data

                pointer_item = new_data['pointer_data'].pop()
                if len(new_data['pointer_data']) == 0:
                    self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {new_data["offset"]}]; dereference. get pointer value\n')
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4}; dereference. address to temp\n')

                    new_data['type'] = 'de_pointer'
                    new_data['offset'] = result_offset

                else:
                    raise

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
        # print(f'{" " * (indent + PRINT_INDENT)}{self.primary}')
        self.primary.print_me(indent + PRINT_INDENT)
        print(f'{" " * (indent + PRINT_INDENT)}postfix data = {self.data}')

    def gen_asm(self, result_offset, set_result = True):
        print(f'PostfixExpression gen_asm {result_offset = } scope = {self.compiler.scope}')
        self.write_asm(f'    ; PostfixExpression gen_asm\n')
        # print(self.ue)
        # self.pe.gen_asm()

        # for item in self.data:
        #    self.write_asm(f'    ;PostfixExpression item\n')

        if self.primary.idf:
            # if self.data_count == 0:
            #     return self.primary.gen_asm(result_offset)

            scope_item = self.primary.gen_asm(result_offset)

            # scope_item = self.compiler.scope[-1].get(self.primary.idf.name, None)
            # if scope_item is None:
            #     raise CompilerError(f'{self.primary.idf.name} not found')

            print_red(f'scope_item = {scope_item}')
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
                        raise CodeError(f'post {item} on non var')

                elif item[0] == '.':
                    self.write_asm(f'    ; {self.primary.idf.name}.{item[1]}\n')
                elif item[0] == '->':
                    self.write_asm(f'    ; {self.primary.idf.name}->{item[1]}\n')
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
                        raise CodeError(f'indexing on non array [{current_result}]')

                    if current_result['type'] == 'array':
                        # set init array address as current_address
                        self.write_asm(f'    mov {TEMP_REG_4}, rbp ; set init array address\n')
                        self.write_asm(f'    sub {TEMP_REG_4}, {current_result["offset"]} ; set init array address\n')
                        self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; set init array address\n')

                    self.write_asm(f'    sub rsp, 8 ; array index. for exp result\n')
                    offset = self.compiler.add_function_stack_offset(8)

                    exp_data = item[1].gen_asm(offset)
                    print_red(exp_data)

                    # check exp_data
                    if exp_data['type'] not in ['var', 'const', 'mem']:
                        raise CodeError(f'wrong type {exp_data["type"]} as array index')

                    # get array[exp] address
                    # sub_elements_count is known at compile time by array declaration
                    sub_elements_count = 1
                    for rank in current_result['ranks'][1:]:
                        sub_elements_count *= rank

                    self.write_asm(f'    ; sub_elements_count = {sub_elements_count} is known at compile time by array declaration\n')

                    # new_address = current_address + exp * sub_elements_count * element_size

                    element_size = 8 # 8 for all simple data types for now

                    # exp * sub_elements_count * element_size
                    self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {offset}] ; get exp result\n')
                    self.write_asm(f'    imul {TEMP_REG_4}, {sub_elements_count} ; exp * sub_elements_count\n')
                    self.write_asm(f'    imul {TEMP_REG_4}, {element_size} ; * element_size {element_size}\n')

                    # + rbp
                    # self.write_asm(f'    add {TEMP_REG_4}, rbp ; + rbp\n')

                    # + current_address
                    self.write_asm(f'    add {TEMP_REG_4}, [rbp - {result_offset}] ; + current_address\n')

                    # - var offset
                    # self.write_asm(f'    sub {TEMP_REG_4}, {current_result["offset"]} ; - var offset\n')

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
                        raise CodeError(f'indexing on wrong data')
                        current_result['ranks'] = []
                        current_result['dim'] -= 1
                        # current_result['type'] = 'mem'

                    current_result['type'] = 'de_array'

                    self.write_asm(f'    add rsp, 8 ; array index. free\n')
                    self.compiler.add_function_stack_offset(-8)



                elif item[0] == 'function call':
                    # print_red(item)
                    # print_red(item[1])
                    # print_red(len(item[1]))

                    print_yellow(f'arg item = {item}')
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
                        self.write_asm(f'    sub rsp, 8 ; padding for function call\n')
                        self.compiler.add_function_stack_offset(8)

                    self.write_asm(f'    push {TEMP_REG_5} ; save {TEMP_REG_5}\n')
                    self.compiler.add_function_stack_offset(8)
                    self.write_asm(f'    mov {TEMP_REG_5}, {args_count}; {args_count = }\n')

                    # space for args
                    self.write_asm(f'    sub rsp, {8 * abi_storage_args_count} ; for function call args\n')
                    self.compiler.add_function_stack_offset(8 * abi_storage_args_count)

                    last_offset = self.compiler.get_function_stack_offset()
                    self.write_asm(f'    ; last_offset = {last_offset}\n')

                    # gen_asm for each arg
                    for ae in item[1]:
                        print_red(f'arg = {ae}')
                        ae.print_me(0)
                        ae_data = ae.gen_asm(last_offset)

                        if ae_data['type'] in ['const', 'var', 'mem', 'string', 'pointer']:
                            pass
                        elif ae_data['type'] == 'de_pointer':
                            # get value from address
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {last_offset}]\n')
                            self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                            self.write_asm(f'    mov [rbp - {last_offset}], {TEMP_REG_3}\n')
                        elif ae_data['type'] == 'de_array':
                            # get value from address
                            self.write_asm(f'    mov {TEMP_REG_4}, [rbp - {last_offset}]\n')
                            self.write_asm(f'    mov {TEMP_REG_3}, [{TEMP_REG_4}]\n')
                            self.write_asm(f'    mov [rbp - {last_offset}], {TEMP_REG_3}\n')
                        else:
                            raise CodeError(f'wrong arg type {ae_data["type"]}')

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
                    self.write_asm(f'    ; call over offset = {self.compiler.get_function_stack_offset()}\n')

                    if set_result:
                        self.write_asm(f'    mov [rbp - {result_offset}], rax ; save call result\n')

                    # clean
                    self.write_asm(f'    add rsp, {8 * abi_storage_args_count} ; clean for function call args\n')
                    self.compiler.add_function_stack_offset(-8 * abi_storage_args_count)
                    self.write_asm(f'    pop {TEMP_REG_5} ; recover {TEMP_REG_5}\n')
                    self.compiler.add_function_stack_offset(-8)

                    if align != 0:
                        self.write_asm(f'    add rsp, 8 ; clean padding for function call\n')
                        self.compiler.add_function_stack_offset(-8)

                else:
                    raise CompilerError(f'unknown postfix data {item}')

            if set_result:
                pass

            # return {'type':'mem', 'offset':result_offset}
            return current_result
        elif self.primary.const:
            if self.data_count > 0:
                raise CodeError(f'postfix on const')

            return self.primary.gen_asm(result_offset, set_result)

        elif self.primary.string:
            # "13ef"[0]; legal but ...
            if self.data_count > 0:
                raise CodeError(f'postfix on string')

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
        # self.type = tp
        # self.data = data
        self.idf = idf
        self.const = const
        self.string = string
        self.exp = exp

    def __repr__(self):
        return f'PrimaryExpression {self.idf, self.const, self.string, self.exp}'

    def print_me(self, indent):
        print(f'{" " * indent}PrimaryExpression')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.type}')
        # print(f'{" " * (indent + PRINT_INDENT)}{self.data}')
        if self.idf:
            print(f'{" " * (indent + PRINT_INDENT)}{self.idf}')
        elif self.const:
            print(f'{" " * (indent + PRINT_INDENT)}{self.const}')
        elif self.string:
            print(f'{" " * (indent + PRINT_INDENT)}{self.string}')
        else:
            print(f'{" " * (indent + PRINT_INDENT)}{self.exp}')

    def gen_asm(self, result_offset = None, set_result = True):
        print(f'PrimaryExpression gen_asm {result_offset = } scope = {self.compiler.scope}')
        self.write_asm(f'    ; PrimaryExpression gen_asm\n')
        if self.idf:
            # self.write_asm(f'    ; PrimaryExpression get idf {self.idf}\n')
            # return 'idf', self.idf.name

            scope_item = self.compiler.scope[-1].get(self.idf.name, None)
            if scope_item is None:
                raise CodeError(f'{self.idf.name} not found')

            print_red(f'{scope_item = }')

            if set_result:
                if scope_item['type'] in ['var', 'pointer', 'array']:
                    if 'global' in scope_item:
                        self.write_asm(f'    mov [rbp - {result_offset}], {self.idf.name} ; move var {self.idf.name} to offset {result_offset}\n')
                    else:
                        self.write_asm(f'    push rax\n')
                        self.write_asm(f'    mov rax, [rbp - {scope_item["offset"]}] ; move var {self.idf.name}\n')
                        self.write_asm(f'    mov [rbp - {result_offset}], rax ; move var {self.idf.name} to offset {result_offset}\n')
                        self.write_asm(f'    pop rax\n')
                elif scope_item['type'] == 'function':
                    self.write_asm(f'    lea {TEMP_REG_4}, {scope_item["name"]}\n')
                    self.write_asm(f'    mov [rbp - {result_offset}], {TEMP_REG_4} ; move function {self.idf.name} address to offset {result_offset}\n')
                else:
                    raise CompilerError(f'set unknown type [{scope_item["type"]}] to result')

            return scope_item

            # if 'global' in scope_item: # global scope
            #     return {'type':'var', 'name':self.idf.name, 'global':1}
            # else:
            #     return {'type':'var', 'name':self.idf.name, 'offset':scope_item['offset']}
        elif self.const:
            # self.write_asm(f'    ; PrimaryExpression get const {self.const}\n')
            # return 'const', self.const
            if set_result:
                self.write_asm(f'    mov qword ptr [rbp - {result_offset}], {self.const.const} ; mov const\n')
            return {'type':'const', 'value':self.const.const}
        elif self.string:
            if len(self.string) == 0:
                raise CodeError('empty string')

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
                        raise CodeError(f'string escape error')

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

            # return 'string', string_var_name
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
        print(f'ExpressionStatement gen_asm scope = {self.compiler.scope}')
        # f.write(f'    ; {self.exp}\n')
        # f.write(f'    ; ExpressionStatement\n')
        if self.exp:
            self.write_asm(f'    sub rsp, 8 ; SelectionStatement for exp result\n')
            result_offset = self.compiler.add_function_stack_offset(8)

            result = self.exp.gen_asm(result_offset)

            # free
            self.write_asm(f'    add rsp, 8 ; SelectionStatement free\n')
            self.compiler.add_function_stack_offset(-8)

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
        print(f'SelectionStatement gen_asm scope = {self.compiler.scope}')
        # f.write(f'    ; {self.exp}\n')
        # f.write(f'    ; ExpressionStatement\n')
        if not self.switch:
            self.write_asm(f'    sub rsp, 8 ; SelectionStatement for exp result\n')
            result_offset = self.compiler.add_function_stack_offset(8)

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

            # free
            self.write_asm(f'    add rsp, 8 ;\n')
            self.compiler.add_function_stack_offset(-8)

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
        print(f'IterationStatement gen_asm scope = {self.compiler.scope}')

        if self.loop_type == 0:
            '''
            loop_start:
            exp
            cmp exp, 0
            je loop_over
            stmt
            jmp loop_start
            
            loop_over:
            '''

            self.write_asm(f'    sub rsp, 8 ; IterationStatement for exp result\n')
            self.compiler.add_function_stack_offset(8)

            result_offset = self.compiler.get_function_stack_offset()

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

            # free
            self.write_asm(f'    add rsp, 8 ;\n')
            self.compiler.add_function_stack_offset(-8)
        elif self.loop_type == 1:
            '''
            loop_start:
            stmt
            exp
            cmp exp, 0
            je loop_over
            jmp loop_start
            
            loop_over:
            '''

            self.write_asm(f'    sub rsp, 8 ; IterationStatement for exp result\n')
            self.compiler.add_function_stack_offset(8)

            result_offset = self.compiler.get_function_stack_offset()

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

            # free
            self.write_asm(f'    add rsp, 8 ;\n')
            self.compiler.add_function_stack_offset(-8)
        elif self.loop_type == 2:
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

            self.write_asm(f'    sub rsp, 8 ; IterationStatement for exp result\n')
            result_offset = self.compiler.add_function_stack_offset(8)

            label_1_name = f'loop_start_{self.compiler.item_id}'
            self.compiler.item_id += 1

            label_2_name = f'loop_over_{self.compiler.item_id}'
            self.compiler.item_id += 1

            self.write_asm(f'    {label_1_name}:\n')

            if self.exp_2: # else forever
                self.exp_2.gen_asm(result_offset)
                self.write_asm(f'    cmp qword ptr [rbp - {result_offset}], 0\n    je {label_2_name}\n')

            self.stmt.gen_asm()

            if self.exp_3:
                self.exp_3.gen_asm()

            self.write_asm(f'    jmp {label_1_name}\n')
            self.write_asm(f'    {label_2_name}:\n')

            # free
            self.write_asm(f'    add rsp, 8 ;\n')
            self.compiler.add_function_stack_offset(-8)


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
            # print(f'{" " * (indent + PRINT_INDENT)}return {self.exp}')
            self.exp.print_me(indent + PRINT_INDENT)
        else:
            print(f'{" " * (indent + PRINT_INDENT)}{self.cmd}')

    def gen_asm(self, my_result_offset = None):
        print(f'JumpStatement gen_asm scope = {self.compiler.scope}')
        if self.cmd == 'goto':
            # label must in current function
            self.write_asm(f'    jmp {self.idf.name}\n')
        elif self.cmd == 'continue':
            self.write_asm(f'    ;continue\n')
        elif self.cmd == 'break':
            self.write_asm(f'    ;break\n')
        elif self.cmd == 'return':
            # Standard Exit Sequence
            # f.write(f'    mov rsp, rbp\n    pop rbp\n')

            if self.exp:
                # set return value
                self.write_asm(f'    sub rsp, 8\n')
                offset = self.compiler.add_function_stack_offset(8)
                data = self.exp.gen_asm(offset) # todo: add result_reg?

                self.write_asm(f'    mov rax, [rbp - {offset}] ; set return value\n')
                self.write_asm(f'    add rsp, 8\n')
                self.compiler.add_function_stack_offset(-8)
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
        # self.dtr.print_me(indent + PRINT_INDENT)
        print(f'{" " * (indent + PRINT_INDENT)}dtr = {self.dtr}')
        self.init.print_me(indent + PRINT_INDENT)
        # print(f'{" " * (indent + PRINT_INDENT)}init = {self.init}')


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
        # self.dtr.print_me(indent + PRINT_INDENT)
        # print(f'{" " * (indent + PRINT_INDENT)}{self.name}')
        # self.init.print_me(indent + PRINT_INDENT)
