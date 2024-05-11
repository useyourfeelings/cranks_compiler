import pprint
from compiler.tool import CompilerError, print_red, print_yellow, print_green, print_orange


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

    def gen_asm(self):
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
            ed.print_me(indent + 4)

    def gen_asm(self):
        self.write_asm(f'\n    .code\n\n')

        # insert to scope
        for ed in self.eds:
            # scope.append(scope[-1])
            ed.gen_asm(global_scope = True)
            # print(ed)
            for item in ed.get_name():
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

        self.name = self.declarator[1][1][0].name

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
        print(f'{" " * (indent + 4)}dss')
        for ds in self.dss:
            # if bi.hasattr('print_me'):
            if hasattr(ds, 'print_me'):
                ds.print_me(indent + 8)
            else:
                print(f'{" " * (indent + 8)}{ds}')

        print(f'{" " * (indent + 4)}{self.declarator}')
        # print(f'{" " * (indent + 4)}{self.dl}')
        # print(f'{" " * (indent + 4)}{self.cs}')
        self.cs.print_me(indent + 4)

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
        # print(f'{" " * (indent + 4)}ds\n{" " * (indent + 8)}{self.ds}')
        print(f'{" " * (indent + 4)}dss')
        for ds in self.dss:
            # if bi.hasattr('print_me'):
            if hasattr(ds, 'print_me'):
                ds.print_me(indent + 8)
            else:
                print(f'{" " * (indent + 8)}{ds}')
        print(f'{" " * (indent + 4)}idl')
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
            print(initd.dtr[1][0])
            # names.append((initd.dtr[1][0], initd.dtr[1][1][0].name))
            names.append({'type':initd.dtr[1][0], 'name':initd.dtr[1][1][0].name})
            # print(ds.type_data)
            # names.append(ds.type_data)
        return names

    def gen_asm(self, global_scope = False):
        print(f'Declaration scope = {self.compiler.scope[-1]}')

        # f.write(f'    ; {self.dss} {self.idl}\n')
        if global_scope:
            data_type = self.dss[0].type_data
            if self.idl:
                for initd in self.idl:
                    # if isinstance(self.dss..type_data, Identifier):
                    #    pass
                    # print(initd)
                    if not initd.dtr[0]:
                        if initd.dtr[1][0] == 'var':
                            if data_type == 'int':
                                self.write_asm_data(f'{initd.dtr[1][1][0].name} dword 0\n')
                                continue
                        elif initd.dtr[1][0] == 'function':
                            self.write_asm_data(f'extern {initd.dtr[1][1][0].name}:proc\n')
                            continue

                    self.write_asm_data(f'    ; Declaration\n')
        else:
            # self.write_asm(f'    ; Declaration\n')
            if self.dss[0].type_data == 'int':
                # self.write_asm(f'    ; Declaration {self.dss[0].type_data}\n')

                for item in self.idl:
                    if item.dtr[0]:  # pointer
                        pass
                    else:
                        name = item.dtr[1][1][0].name

                        if item.dtr[1][0] == 'var':  # declaration
                            # print(item.dtr[1][1])
                            # self.write_asm(f'    ; Declaration var {self.dss[0].type_data} {item.dtr[1][1][0].name}\n')
                            self.compiler.add_function_stack_offset(8)
                            self.write_asm(f'    sub rsp, 8 ; Declaration var {self.dss[0].type_data} {name} offset = {self.compiler.get_function_stack_offset()}\n')

                            scope_item = {'type':self.dss[0].type_data, 'name':name, 'offset':self.compiler.get_function_stack_offset()}
                            # self.compiler.scope[-1].append({'type':self.dss[0].type_data, 'name':item.dtr[1][1][0].name, 'offset':self.compiler.get_function_stack_offset()})
                            self.compiler.scope[-1][scope_item['name']] = scope_item

                            print_red(f'{name} item.init = {item.init}')
                            if isinstance(item.init, AssignmentExpression):
                                item.init.gen_asm(scope_item['offset'])

                        elif item.dtr[1][0] == 'array':
                            # print(item.dtr[1][1])
                            self.write_asm(f'    ; Declaration array {self.dss[0].type_data} {name}\n')

                            print_red(f'dtr size {len(item.dtr[1][1])}')
                            for ditem in item.dtr[1][1]:
                                print_red(f'{ditem}')
            else:
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
            self.type_data.print_me(indent + 4)
        else:
            print(f'{" " * (indent + 4)}{self.type_data}')


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
        print(f'{" " * (indent + 4)}name = {self.name}')
        if self.decls:
            for decl in self.decls:
                # if bi.hasattr('print_me'):
                if hasattr(decl, 'print_me'):
                    decl.print_me(indent + 4)
                else:
                    print(f'{" " * (indent + 4)}{decl}')
        else:
            print(f'{" " * (indent + 4)}NoObject()')


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
                bi.print_me(indent + 4)
            else:
                print(f'{" " * (indent + 4)}{bi}')

    def gen_asm(self, result_offset = None):
        for bi in self.bil:
            #print_red(f'bi = {bi}')

            # if hasattr(bi, 'gen_asm'):
            #     bi.gen_asm(result_offset)
            # else:
            #     bi.gen_asm(result_offset)

            if isinstance(bi, Declaration):
                bi.gen_asm()
            else:
                bi.gen_asm(result_offset)


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
                bi.print_me(indent + 4)
            else:
                print(f'{" " * (indent + 4)}{bi}')


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
                item.print_me(indent + 4)
            else:
                print(f'{" " * (indent + 4)}{item}')

    def gen_asm(self):
        if self.data[0] not in ['case', 'default']:
            self.write_asm(f'    {self.data[0].name}:\n')


class Expression(CComponent):
    # assignment-expression
    # expression , assignment-expression

    def __init__(self, compiler, data: list):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'Expression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}Expression len = {self.data_count}')
        for item in self.data:
            # if bi.hasattr('print_me'):
            if hasattr(item, 'print_me'):
                item.print_me(indent + 4)
            else:
                print(f'{" " * (indent + 4)}{item}')

    def gen_asm(self, my_result_offset):
        print(f'Expression gen_asm scope = {self.compiler.scope}')

        for item in self.data:
            # self.write_asm(f'    ; Expression\n')
            # print_yellow(item)
            self.write_asm(f'\n    ; Expression start offset = {self.compiler.get_function_stack_offset()} my_result_offset = {my_result_offset}\n')
            item.gen_asm(my_result_offset)
            self.write_asm(f'    ; Expression over offset = {self.compiler.get_function_stack_offset()}\n\n')


class AssignmentExpression(CComponent):
    # conditional-expression
    # unary-expression assignment-operator assignment-expression
    def __init__(self, compiler, ce = NoObject(), ue = NoObject(), opt = NoObject(), ae = NoObject()):
        super().__init__(compiler)
        self.ce = ce
        self.ue = ue
        self.opt = opt
        self.ae = ae

    def __repr__(self):
        return f'AssignmentExpression {self.ce, self.ue, self.opt, self.ae}'

    def print_me(self, indent):
        print(f'{" " * indent}AssignmentExpression')
        if self.ce:
            print(f'{" " * (indent + 4)}{self.ce}')
        else:
            print(f'{" " * (indent + 4)}{self.ue}')
            print(f'{" " * (indent + 4)}{self.opt}')
            self.ae.print_me(indent + 4)

    def gen_asm(self, my_result_offset):
        print(f'AssignmentExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')
        if self.ce:
            self.ce.gen_asm(my_result_offset)
        else:
            # self.write_asm(f'    sub rsp 8; space for unary-expression\n')
            # self.compiler.add_function_stack_offset(8)
            data = self.ue.gen_asm()
            if data['type'] == 'var':
                # '=', '*=', '/=', '%=', '+=', '-=', '<<=', '>>=', '&=', '^=', '|='
                # v1 = xxx
                if self.opt == '=':
                    self.ae.gen_asm(data['offset'])


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
        print(f'{" " * (indent + 4)}{self.loe, self.exp, self.ce}')

    def gen_asm(self, my_result_offset):
        print(f'ConditionalExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')
        if not self.exp:
            self.loe.gen_asm(my_result_offset)
        else:
            self.loe.gen_asm(my_result_offset)
            self.write_asm(f'    ; ConditionalExpression test le result\n')
            self.exp.gen_asm()
            self.ce.gen_asm()


'''
caller makes space at my_result_offset

gen_asm(self, my_result_offset):
    choose a reg like r12
    push r12
    make slots for subitems results
    gen_asm(slot) for each subitem
    calc results, may use r12.
    save final result in my_result_offset
    free space
    pop r12
'''


class LogicalOrExpression(CComponent):
    # logical-and-expression
    # logical-or-expression || logical-and-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'LogicalOrExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}LogicalOrExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'LogicalOrExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        if self.data_count == 1:
            return self.data[0].gen_asm(my_result_offset)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; LogicalOrExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            item.gen_asm(offset)
            offset += 8

        # todo use loop in asm
        '''
            cmp v1 0
            jne cmp_or_ok

            cmp v2 0
            jne cmp_or_ok

            ...

            cmp vx 0
            jne cmp_or_ok

            mov r12, 0
            jmp cmp_done

            cmp_or_ok:
                mov r12, 1
            cmp_done:
        '''

        label_1_name = f'cmp_or_ok_{self.compiler.item_id}'
        self.compiler.item_id += 1
        label_2_name = f'cmp_done_{self.compiler.item_id}'
        self.compiler.item_id += 1

        for index in range(0, self.data_count):
            self.write_asm(f'    cmp qword ptr [rbp - {result_offset}], 0\n    jne {label_1_name}\n')
            result_offset += 8

        # set result
        self.write_asm(f'    mov qword ptr [rbp - {my_result_offset}], 0\n    jmp {label_2_name}\n    {label_1_name}:\n')
        self.write_asm(f'        mov qword ptr [rbp - {my_result_offset}], 1\n    {label_2_name}:\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; LogicalOrExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)


class LogicalAndExpression(CComponent):
    # inclusive-or-expression
    # logical-and-expression && inclusive-or-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'LogicalAndExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}LogicalAndExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'LogicalAndExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        if self.data_count == 1:
            return self.data[0].gen_asm(my_result_offset)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; LogicalAndExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            item.gen_asm(offset)
            offset += 8

        # todo use loop in asm
        '''
            cmp v1 0
            je cmp_and_fail
            
            cmp v2 0
            je cmp_and_fail
            
            ...
            
            cmp vx 0
            je cmp_and_fail
            
            mov r12, 1
            jmp cmp_done
            
            cmp_and_fail:
                mov r12, 0
            cmp_done:
        '''

        label_1_name = f'cmp_and_fail_{self.compiler.item_id}'
        self.compiler.item_id += 1
        label_2_name = f'cmp_done_{self.compiler.item_id}'
        self.compiler.item_id += 1

        for index in range(0, self.data_count):
            self.write_asm(f'    cmp qword ptr [rbp - {result_offset}], 0\n    je {label_1_name}\n')
            result_offset += 8

        # set result
        self.write_asm(f'    mov qword ptr [rbp - {my_result_offset}], 1\n    jmp {label_2_name}\n    {label_1_name}:\n')
        self.write_asm(f'        mov qword ptr [rbp - {my_result_offset}], 0\n    {label_2_name}:\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; LogicalAndExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)


class InclusiveOrExpression(CComponent):
    # exclusive-or-expression
    # inclusive-or-expression | exclusive-or-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'InclusiveOrExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}InclusiveOrExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'InclusiveOrExpression gen_asm {my_result_offset = } {self.data_count = } {self.compiler.get_function_stack_offset()} scope = {self.compiler.scope}')

        # save r12
        self.write_asm(f'    push r12 ; save r12\n')
        self.compiler.add_function_stack_offset(8)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; InclusiveOrExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            item.gen_asm(offset)
            offset += 8

        # first to r12
        self.write_asm(f'    mov r12, [rbp - {result_offset}] ; InclusiveOrExpression get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            '''
            and r12, xxx
            '''
            self.write_asm(f'    or r12, [rbp - {result_offset}]\n')

        # set result
        if my_result_offset:
            self.write_asm(f'    mov [rbp - {my_result_offset}], r12 ; InclusiveOrExpression set result\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; InclusiveOrExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)
        self.write_asm(f'    pop r12 ; InclusiveOrExpression recover r12\n')
        self.compiler.add_function_stack_offset(-8)

class ExclusiveOrExpression(CComponent):
    # and-expression
    # exclusive-or-expression ^ and-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'ExclusiveOrExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}ExclusiveOrExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'ExclusiveOrExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        # save r12
        self.write_asm(f'    push r12 ; save r12\n')
        self.compiler.add_function_stack_offset(8)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; ExclusiveOrExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            item.gen_asm(offset)
            offset += 8

        # first to r12
        self.write_asm(f'    mov r12, [rbp - {result_offset}] ; ExclusiveOrExpression get first result. offset = {self.compiler.get_function_stack_offset()}\n')

        for index in range(1, self.data_count):
            result_offset += 8
            '''
            and r12, xxx
            '''
            self.write_asm(f'    xor r12, [rbp - {result_offset}]\n')

        # set result
        if my_result_offset:
            self.write_asm(f'    mov [rbp - {my_result_offset}], r12 ; ExclusiveOrExpression set result\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; ExclusiveOrExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)
        self.write_asm(f'    pop r12 ; ExclusiveOrExpression recover r12\n')
        self.compiler.add_function_stack_offset(-8)


class AndExpression(CComponent):
    # equality-expression
    # and-expression & equality-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'AndExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}AndExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'AndExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        # save r12
        self.write_asm(f'    push r12 ; save r12\n')
        self.compiler.add_function_stack_offset(8)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; AndExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            item.gen_asm(offset)
            offset += 8

        # first to r12
        self.write_asm(f'    mov r12, [rbp - {result_offset}] ; AndExpression get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            '''
            and r12, xxx
            '''
            self.write_asm(f'    and r12, [rbp - {result_offset}]\n')

        # set result
        if my_result_offset:
            self.write_asm(f'    mov [rbp - {my_result_offset}], r12 ; set result\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; AndExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)
        self.write_asm(f'    pop r12 ; AndExpression recover r12\n')
        self.compiler.add_function_stack_offset(-8)


class EqualityExpression(CComponent):
    # relational-expression
    # equality-expression == relational-expression
    # equality-expression != relational-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'EqualityExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}EqualityExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'EqualityExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        # save r12
        self.write_asm(f'    push r12 ; save r12\n')
        self.compiler.add_function_stack_offset(8)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; EqualityExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            # print_yellow(item)
            # pprint.pprint(item, indent = 4, width = 1)
            item[1].gen_asm(offset)
            offset += 8
            # print_yellow(f'asm_result = {asm_result}')

        # first to r12
        self.write_asm(f'    mov r12, [rbp - {result_offset}] ; EqualityExpression get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            label_1_name = f'cmp_label_{self.compiler.item_id}'
            self.compiler.item_id += 1
            label_2_name = f'cmp_label_{self.compiler.item_id}'
            self.compiler.item_id += 1

            if self.data[index][0] == '==':
                '''
                cmp r12, xxx
                je label_1
                mov r12, 0
                jmp label_2
                label_1:
                    mov r12, 1
                label_2:
                '''

                self.write_asm(f'    cmp r12, [rbp - {result_offset}]\n    je {label_1_name}\n    mov r12, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov r12, 1\n    {label_2_name}:\n')
            elif self.data[index][0] == '！=':
                self.write_asm(f'    cmp r12, [rbp - {result_offset}]\n    jne {label_1_name}\n    mov r12, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov r12, 1\n    {label_2_name}:\n')
            else:
                raise CompilerError(f'wtf')

        # set result
        if my_result_offset:
            self.write_asm(f'    mov [rbp - {my_result_offset}], r12 ; EqualityExpression set result\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; EqualityExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)
        self.write_asm(f'    pop r12 ; EqualityExpression recover r12\n')
        self.compiler.add_function_stack_offset(-8)


class RelationalExpression(CComponent):
    # shift-expression
    # relational-expression < shift-expression
    # relational-expression > shift-expression
    # relational-expression <= shift-expression
    # relational-expression >= shift-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'RelationalExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}RelationalExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'RelationalExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        # save r12
        self.write_asm(f'    push r12 ; save r12\n')
        self.compiler.add_function_stack_offset(8)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; RelationalExpression for exp result. offset = {self.compiler.get_function_stack_offset()}\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            # print_yellow(item)
            # pprint.pprint(item, indent = 4, width = 1)
            item[1].gen_asm(offset)
            offset += 8

        # first to r12
        self.write_asm(f'    mov r12, [rbp - {result_offset}] ; RelationalExpression get first result. offset = {self.compiler.get_function_stack_offset()}\n')

        for index in range(1, self.data_count):
            result_offset += 8

            label_1_name = f'cmp_label_{self.compiler.item_id}'
            self.compiler.item_id += 1
            label_2_name = f'cmp_label_{self.compiler.item_id}'
            self.compiler.item_id += 1

            if self.data[index][0] == '<':
                '''
                cmp r12, xxx
                jl label_1
                mov r12, 0
                jmp label_2
                label_1:
                    mov r12, 1
                label_2:
                '''

                self.write_asm(f'    cmp r12, [rbp - {result_offset}]\n    jl {label_1_name}\n    mov r12, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov r12, 1\n    {label_2_name}:\n')
            elif self.data[index][0] == '>':
                self.write_asm(f'    cmp r12, [rbp - {result_offset}]\n    jg {label_1_name}\n    mov r12, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov r12, 1\n    {label_2_name}:\n')
            elif self.data[index][0] == '<=':
                self.write_asm(f'    cmp r12, [rbp - {result_offset}]\n    jle {label_1_name}\n    mov r12, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov r12, 1\n    {label_2_name}:\n')
            elif self.data[index][0] == '>=':
                self.write_asm(f'    cmp r12, [rbp - {result_offset}]\n    jge {label_1_name}\n    mov r12, 0\n    jmp {label_2_name}\n    {label_1_name}:\n        mov r12, 1\n    {label_2_name}:\n')
            else:
                raise CompilerError(f'wtf')

        # set result
        if my_result_offset:
            self.write_asm(f'    mov [rbp - {my_result_offset}], r12 ; RelationalExpression set result\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; RelationalExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)
        self.write_asm(f'    pop r12 ; RelationalExpression recover r12\n')
        self.compiler.add_function_stack_offset(-8)


class ShiftExpression(CComponent):
    # additive-expression
    # shift-expression << additive-expression
    # shift-expression >> additive-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'ShiftExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}ShiftExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'ShiftExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        # save r12
        self.write_asm(f'    push r12 ; save r12\n')
        self.compiler.add_function_stack_offset(8)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; ShiftExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            # print_yellow(item)
            # pprint.pprint(item, indent = 4, width = 1)
            item[1].gen_asm(offset)
            offset += 8
            # print_yellow(f'asm_result = {asm_result}')

        # first to r12
        self.write_asm(f'    mov r12, [rbp - {result_offset}] ; ShiftExpression get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            # shift at most 8bit?

            self.write_asm(f'    push rcx\n')
            self.write_asm(f'    mov rcx, [rbp - {result_offset}]\n')
            if self.data[index][0] == '<<':
                self.write_asm(f'    shl r12, cl\n')
            elif self.data[index][0] == '>>':
                self.write_asm(f'    shr r12, cl\n')
            else:
                raise CompilerError(f'wtf')
            self.write_asm(f'    pop rcx\n')

        # set result
        if my_result_offset:
            self.write_asm(f'    mov [rbp - {my_result_offset}], r12 ; ShiftExpression set result\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; ShiftExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)
        self.write_asm(f'    pop r12 ; ShiftExpression recover r12\n')
        self.compiler.add_function_stack_offset(-8)


class AdditiveExpression(CComponent):
    # multiplicative-expression
    # additive-expression + multiplicative-expression
    # additive-expression - multiplicative-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'AdditiveExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}AdditiveExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'AdditiveExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        # save r12
        self.write_asm(f'    push r12 ; save r12\n')
        self.compiler.add_function_stack_offset(8)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; AdditiveExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            # print_yellow(item)
            # pprint.pprint(item, indent = 4, width = 1)
            item[1].gen_asm(offset)
            offset += 8

        # first to r12
        self.write_asm(f'    mov r12, [rbp - {result_offset}] ; AdditiveExpression get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            if self.data[index][0] == '+':
                self.write_asm(f'    add r12, [rbp - {result_offset}]\n')
            elif self.data[index][0] == '-':
                self.write_asm(f'    sub r12, [rbp - {result_offset}]\n')
            else:
                raise CompilerError(f'wtf')

        # set result
        if my_result_offset:
            self.write_asm(f'    mov [rbp - {my_result_offset}], r12 ; AdditiveExpression set result\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; AdditiveExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)
        self.write_asm(f'    pop r12 ; AdditiveExpression recover r12\n')
        self.compiler.add_function_stack_offset(-8)


class MultiplicativeExpression(CComponent):
    # cast-expression
    # multiplicative-expression * cast-expression
    # multiplicative-expression / cast-expression
    # multiplicative-expression % cast-expression

    def __init__(self, compiler, data):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'MultiplicativeExpression {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}MultiplicativeExpression')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, my_result_offset):
        print(f'MultiplicativeExpression gen_asm {my_result_offset = } scope = {self.compiler.scope}')

        # save r12
        self.write_asm(f'    push r12 ; save r12\n')
        self.compiler.add_function_stack_offset(8)

        # space for exp results
        self.write_asm(f'    sub rsp, {8 * self.data_count} ; MultiplicativeExpression for exp result\n')
        offset = self.compiler.get_function_stack_offset() + 8
        self.compiler.add_function_stack_offset(8 * self.data_count)

        result_offset = offset

        # gen_asm for each
        for item in self.data:
            # print_yellow(item)
            # pprint.pprint(item, indent = 4, width = 1)
            item[1].gen_asm(offset)
            offset += 8

        # first to r12
        self.write_asm(f'    mov r12, [rbp - {result_offset}] ; MultiplicativeExpression get first result\n')

        for index in range(1, self.data_count):
            result_offset += 8

            # print_orange(f'MultiplicativeExpression item = {self.data[index]}')
            if self.data[index][0] == '*':
                self.write_asm(f'    imul r12, [rbp - {result_offset}]\n')
            elif self.data[index][0] == '/':
                # 32-bit int
                # edx:eax / dword ptr [rbp - {result_offset}]
                # quotient in eax, remainder in edx.

                # todo: corner case?
                self.write_asm(f'    push rdx\n')
                self.write_asm(f'    push rax\n')
                self.write_asm(f'    mov rdx, r12 ; set edx\n')
                self.write_asm(f'    shr rdx, 32\n')
                self.write_asm(f'    mov rax, r12 ; set eax\n')
                self.write_asm(f'    and rax, right_32f\n') # 0xffffffff
                self.write_asm(f'    div dword ptr [rbp - {result_offset}]\n')
                self.write_asm(f'    mov r12, rax\n') # save result to r12
                self.write_asm(f'    pop rax\n')
                self.write_asm(f'    pop rdx\n')
            elif self.data[index][0] == '%':
                # todo: corner case?
                self.write_asm(f'    push rdx\n')
                self.write_asm(f'    push rax\n')
                self.write_asm(f'    mov rdx, r12 ; set edx\n')
                self.write_asm(f'    shr rdx, 32\n')
                self.write_asm(f'    mov rax, r12 ; set eax\n')
                self.write_asm(f'    and rax, right_32f\n')  # 0xffffffff
                self.write_asm(f'    div dword ptr [rbp - {result_offset}]\n')
                self.write_asm(f'    mov r12, rdx\n')  # save result to r12
                self.write_asm(f'    pop rax\n')
                self.write_asm(f'    pop rdx\n')

        # set result
        if my_result_offset:
            self.write_asm(f'    mov [rbp - {my_result_offset}], r12 ; MultiplicativeExpression set result\n')

        # pop
        self.write_asm(f'    add rsp, {8 * self.data_count} ; MultiplicativeExpression\n')
        self.compiler.add_function_stack_offset(-8 * self.data_count)
        self.write_asm(f'    pop r12 ; MultiplicativeExpression recover r12\n')
        self.compiler.add_function_stack_offset(-8)


class CastExpression(CComponent):
    # unary-expression
    # ( type-name ) cast-expression

    def __init__(self, compiler, casts, ue):
        super().__init__(compiler)
        self.casts = casts
        self.ue = ue

    def __repr__(self):
        return f'CastExpression {self.casts, self.ue}'

    def print_me(self, indent):
        print(f'{" " * indent}CastExpression')
        print(f'{" " * (indent + 4)}{self.casts}')
        print(f'{" " * (indent + 4)}{self.ue}')

    def gen_asm(self, result_offset = None):
        print(f'CastExpression gen_asm {result_offset = } scope = {self.compiler.scope}')
        # print(self.ue)
        return self.ue.gen_asm(result_offset)


class UnaryExpression(CComponent):
    # postfix-expression
    # ++ unary-expression
    # -- unary-expression
    # unary-operator cast-expression
    # sizeof unary-expression
    # sizeof ( type-name )

    def __init__(self, compiler, pe = NoObject(), pp = NoObject(), mm = NoObject(), ue = NoObject(), uo = NoObject(),
                 cast = NoObject(), sizeof = NoObject(), tn = NoObject()):
        super().__init__(compiler)
        self.pe = pe
        self.pp = pp
        self.mm = mm
        self.ue = ue
        self.uo = uo
        self.cast = cast
        self.sizeof = sizeof
        self.tn = tn

    def __repr__(self):
        return f'UnaryExpression {self.pe, self.pp, self.mm, self.ue, self.uo, self.cast, self.sizeof, self.tn}'

    def print_me(self, indent):
        print(f'{" " * indent}UnaryExpression')
        print(f'{" " * (indent + 4)}{self.pe, self.pp, self.mm, self.ue, self.uo, self.cast, self.sizeof, self.tn}')

    def gen_asm(self, result_offset = None):
        print(f'UnaryExpression gen_asm {result_offset = } scope = {self.compiler.scope}')
        if self.pe:
            return self.pe.gen_asm(result_offset)
        elif self.pp:
            data = self.ue.gen_asm(result_offset)
            if data['type'] == 'const':
                raise CompilerError(f'++ on const')

            self.write_asm(f'    inc qword ptr [rbp - {result_offset}] ; --\n')
            return data
        elif self.mm:
            data = self.ue.gen_asm(result_offset)
            if data['type'] == 'const':
                raise CompilerError(f'-- on const')

            self.write_asm(f'    dec qword ptr [rbp - {result_offset}] ; ++\n')
            return data
        elif self.uo:
            # ['&', '*', '+', '-', '~', '!']
            if self.uo == '-':
                self.cast.gen_asm(result_offset)

                # c std 6.5.3.3
                self.write_asm(f'    neg qword ptr [rbp - {result_offset}] ; negation\n')

class PostfixExpression(CComponent):
    # primary-expression
    # postfix-expression [ expression ]
    # postfix-expression ( argument-expression-list? )
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
        print(f'{" " * (indent + 4)}{self.primary}')
        print(f'{" " * (indent + 4)}{self.data}')

    def gen_asm(self, result_offset = None):
        print(f'PostfixExpression gen_asm {result_offset = } scope = {self.compiler.scope}')
        # print(self.ue)
        # self.pe.gen_asm()

        # for item in self.data:
        #    self.write_asm(f'    ;PostfixExpression item\n')

        if self.primary.idf:
            if self.data_count == 0:
                return self.primary.gen_asm(result_offset)

            for item in self.data:
                if item == '++':
                    # print_red(f'scope = {self.compiler.scope[-1]}')

                    scope_item = self.compiler.scope[-1].get(self.primary.idf.name, None)
                    if scope_item is None:
                        raise CompilerError(f'{self.primary.idf.name} not found')

                    self.write_asm(f'    inc qword ptr [rbp - {scope_item["offset"]}] ; {self.primary.idf.name}++\n')
                    # self.write_asm(f'    add qword ptr [rbp - {scope_item["offset"]}], 1; {self.pe.idf.name}++\n')
                elif item == '--':
                    scope_item = self.compiler.scope[-1].get(self.primary.idf.name, None)
                    if scope_item is None:
                        raise CompilerError(f'{self.primary.idf.name} not found')

                    self.write_asm(f'    dec qword ptr [rbp - {scope_item["offset"]}] ; {self.primary.idf.name}--\n')
                elif item[0] == '.':
                    self.write_asm(f'    ; {self.primary.idf.name}.{item[1]}\n')
                elif item[0] == '->':
                    self.write_asm(f'    ; {self.primary.idf.name}->{item[1]}\n')
                elif item[0] == 'array index':
                    self.write_asm(f'    ; {self.primary.idf.name}[exp]\n')
                elif item[0] == 'function call':
                    # print_red(item)
                    # print_red(item[1])
                    # print_red(len(item[1]))

                    scope_item = self.compiler.scope[-1].get(self.primary.idf.name, None)
                    if scope_item is None:
                        raise CompilerError(f'{self.primary.idf.name} not found')

                    print_yellow(f'arg item = {item}')
                    args_count = len(item[1])

                    # save args count to r15

                    # stack
                    #   r15
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
                    # 1 for r15
                    align = ((1 + abi_storage_args_count) * 8 + self.compiler.get_function_stack_offset()) % 16
                    if align not in [0, 8]:
                        raise CompilerError(f'check alignment before call align = {align} not in [0, 8]')

                    if align != 0:
                        self.write_asm(f'    sub rsp, 8 ; padding for function call\n')
                        self.compiler.add_function_stack_offset(8)

                    self.write_asm(f'    push r15 ; save r15\n')
                    self.compiler.add_function_stack_offset(8)
                    self.write_asm(f'    mov r15, {args_count}; {args_count = }\n')

                    # space for args
                    self.write_asm(f'    sub rsp, {8 * abi_storage_args_count} ; for function call args\n')
                    self.compiler.add_function_stack_offset(8 * abi_storage_args_count)

                    last_offset = self.compiler.get_function_stack_offset()
                    self.write_asm(f'    ; last_offset = {last_offset}\n')

                    # gen_asm for each arg
                    for arg in item[1]:
                        print_red(f'arg = {arg}')
                        arg.gen_asm(last_offset)
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

                    self.write_asm(f'    mov [rbp - {result_offset}], rax ; save call result\n')

                    # clean
                    self.write_asm(f'    add rsp, {8 * abi_storage_args_count} ; clean for function call args\n')
                    self.compiler.add_function_stack_offset(-8 * abi_storage_args_count)
                    self.write_asm(f'    pop r15 ; recover r15\n')
                    self.compiler.add_function_stack_offset(-8)

                    if align != 0:
                        self.write_asm(f'    add rsp, 8 ; clean padding for function call\n')
                        self.compiler.add_function_stack_offset(-8)

                else:
                    raise CompilerError(f'unknown postfix data {item}')
        elif self.primary.const:
            if self.data_count > 0:
                raise CompilerError(f'postfix on const')

            return self.primary.gen_asm(result_offset)

        elif self.primary.string:
            # "13ef"[0]; legal but ...
            if self.data_count > 0:
                raise CompilerError(f'postfix on const')

            return self.primary.gen_asm(result_offset)
        else:
            self.primary.exp.gen_asm(result_offset)


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
        # print(f'{" " * (indent + 4)}{self.type}')
        # print(f'{" " * (indent + 4)}{self.data}')
        if self.idf:
            print(f'{" " * (indent + 4)}{self.idf}')
        elif self.const:
            print(f'{" " * (indent + 4)}{self.const}')
        elif self.string:
            print(f'{" " * (indent + 4)}{self.string}')
        else:
            print(f'{" " * (indent + 4)}{self.exp}')

    def gen_asm(self, result_offset = None):
        print(f'PrimaryExpression gen_asm {result_offset = } scope = {self.compiler.scope}')
        # f.write(f'    ; {self.exp}\n')
        if self.idf:
            # self.write_asm(f'    ; PrimaryExpression get idf {self.idf}\n')
            # return 'idf', self.idf.name

            scope_item = self.compiler.scope[-1].get(self.idf.name, None)
            if scope_item is None:
                raise CompilerError(f'{self.idf.name} not found')

            if result_offset:
                self.write_asm(f'    push rax\n')
                self.write_asm(f'    mov rax, [rbp - {scope_item["offset"]}] ; move var {self.idf.name}\n')
                self.write_asm(f'    mov [rbp - {result_offset}], rax ; move var {self.idf.name} to offset {result_offset}\n')
                self.write_asm(f'    pop rax\n')

            return {'type':'var', 'name':self.idf.name, 'offset':scope_item['offset']}
        elif self.const:
            # self.write_asm(f'    ; PrimaryExpression get const {self.const}\n')
            # return 'const', self.const
            self.write_asm(f'    mov qword ptr [rbp - {result_offset}], {self.const.const} ; mov const\n')
            return {'type':'const', 'value':self.const.const}
        elif self.string:
            if len(self.string) == 0:
                raise CompilerError('empty string')

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
                        raise CompilerError(f'string escape error')

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
            self.write_asm(f'    lea r14, {string_var_name} ; load string {string_var_name}\n')
            self.write_asm(f'    mov [rbp - {result_offset}], r14 ; load string {string_var_name}\n')

            return {'type':'string', 'name':string_var_name}
        else:
            return self.exp.gen_asm()


class ExpressionStatement(CComponent):
    # expression? ;

    def __init__(self, compiler, exp: Expression):
        super().__init__(compiler)
        self.exp = exp

    def __repr__(self):
        return f'ExpressionStatement {self.exp}'

    def print_me(self, indent):
        print(f'{" " * indent}ExpressionStatement')
        self.exp.print_me(indent + 4)

    def gen_asm(self, my_result_offset):
        print(f'ExpressionStatement gen_asm {my_result_offset = } scope = {self.compiler.scope}')
        # f.write(f'    ; {self.exp}\n')
        # f.write(f'    ; ExpressionStatement\n')
        if self.exp:
            self.exp.gen_asm(my_result_offset)


class SelectionStatement(CComponent):
    # if ( expression ) statement
    # if ( expression ) statement else statement
    # switch ( expression ) statement

    def __init__(self, compiler, data: list):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'SelectionStatement {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}SelectionStatement len = {self.data_count}')
        for item in self.data:
            # if bi.hasattr('print_me'):
            if hasattr(item, 'print_me'):
                item.print_me(indent + 4)
            else:
                print(f'{" " * (indent + 4)}{item}')


class IterationStatement(CComponent):
    # while ( expression ) statement
    # do statement while ( expression ) ;
    # for ( expression? ; expression? ; expression? ) statement
    # for ( declaration expression? ; expression? ) statement

    def __init__(self, compiler, data: list):
        super().__init__(compiler)
        self.data = data
        self.data_count = len(data)

    def __repr__(self):
        return f'IterationStatement {self.data}'

    def print_me(self, indent):
        print(f'{" " * indent}IterationStatement len = {self.data_count}')
        for item in self.data:
            # if bi.hasattr('print_me'):
            if hasattr(item, 'print_me'):
                item.print_me(indent + 4)
            else:
                print(f'{" " * (indent + 4)}{item}')


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
            print(f'{" " * (indent + 4)}goto {self.idf.name}')
        elif self.cmd == 'return':
            print(f'{" " * (indent + 4)}return {self.exp}')
        else:
            print(f'{" " * (indent + 4)}{self.cmd}')

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
        # self.dtr.print_me(indent + 4)
        print(f'{" " * (indent + 4)}dtr = {self.dtr}')
        # self.init.print_me(indent + 4)
        print(f'{" " * (indent + 4)}init = {self.init}')


class Constant(CComponent):
    def __init__(self, compiler, const):
        super().__init__(compiler)
        self.const = const

    def __repr__(self):
        return f'Constant({self.const})'

    def print_me(self, indent):
        print(f'{" " * indent}Constant')
        # self.dtr.print_me(indent + 4)
        print(f'{" " * (indent + 4)}{self.const}')
        # self.init.print_me(indent + 4)


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
        # self.dtr.print_me(indent + 4)
        # print(f'{" " * (indent + 4)}{self.name}')
        # self.init.print_me(indent + 4)
