# cranks c compiler
# 民科野生c语言编译器
# 20240322 xc create


import sys
import os
import io
import traceback
import functools
import subprocess
# import locale
import datetime
import copy
import pprint
import json

import compiler.component as comp
import compiler.tool as tool
from compiler.tool import CompilerError, CodeError


class Scope:
    def __init__(self, outer = {}):
        self.current = {}
        self.outer = outer
        self.variable_stack_size = 0

    def __repr__(self):
        return f'current = {pprint.pformat(self.current)}\nouter = {pprint.pformat(self.outer)}\nvariable_stack_size = {self.variable_stack_size}'


class Compiler:
    def __init__(self, ml64_path, win_sdk_lib_path):
        self.ml64_path = ml64_path
        self.win_sdk_lib_path = win_sdk_lib_path
        self.depth = 0
        self.print_depth = False
        self.print_parsing = False
        self.saved_index = None
        self.source_file_index = None
        self.source_file_buffer = None
        self.source_file_buffer_len = None
        self.typedef_names = []
        self.keywords = {'auto', 'double', 'int', 'struct', 'break', 'else', 'long', 'switch', 'case', 'enum',
                         'register', 'typedef', 'char', 'extern', 'return', 'union', 'const', 'float', 'short',
                         'unsigned', 'continue', 'for', 'signed', 'void', 'default', 'goto', 'sizeof', 'volatile', 'do',
                         'if', 'static', 'while'}

        # self.out_f = open('./output/cranks_compiler.log', 'w', encoding = 'utf8')
        self.asm_head = io.StringIO()
        self.asm_data = io.StringIO()  # .data
        self.asm_code = io.StringIO()  # .code

        self.current_function = None
        self.current_lineno = 1

        # for label name
        # todo
        self.item_id = 0

        # two set for each scope. current and outer

        # default ({}, {})
        #     scope A ({A}, {})
        #         scope B ({B}, {A})
        #             scope C ({C}, {AB})
        #                 scope D ({D}, {ABC})
        #         scope E ({E}, {A})

        self.scopes = [Scope()] # default empty

    def init(self):
        self.depth = 0
        self.asm_head = io.StringIO()
        self.asm_data = io.StringIO()  # .data
        self.asm_code = io.StringIO()  # .code
        self.current_function = None
        self.current_lineno = 1
        self.item_id = 0
        self.scopes = [Scope()]  # default empty
        self.source_file_index = -1

    def enter_scope(self):
        # combine to new_outer
        new_outer = copy.deepcopy(self.scopes[-1].outer)
        new_outer.update(self.scopes[-1].current)
        self.scopes.append(Scope(new_outer))

    def leave_scope(self):
        self.scopes.pop()

    def add_function_stack_offset(self, offset):
        self.current_function.offset += offset
        return self.current_function.offset

    def get_function_stack_offset(self):
        return self.current_function.offset


    def go_deep(func):
        @functools.wraps(func)
        def do_go_deep(self, *args, **kwargs):
            self.depth += 1
            if self.depth > 100:
                # self.dbg('fuck depth')
                # exit(0)
                raise CompilerError(f'fuck depth [{self.depth}]')
            ret = func(self, *args, **kwargs)
            self.depth -= 1
            return ret

        return do_go_deep

    def dbg(self, text):
        if self.print_parsing:
            if self.print_depth:
                # print(f'\33[38;5;1m[depth = {self.depth:04}]{" " * (self.depth * 2)}{text}')
                print(f'[depth = {self.depth:04}]{" " * (self.depth * 2)}{text}')
            else:
                print(f'{text}')

    def dbg_ok(self, text):
        if self.print_depth:
            tool.print_green(f'[depth = {self.depth:04}]{" " * (self.depth * 2)}{text}')
        else:
            tool.print_green(f'{text}')

    def dbg_fail(self, text):
        if self.print_depth:
            tool.print_red(f'[depth = {self.depth:04}]{" " * (self.depth * 2)}{text}')
        else:
            tool.print_red(f'{text}')

    def dbg_yellow(self, text):
        if self.print_depth:
            tool.print_yellow(f'[depth = {self.depth:04}]{" " * (self.depth * 2)}{text}')
        else:
            tool.print_yellow(f'{text}')

    def error(self, text):
        tool.print_orange(f'{text}')
        sys.exit(0)

    def getc(self):
        self.source_file_index += 1

        if self.source_file_index < self.source_file_buffer_len:
            c = self.source_file_buffer[self.source_file_index]
            if c == '\n':
                self.current_lineno += 1
                self.dbg(f'{self.current_lineno = }')

            self.dbg(f'getc return {c = }')
            return c

        return None

    def getc_skip_white(self):
        while True:
            c = self.getc()
            if c.isspace():
                self.dbg('space')
            else:
                return c

    def skip_white(self):
        while True:
            c = self.getc()
            if c is None:
                return False

            if not c.isspace():
                self.source_file_index -= 1
                return True

    def now_all_white(self):
        self.dbg(f'now_all_white')
        index = self.source_file_index
        while True:
            index += 1
            if index >= self.source_file_buffer_len:
                return True

            c = self.source_file_buffer[index]
            if not c.isspace():
                self.dbg(f'not c.isspace() {c}')
                return False

    def save(self):
        return self.source_file_index, self.current_lineno

    def load(self, save_data):
        self.source_file_index, self.current_lineno = save_data

    def get_index(self):
        return self.source_file_index

    def set_index(self, index):
        self.source_file_index = index

    def raise_code_error(self, msg = ''):
        raise CodeError(f'line {self.current_lineno}: {msg}')


    @go_deep
    def get_template(self):
        # rule
        self.dbg(f'get_template')
        save_1 = self.save()


        # fail
        self.load(save_1)
        self.dbg(f'get_template return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_translation_unit(self):
        # external-declaration
        # translation-unit external-declaration

        self.dbg(f'get_translation_unit')

        eds = []

        while True:
            save_1 = self.save()

            ed = self.get_external_declaration()

            if ed:
                eds.append(ed)
                continue
            else:
                self.load(save_1)

                self.skip_white()

                if not self.now_all_white():
                    self.raise_code_error(f'get declaration failed')

                break

        self.dbg(f'get_translation_unit return {eds}')
        return comp.TranslationUnit(self, eds)

    @go_deep
    def get_external_declaration(self):
        # function-definition
        # declaration

        self.dbg(f'get_external_declaration')
        save_1 = self.save()

        fd = self.get_function_definition()
        if fd:
            self.dbg(f'get_external_declaration return {fd}')
            return fd

        self.load(save_1)

        decl = self.get_declaration()
        if decl:
            self.dbg(f'get_external_declaration return {decl}')
            return decl

        self.load(save_1)
        self.dbg(f'get_external_declaration return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_function_definition(self):
        # declaration-specifiers declarator declaration-list? compound-statement

        # declaration-list? is unusual, replace with
        # declaration-specifiers declarator compound-statement

        self.dbg(f'get_function_definition')
        save_1 = self.save()

        dss = self.get_declaration_specifiers(for_what = 'function_definition')
        if dss:
            declarator = self.get_declarator(for_what = 'function_definition')
            if declarator:
                # dl = self.get_declaration_list()
                cs = self.get_compound_statement()
                if cs:
                    # self.dbg_ok(f'get_function_definition return {(dss, declarator, dl, cs)}')
                    fd = comp.FunctionDefinition(self, dss, declarator, cs)
                    self.dbg(f'get_function_definition return {(dss, declarator, cs)}')
                    return fd

        self.load(save_1)
        self.dbg(f'get_function_definition return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_declaration_list(self):
        # declaration
        # declaration-list declaration
        self.dbg(f'get_declaration_list')
        save_1 = self.save()

        decl = self.get_declaration()
        if decl:
            decls = [decl]
            while True:
                decl = self.get_declaration()
                if decl:
                    decls.append(decl)
                else:
                    self.dbg(f'get_declaration_list return {decls}')
                    return decls

        self.load(save_1)
        self.dbg(f'get_declaration_list return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_compound_statement(self):
        # { block-item-list }

        self.dbg(f'get_compound_statement')
        save_1 = self.save()

        if self.get_a_string('{'):
            bil = self.get_block_item_list()
            if self.get_a_string('}'):
                self.dbg(f'get_compound_statement return {bil}')
                # return bil
                return comp.CompoundStatement(self, bil)

        self.load(save_1)
        self.dbg(f'get_compound_statement return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_block_item_list(self):
        # block-item
        # block-item-list block-item
        self.dbg(f'get_block_item_list')
        save_1 = self.save()

        bil = []

        bi = self.get_block_item()
        if bi:
            bil = [bi]
            while True:
                save_2 = self.save()

                bi = self.get_block_item()
                if bi:
                    bil.append(bi)
                else:
                    self.load(save_2)
                    break
        else:
            self.load(save_1)

        self.dbg(f'get_block_item_list return {bil}')
        return bil

    @go_deep
    def get_block_item(self):
        # declaration
        # statement
        self.dbg(f'get_block_item')
        save_1 = self.save()

        decl = self.get_declaration()
        if decl:
            self.dbg(f'get_block_item return {decl}')
            return decl

        self.load(save_1)

        stmt = self.get_statement()
        if stmt:
            self.dbg(f'get_block_item return {stmt}')
            return stmt

        self.load(save_1)
        self.dbg(f'get_block_item return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_statement(self):
        # labeled-statement
        # compound-statement
        # expression-statement
        # selection-statement
        # iteration-statement
        # jump-statement

        self.dbg(f'get_statement')
        save_1 = self.save()

        ls = self.get_labeled_statement()
        if ls:
            self.dbg(f'get_statement return {ls}')
            return ls

        cs = self.get_compound_statement()
        if cs:
            self.dbg(f'get_statement return {cs}')
            return cs

        es = self.get_expression_statement()
        if es:
            self.dbg(f'get_statement return {es}')
            return es

        ss = self.get_selection_statement()
        if ss:
            self.dbg(f'get_statement return {ss}')
            return ss

        its = self.get_iteration_statement()
        if its:
            self.dbg(f'get_statement return {its}')
            return its

        js = self.get_jump_statement()
        if js:
            self.dbg(f'get_statement return {js}')
            return js

        self.load(save_1)
        self.dbg(f'get_statement return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_labeled_statement(self):
        # identifier : statement
        # case constant-expression : statement
        # default : statement

        self.dbg(f'get_labeled_statement')
        save_1 = self.save()

        idf = self.get_identifier()
        if idf:
            if idf not in ['case', 'default']:
                if self.get_a_string(':'):
                    stmt = self.get_statement()
                    if stmt:
                        self.dbg(f'get_labeled_statement return {"identifier", idf, stmt}')
                        return comp.LabeledStatement(self, [idf, stmt])
            elif idf == 'case':
                ce = self.get_constant_expression()
                if ce:
                    if self.get_a_string(':'):
                        stmt = self.get_statement()
                        if stmt:
                            self.dbg(f'get_labeled_statement return {"case", ce, stmt}')
                            return comp.LabeledStatement(self, ['case', ce, stmt])
            elif idf == 'default':
                if self.get_a_string(':'):
                    stmt = self.get_statement()
                    if stmt:
                        self.dbg(f'get_labeled_statement return {"default", stmt}')
                        return comp.LabeledStatement(self, ['default', stmt])

        self.load(save_1)
        self.dbg(f'get_labeled_statement return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_iteration_statement(self):
        # while ( expression ) statement
        # do statement while ( expression ) ;
        # for ( expression? ; expression? ; expression? ) statement
        # for ( declaration expression? ; expression? ) statement

        self.dbg(f'get_iteration_statement')
        save_1 = self.save()

        idf = self.get_identifier()
        if idf == 'while':
            if self.get_a_string('('):
                exp = self.get_expression()
                if exp:
                    if self.get_a_string(')'):
                        stmt = self.get_statement()
                        if stmt:
                            self.dbg(f'get_selection_statement return {("while", exp, stmt)}')
                            return comp.IterationStatement(self, 0, exp_1 = exp, stmt = stmt)
        elif idf == 'do':
            stmt = self.get_statement()
            if stmt:
                idf = self.get_identifier()
                if idf == 'while':
                    if self.get_a_string('('):
                        exp = self.get_expression()
                        if exp:
                            if self.get_a_string(')'):
                                if self.get_a_string(';'):
                                    self.dbg(f'get_selection_statement return {("do", stmt, "while", exp)}')
                                    return comp.IterationStatement(self, 1, exp_1 = exp, stmt = stmt)
        elif idf == 'for':
            if self.get_a_string('('):
                save_2 = self.save()

                exp_1 = comp.NoObject()

                decl = self.get_declaration()
                if not decl:
                    self.load(save_2)

                    exp_1 = self.get_expression()
                    if not self.get_a_string(';'):
                        # fail
                        self.load(save_1)
                        self.dbg(f'get_iteration_statement return comp.NoObject()')
                        return comp.NoObject()

                exp_2 = self.get_expression()
                if self.get_a_string(';'):
                    exp_3 = self.get_expression()
                    if self.get_a_string(')'):
                        stmt = self.get_statement()
                        if stmt:
                            self.dbg(f'get_selection_statement return {("for", exp_1, exp_2, exp_3, stmt)}')
                            return comp.IterationStatement(self, 2, declaration = decl, exp_1 = exp_1, exp_2 = exp_2, exp_3 = exp_3, stmt = stmt)

        # fail
        self.load(save_1)
        self.dbg(f'get_iteration_statement return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_selection_statement(self):
        # if ( expression ) statement
        # if ( expression ) statement else statement
        # switch ( expression ) statement

        self.dbg(f'get_selection_statement')
        save_1 = self.save()

        idf = self.get_identifier()
        if idf == 'if':
            if self.get_a_string('('):
                exp = self.get_expression()
                if exp:
                    if self.get_a_string(')'):
                        stmt_1 = self.get_statement()
                        if stmt_1:
                            save_2 = self.save()
                            idf = self.get_identifier()
                            if idf == 'else':
                                stmt_2 = self.get_statement()
                                if stmt_2:
                                    self.dbg(f'get_selection_statement return {("if", exp, stmt_1, "else", stmt_2)}')
                                    return comp.SelectionStatement(self, exp = exp, stmt_1 = stmt_1, stmt_2 = stmt_2)

                            self.load(save_2)
                            self.dbg(f'get_selection_statement return {("if", exp, stmt_1)}')
                            return comp.SelectionStatement(self, exp = exp, stmt_1 = stmt_1)
        elif idf == 'switch':
            if self.get_a_string('('):
                exp = self.get_expression()
                if exp:
                    if self.get_a_string(')'):
                        stmt_1 = self.get_statement()
                        if stmt_1:
                            self.dbg(f'get_selection_statement return {("switch", exp, stmt_1)}')
                            return comp.SelectionStatement(self, switch = 'switch', exp = exp, stmt_1 = stmt_1)

        # fail
        self.load(save_1)
        self.dbg(f'get_selection_statement return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_expression_statement(self):
        # expression? ;

        self.dbg(f'get_expression_statement')
        save_1 = self.save()

        exp = self.get_expression()
        # if exp is None:
        #     exp = []

        if self.get_a_string(';'):
            self.dbg(f'get_expression_statement return {exp}')
            return comp.ExpressionStatement(self, exp)

        # fail
        self.load(save_1)
        self.dbg(f'get_expression_statement return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_jump_statement(self):
        # goto identifier ;
        # continue ;
        # break ;
        # return expression? ;

        self.dbg(f'get_jump_statement')
        save_1 = self.save()

        idf = self.get_identifier()

        save_2 = self.save()

        if idf == 'goto':
            idf = self.get_identifier()
            if idf:
                c = self.getc_skip_white()
                if c == ';':
                    self.dbg(f'get_jump_statement return {("goto", idf)}')
                    return comp.JumpStatement(self, cmd = 'goto', idf = idf)

        self.load(save_2)

        if idf == 'continue':
            c = self.getc_skip_white()
            if c == ';':
                self.dbg(f'get_jump_statement return {("continue", None)}')
                return comp.JumpStatement(self, cmd = 'continue')

        self.load(save_2)

        if idf == 'break':
            c = self.getc_skip_white()
            if c == ';':
                self.dbg(f'get_jump_statement return {("break", None)}')
                return comp.JumpStatement(self, cmd = 'break')

        self.load(save_2)

        if idf == 'return':
            exp = self.get_expression()
            if exp:
                pass
            else:
                pass

            c = self.getc_skip_white()
            if c == ';':
                self.dbg(f'get_jump_statement return {("return", exp)}')
                return comp.JumpStatement(self, cmd = 'return', exp = exp)

        # fail
        self.load(save_1)
        self.dbg(f'get_jump_statement return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_declaration(self):
        # declaration-specifiers init-declarator-list? ;

        # const int              a, b, *p, c = 666     ;
        # struct S1{int a;}      s1, s2 = {...}        ;
        # struct S2{int a, b;}                         ;
        # struct S3              s1, s2                ;
        # struct {int a, b;}     s1, s2                ;

        self.dbg(f'get_declaration')
        save_1 = self.save()

        dss = self.get_declaration_specifiers() # const int ...
        if dss:
            idl = self.get_init_declarator_list() # a, b, *p, c = 666

            if self.get_a_string(';'):
                declaration = comp.Declaration(self, dss, idl)
                self.dbg(f'get_declaration return {(dss, idl)}')
                # return dss, idl
                return declaration

        # fail
        self.load(save_1)
        self.dbg(f'get_declaration return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_init_declarator_list(self):
        # init-declarator
        # init-declarator-list , init-declarator
        self.dbg(f'get_init_declarator_list')
        save_1 = self.save()

        idt = self.get_init_declarator()
        if idt:
            idts = [idt]

            while True:
                save_2 = self.save()

                if self.get_a_string(','):
                    idt = self.get_init_declarator()
                    if idt:
                        idts.append(idt)
                        continue

                self.load(save_2)
                self.dbg(f'get_init_declarator_list return {idts}')
                return idts

        # fail
        self.dbg('get_init_declarator_list return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_init_declarator(self):
        # declarator
        # declarator = initializer

        self.dbg(f'get_init_declarator')
        save_1 = self.save()

        dtr = self.get_declarator()

        if dtr:
            save_2 = self.save()

            if self.get_a_string('='):
                init = self.get_initializer()
                if init:
                    self.dbg(f'get_init_declarator return {(dtr, init)}')
                    return comp.InitDeclarator(self, dtr, init)
            else:
                self.load(save_2)
                self.dbg(f'get_init_declarator return {(dtr, None)}')
                return comp.InitDeclarator(self, dtr, comp.NoObject())

        # fail
        self.load(save_1)
        self.dbg(f'get_init_declarator return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_declarator(self, for_what = None):
        # pointer? direct-declarator

        self.dbg(f'get_declarator')
        save_1 = self.save()

        pointer = self.get_pointer()
        if pointer:
            pass
        else:
            pass

        dd = self.get_direct_declarator(for_what = for_what)
        if dd:
            self.dbg(f'get_declarator return {(pointer, dd)}')
            return pointer, dd

        self.load(save_1)
        self.dbg(f'get_declarator return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_direct_declarator(self, for_what = None):
        # identifier
        # ( declarator )
        # direct-declarator [ constant-expression? ] # array decl
        # direct-declarator ( parameter-type-list ) # function
        # direct-declarator ( identifier-list? ) # function

        self.dbg(f'get_direct_declarator')
        save_1 = self.save()

        name = ''
        data_type = 'na' # var array function
        data = []

        idf = self.get_identifier()
        if idf:
            data_type = 'var'
            #data = [idf]
            name = idf.name
            # self.dbg(f'get_direct_declarator return {idf}')
            # return idf
        elif False: # no support # else:
            if self.get_a_string('('):
                decl = self.get_declarator()
                if decl:
                    if self.get_a_string(')'):
                        dd_type = 'var()'
                        data = [decl]

        # if data == []:
        if not idf:
            self.dbg(f'get_direct_declarator return comp.NoObject()')
            return comp.NoObject()

        array_data = {'dim':0, 'ranks':[]}

        while True:
            save_2 = self.save()

            if self.get_a_string('['):
                ce = self.get_constant_expression()
                if self.get_a_string(']'):
                    # data.append(ce)

                    if data_type == 'function':
                        raise CodeError(f'function decl followed by []')

                    self.dbg(f'ce = {ce}')

                    # raise  CompilerError(f'ce = {ce}')

                    data_type = 'array'
                    array_data['dim'] += 1
                    array_data['ranks'].append(ce)
                    continue

            self.load(save_2)

            if self.get_a_string('('):
                ptl = self.get_parameter_type_list()
                if ptl:
                    if self.get_a_string(')'):
                        if data_type == 'array':
                            raise CodeError(f'array decl followed by ()')

                        data.append(ptl)
                        data_type = 'function'
                        continue

            self.load(save_2)

            if self.get_a_string('('):
                idfs = self.get_identifier_list()
                if self.get_a_string(')'):
                    if data_type == 'array':
                        raise CodeError(f'array decl followed by ()')

                    data += idfs
                    data_type = 'function'
                    continue

            # all fail
            self.load(save_2)
            break

        return_data = {'type':data_type, 'name':name}
        if data_type == 'array':
            return_data['array_data'] = array_data

        self.dbg(f'get_direct_declarator return {return_data}')
        # return dd_type, data
        return return_data

    @go_deep
    def get_identifier_list(self):
        # identifier
        # identifier-list , identifier
        self.dbg(f'get_identifier_list')
        save_1 = self.save()

        idfs = []

        idf = self.get_identifier()
        if idf:
            idfs = [idf]
            while True:
                save_2 = self.save()

                idf = self.get_identifier()
                if idf:
                    idfs.append(idf)
                else:
                    self.load(save_2)
                    break
        else:
            self.load(save_1)

        self.dbg(f'get_identifier_list return {idfs}')
        return idfs

    @go_deep
    def get_parameter_type_list(self):
        # parameter-list
        # parameter-list , ...
        self.dbg(f'get_parameter_type_list')
        save_1 = self.save()

        pl = self.get_parameter_list()
        if pl:
            save_2 = self.save()
            if self.get_a_string(','):
                if self.get_a_string('...'):
                    self.dbg(f'get_parameter_type_list return {(pl, "...")}')
                    return pl, "..."

            self.load(save_2)
            self.dbg(f'get_parameter_type_list return {(pl, None)}')
            return pl, None

        self.load(save_1)
        self.dbg(f'get_parameter_type_list return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_parameter_list(self):
        # parameter-declaration
        # parameter-list , parameter-declaration
        self.dbg(f'get_parameter_list')
        save_1 = self.save()

        pd = self.get_parameter_declaration()
        if pd:
            pl = [pd]

            while True:
                save_2 = self.save()

                if self.get_a_string(','):
                    pd = self.get_parameter_declaration()
                    if pd:
                        pl.append(pd)
                        continue

                self.load(save_2)
                self.dbg(f'get_parameter_list return {pl}')
                return pl

        self.load(save_1)
        self.dbg(f'get_parameter_list return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_parameter_declaration(self):
        # declaration-specifiers declarator
        # declaration-specifiers abstract-declarator?
        self.dbg(f'get_parameter_declaration')
        save_1 = self.save()

        dss = self.get_declaration_specifiers()
        if dss:
            decl = self.get_declarator()
            if decl:
                self.dbg(f'get_parameter_declaration return {(dss, decl)}')
                return dss, decl

            ad = self.get_abstract_declarator()
            self.dbg(f'get_parameter_declaration return {(dss, ad)}')
            return dss, ad

        self.load(save_1)
        self.dbg(f'get_parameter_declaration return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_initializer(self):
        # assignment-expression
        # { initializer-list }
        # { initializer-list , }

        self.dbg(f'get_initializer')
        save_1 = self.save()

        ae = self.get_assignment_expression()
        if ae:
            self.dbg(f'get_initializer return {ae}')
            return ae

        self.load(save_1)

        if self.get_a_string('{'):
            il = self.get_initializer_list()
            if il:
                save_2 = self.save()

                if self.get_a_string('}'):
                    self.dbg(f'get_initializer return {il}')
                    return il

                self.load(save_2)
                if self.get_a_string(','):
                    if self.get_a_string('}'):
                        self.dbg(f'get_initializer return {il}')
                        return il

        # fail
        self.load(save_1)
        self.dbg(f'get_initializer return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_initializer_list(self):
        # designation? initializer
        # initializer-list , designation? initializer
        self.dbg(f'get_initializer_list')
        save_1 = self.save()

        dst = self.get_designation()
        if not dst:
            self.load(save_1)

        init = self.get_initializer()
        if init:
            data = [(dst, init)]

            while True:
                save_2 = self.save()
                if self.get_a_string(','):
                    save_3 = self.save()
                    dst = self.get_designation()
                    if not dst:
                        self.load(save_3)

                    init = self.get_initializer()
                    if init:
                        data.append((dst, init))
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_initializer_list return {data}')
            return data

        self.load(save_1)
        self.dbg(f'get_initializer_list return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_designation(self):
        # designator-list =
        self.dbg(f'get_designation')
        save_1 = self.save()

        dstl = self.get_designator_list()
        if dstl:
            if self.get_a_string('='):
                self.dbg(f'get_designation return {dstl}')
                return dstl

        self.load(save_1)
        self.dbg(f'get_designation return comp.NoObject()')
        return comp.NoObject()


    @go_deep
    def get_designator_list(self):
        # designator
        # designator-list designator
        self.dbg(f'get_designator_list')
        save_1 = self.save()

        dst = self.get_designator()
        if dst:
            dsts = [dst]

            while True:
                save_2 = self.save()
                dst = self.get_designator()
                if dst:
                    dsts.append(dst)
                else:
                    self.load(save_2)
                    self.dbg(f'get_designator return {dsts}')
                    return dsts

        self.load(save_1)
        self.dbg(f'get_designator return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_designator(self):
        # [ constant-expression ]
        # . identifier
        self.dbg(f'get_designator')
        save_1 = self.save()

        if self.get_a_string('['):
            ce = self.get_constant_expression()
            if ce:
                if self.get_a_string(']'):
                    self.dbg(f'get_designator return {ce}')
                    return ce

        self.load(save_1)

        if self.get_a_string('.'):
            idf = self.get_identifier()
            if idf:
                self.dbg(f'get_designator return {idf}')
                return idf

        self.load(save_1)
        self.dbg(f'get_designator return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_declaration_specifiers(self, for_what = None):
        # storage-class-specifier declaration-specifiers? # 'auto', 'register', 'static', 'extern', 'typedef'
        # type-specifier declaration-specifiers? # void int ...
        # type-qualifier declaration-specifiers? # 'const', 'volatile'
        # function-specifier declaration-specifiers?
        # alignment-specifier declaration-specifiers?

        self.dbg(f'get_declaration_specifiers')
        save_1 = self.save()

        storage_spec = None
        type_spec = None
        type_qua = None
        function_spec = None
        alignment_spec = None

        dss = []

        while True:
            save_2 = self.save()

            ss = self.get_storage_class_specifier()
            if ss:
                dss.append(('ss', ss))
                continue

            self.load(save_2)

            ts = self.get_type_specifier(for_what = for_what)
            if ts:
                if type_spec is not None:
                    raise CodeError(f'more than one TypeSpecifier {type_spec}')

                type_spec = ts
                # dss.append(ts)
                continue

            self.load(save_2)

            tq = self.get_type_qualifier()
            if tq:
                dss.append(('tq', tq))
                continue

            self.load(save_2)

            fs = self.get_function_specifier()
            if fs:
                dss.append(('fs', fs))
                continue

            self.load(save_2)

            aspec = self.get_alignment_specifier()
            if aspec:
                dss.append(('aspec', aspec))
                continue

            self.load(save_2)
            break

        if type_spec is not None: # if len(dss) != 0:
            self.dbg(f'get_declaration_specifiers return {type_spec, dss}')
            return type_spec, dss

        self.load(save_1)
        self.dbg(f'get_declaration_specifiers return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_declaration_specifiers_1(self):
        # storage-class-specifier declaration-specifiers*
        # type-specifier declaration-specifiers*
        # type-qualifier declaration-specifiers*
        # function-specifier declaration-specifiers*
        # alignment-specifier declaration-specifiers*

        self.dbg(f'get_declaration_specifiers')

        save_1 = self.save()

        storage_spec = None
        type_spec = None
        type_qua = None
        function_spec = None
        alignment_spec = None

        while True:
            save_2 = self.save()

            ss = self.get_storage_class_specifier()
            if ss:
                if storage_spec:
                    raise CodeError(f'more than one storage_spec')

                storage_spec = ss
                continue

            self.load(save_2)

            ts = self.get_type_specifier()
            if ts:
                if type_spec:
                    raise CodeError(f'more than one type_spec')

                type_spec = ts
                continue

            self.load(save_2)

            tq = self.get_type_qualifier()
            if tq:
                if type_qua:
                    raise CodeError(f'more than one type_qua')

                type_qua = tq
                continue

            self.load(save_2)

            fs = self.get_function_specifier()
            if fs:
                if function_spec:
                    raise CodeError(f'more than one function_spec')

                function_spec = fs
                continue

            self.load(save_2)

            aspec = self.get_alignment_specifier()
            if aspec:
                if alignment_spec:
                    raise CodeError(f'more than one alignment_spec')

                alignment_spec = aspec
                continue

            self.load(save_2)
            break

        if storage_spec or type_spec or type_qua or function_spec or alignment_spec:
            return (storage_spec, type_spec, type_qua, function_spec, alignment_spec)

        self.load(save_1)
        self.dbg(f'get_declaration_specifiers return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_storage_class_specifier(self):
        self.dbg(f'get_storage_class_specifier')

        idf = self.get_identifier()

        if idf in ['auto', 'register', 'static', 'extern', 'typedef']:
            self.dbg(f'get_storage_class_specifier return {idf}')
            return idf

        self.dbg(f'get_storage_class_specifier return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_type_specifier(self, for_what = None):
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
        self.dbg(f'get_type_specifier')
        save_1 = self.save()

        idf = self.get_identifier()

        if not idf:
            self.load(save_1)
            self.dbg(f'get_type_specifier return comp.NoObject()')
            return comp.NoObject()

        if idf.name in ['void', 'char', 'short', 'int', 'long', 'float', 'double', 'signed', 'unsigned']:
            self.dbg(f'get_type_specifier return {idf.name}')
            return comp.TypeSpecifier(self, idf.name)

        if idf.name in ['struct', 'union']:
            if for_what == 'function_definition':
                self.load(save_1)
                self.dbg(f'get_type_specifier return comp.NoObject()')
                return comp.NoObject()

            if False:
                head, idf, sds = self.get_struct_or_union_specifier(idf)
                if not idf and not sds:
                    self.dbg(f'get_type_specifier return comp.NoObject()')
                    return comp.NoObject()
                else:
                    self.dbg(f'get_type_specifier return {(head, idf, sds)}')
                    return head, idf, sds
            else:
                su = self.get_struct_or_union_specifier(idf.name)
                if su:
                    return comp.TypeSpecifier(self, su)

                self.dbg(f'get_type_specifier return comp.NoObject()')
                return comp.NoObject()

        if idf == 'enum':
            es = self.get_enum_specifier()
            if es:
                self.dbg(f'get_type_specifier return {("enum", es)}')
                return comp.TypeSpecifier(self, ("enum", es))

        # typedef-name
        # self.dbg(f'get_type_specifier return {("typedef", idf)}')
        # return "typedef", idf
        if idf.name in self.typedef_names:
            return comp.TypeSpecifier(self, ('typedef', idf))

        self.load(save_1)
        self.dbg(f'get_type_specifier return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_typedef_name(self):
        self.dbg(f'get_typedef_name')
        save_1 = self.save()

        idf = self.get_identifier()
        if idf:
            self.dbg(f'get_typedef_name return {idf}')
            return idf

        self.load(save_1)
        self.dbg(f'get_typedef_name return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_enum_specifier(self):
        # enum identifier? { enumerator-list }
        # enum identifier
        self.dbg(f'get_enum_specifier')
        save_1 = self.save()

        idf = self.get_identifier()

        save_2 = self.save()

        if self.get_a_string('{'):
            el = self.get_enumerator_list()
            if el:
                if self.get_a_string('}'):
                    self.dbg(f'get_enum_specifier return {("enum", idf, el)}')
                    return "enum", idf, el

        self.load(save_2)

        if idf:
            self.dbg(f'get_enum_specifier return {("enum", idf, comp.NoObject())}')
            return "enum", idf, comp.NoObject()

        self.load(save_1)
        self.dbg(f'get_enum_specifier return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_enumerator_list(self):
        # enumerator
        # enumerator-list , enumerator
        self.dbg(f'get_enumerator_list')
        save_1 = self.save()

        etr = self.get_enumerator()
        if etr:
            etrs = [etr]

            while True:
                save_2 = self.save()

                if self.get_a_string(','):
                    etr = self.get_enumerator()
                    if etr:
                        etrs.append(etr)
                        continue

                self.load(save_2)
                self.dbg(f'get_enumerator_list return {etrs}')
                return etrs

        self.load(save_1)
        self.dbg(f'get_enumerator_list return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_enumerator(self):
        # identifier
        # identifier = constant-expression
        self.dbg(f'get_enumerator')
        save_1 = self.save()

        idf = self.get_identifier()
        if idf:
            save_2 = self.save()

            if self.get_a_string('='):
                ce = self.get_constant_expression()
                if ce:
                    self.dbg(f'get_enumerator return {(idf, ce)}')
                    return idf, ce

            self.load(save_2)
            self.dbg(f'get_enumerator return {(idf, comp.NoObject())}')
            return idf, comp.NoObject()

        self.load(save_1)
        self.dbg(f'get_enumerator return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_function_specifier(self):
        # inline
        self.dbg(f'get_function_specifier')

        self.dbg(f'get_function_specifier return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_alignment_specifier(self):
        self.dbg(f'get_alignment_specifier')

        self.dbg(f'get_alignment_specifier return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_constant_expression(self):
        # conditional-expression

        self.dbg(f'get_constant_expression return comp.NoObject()')
        save_1 = self.save()

        ce = self.get_conditional_expression()

        if ce:
            self.dbg(f'get_constant_expression return {ce}')
            return ce

        self.load(save_1)
        self.dbg(f'get_constant_expression return comp.NoObject()')
        return comp.NoObject()


    @go_deep
    def get_conditional_expression(self):
        # logical-or-expression
        # logical-or-expression ? expression : conditional-expression

        self.dbg(f'get_conditional_expression')
        save_1 = self.save()

        loe = self.get_logical_or_expression()
        if loe:
            save_2 = self.save()
            if self.get_a_string('?'):
                exp = self.get_expression()
                if exp:
                    if self.get_a_string(':'):
                        ce = self.get_conditional_expression()
                        if ce:
                            new_ce = comp.ConditionalExpression(self, loe, exp, ce)
                            self.dbg(f'get_conditional_expression return {new_ce}')
                            return new_ce

            self.load(save_2)
            new_ce = comp.ConditionalExpression(self, loe, comp.NoObject(), comp.NoObject())
            self.dbg(f'get_conditional_expression return {new_ce}')
            return new_ce


        self.dbg(f'get_conditional_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_logical_or_expression(self):
        # logical-and-expression
        # logical-or-expression || logical-and-expression

        self.dbg(f'get_logical_or_expression')
        save_1 = self.save()

        lae = self.get_logical_and_expression()
        if lae:
            data = [lae]

            while True:
                save_2 = self.save()

                if self.get_a_string('||'):
                    lae = self.get_logical_and_expression()
                    if lae:
                        data.append(lae)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_logical_or_expression return {data}')
            return comp.LogicalOrExpression(self, data)

        self.dbg(f'get_logical_or_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_logical_and_expression(self):
        # inclusive-or-expression
        # logical-and-expression && inclusive-or-expression

        self.dbg(f'get_logical_and_expression')
        save_1 = self.save()

        ioe = self.get_inclusive_or_expression()
        if ioe:
            data = [ioe]

            while True:
                save_2 = self.save()

                if self.get_a_string('&&'):
                    lae = self.get_inclusive_or_expression()
                    if lae:
                        data.append(lae)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_logical_and_expression return {data}')
            return comp.LogicalAndExpression(self, data)

        self.dbg(f'get_logical_and_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_inclusive_or_expression(self):
        # exclusive-or-expression
        # inclusive-or-expression | exclusive-or-expression

        self.dbg(f'get_inclusive_or_expression')
        save_1 = self.save()

        eoe = self.get_exclusive_or_expression()
        if eoe:
            data = [eoe]

            while True:
                save_2 = self.save()

                if self.get_a_string('|'):
                    lae = self.get_exclusive_or_expression()
                    if lae:
                        data.append(lae)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_inclusive_or_expression return {data}')
            return comp.InclusiveOrExpression(self, data)

        self.dbg(f'get_inclusive_or_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_exclusive_or_expression(self):
        # and-expression
        # exclusive-or-expression ^ and-expression

        self.dbg(f'get_exclusive_or_expression')
        save_1 = self.save()

        ae = self.get_and_expression()
        if ae:
            data = [ae]

            while True:
                save_2 = self.save()

                if self.get_a_string('^'):
                    lae = self.get_and_expression()
                    if lae:
                        data.append(lae)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_exclusive_or_expression return {data}')
            return comp.ExclusiveOrExpression(self, data)

        self.dbg(f'get_exclusive_or_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_and_expression(self):
        # equality-expression
        # and-expression & equality-expression

        self.dbg(f'get_and_expression')
        save_1 = self.save()

        ee = self.get_equality_expression()
        if ee:
            data = [ee]

            while True:
                save_2 = self.save()

                if self.get_a_string('&'):
                    save_3 = self.save()
                    if self.getc() in '&=':  # avoid && &=
                        self.load(save_2)
                        break

                    self.load(save_3)

                    lae = self.get_equality_expression()
                    if lae:
                        data.append(lae)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_and_expression return {data}')
            return comp.AndExpression(self, data)

        self.dbg(f'get_and_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_equality_expression(self):
        # relational-expression
        # equality-expression == relational-expression
        # equality-expression != relational-expression

        self.dbg(f'get_equality_expression')
        save_1 = self.save()

        ree = self.get_relational_expression()
        if ree:
            data = [ree]

            while True:
                save_2 = self.save()

                if self.get_a_string('=='):
                    ree = self.get_relational_expression()
                    if ree:
                        ree.set_opt('==')
                        data.append(ree)
                        continue

                self.load(save_2)

                if self.get_a_string('!='):
                    ree = self.get_relational_expression()
                    if ree:
                        ree.set_opt('!=')
                        data.append(ree)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_equality_expression return {data}')
            return comp.EqualityExpression(self, data)

        self.dbg(f'get_equality_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_relational_expression(self):
        # shift-expression
        # relational-expression < shift-expression
        # relational-expression > shift-expression
        # relational-expression <= shift-expression
        # relational-expression >= shift-expression

        self.dbg(f'get_relational_expression')
        save_1 = self.save()

        se = self.get_shift_expression()
        if se:
            data = [se]

            while True:
                save_2 = self.save()

                if self.get_a_string('<'):
                    se = self.get_shift_expression()
                    if se:
                        se.set_opt('<')
                        data.append(se)
                        continue

                self.load(save_2)

                if self.get_a_string('>'):
                    se = self.get_shift_expression()
                    if se:
                        se.set_opt('>')
                        data.append(se)
                        continue

                self.load(save_2)

                if self.get_a_string('<='):
                    se = self.get_shift_expression()
                    if se:
                        se.set_opt('<=')
                        data.append(se)
                        continue

                self.load(save_2)

                if self.get_a_string('>='):
                    se = self.get_shift_expression()
                    if se:
                        se.set_opt('>=')
                        data.append(se)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_relational_expression return {data}')
            return comp.RelationalExpression(self, data)

        self.dbg(f'get_relational_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_shift_expression(self):
        # additive-expression
        # shift-expression << additive-expression
        # shift-expression >> additive-expression

        self.dbg(f'get_shift_expression')
        save_1 = self.save()

        ae = self.get_additive_expression()
        if ae:
            data = [ae]

            while True:
                save_2 = self.save()

                if self.get_a_string('<<'):
                    ae = self.get_additive_expression()
                    if ae:
                        ae.set_opt('<<')
                        data.append(ae)
                        continue

                self.load(save_2)

                if self.get_a_string('>>'):
                    ae = self.get_additive_expression()
                    if ae:
                        ae.set_opt('>>')
                        data.append(ae)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_shift_expression return {data}')
            return comp.ShiftExpression(self, data)

        self.dbg(f'get_shift_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_additive_expression(self):
        # multiplicative-expression
        # additive-expression + multiplicative-expression
        # additive-expression - multiplicative-expression

        self.dbg(f'get_additive_expression')
        save_1 = self.save()

        me = self.get_multiplicative_expression()
        if me:
            data = [me]

            while True:
                save_2 = self.save()

                if self.get_a_string('+'):
                    me = self.get_multiplicative_expression()
                    if me:
                        me.set_opt('+')
                        data.append(me)
                        continue

                self.load(save_2)

                if self.get_a_string('-'):
                    me = self.get_multiplicative_expression()
                    if me:
                        me.set_opt('-')
                        data.append(me)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_additive_expression return {data}')
            return comp.AdditiveExpression(self, data)

        self.dbg(f'get_additive_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_multiplicative_expression(self):
        # cast-expression
        # multiplicative-expression * cast-expression
        # multiplicative-expression / cast-expression
        # multiplicative-expression % cast-expression

        self.dbg(f'get_multiplicative_expression')
        save_1 = self.save()

        ce = self.get_cast_expression()
        if ce:
            data = [ce] # first

            while True:
                save_2 = self.save()

                if self.get_a_string('*'):
                    ce = self.get_cast_expression()
                    if ce:
                        ce.set_opt('*')
                        data.append(ce)
                        continue

                self.load(save_2)

                if self.get_a_string('/'):
                    ce = self.get_cast_expression()
                    if ce:
                        ce.set_opt('/')
                        data.append(ce)
                        continue

                self.load(save_2)

                if self.get_a_string('%'):
                    ce = self.get_cast_expression()
                    if ce:
                        ce.set_opt('%')
                        data.append(ce)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_multiplicative_expression return {data}')
            return comp.MultiplicativeExpression(self, data)

        self.dbg(f'get_multiplicative_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()


    @go_deep
    def get_expression(self):
        # assignment-expression
        # expression , assignment-expression

        self.dbg(f'get_expression')
        save_1 = self.save()

        ae = self.get_assignment_expression()
        if ae:
            aes = [ae]

            while True:
                save_2 = self.save()

                if self.get_a_string(','):
                    ae = self.get_assignment_expression()
                    if ae:
                        aes.append(ae)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_expression return {aes}')
            return comp.Expression(self, aes)

        # fail
        self.dbg(f'get_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()


    @go_deep
    def get_assignment_expression(self):
        # conditional-expression
        # unary-expression assignment-operator assignment-expression

        # greedy？

        self.dbg(f'get_assignment_expression')
        save_1 = self.save()

        ue = self.get_unary_expression()
        if ue:
            opt = self.get_assignment_operator()
            if opt:
                ae = self.get_assignment_expression()
                if ae:
                    ass = comp.AssignmentExpression(self, ue = ue, opt = opt, ae = ae)
                    self.dbg(f'get_assignment_expression return {ass}')
                    return ass

        self.load(save_1)

        ce = self.get_conditional_expression()
        if ce:
            ass = comp.AssignmentExpression(self, ce = ce)
            self.dbg(f'get_assignment_expression return {ass}')
            return ass

        self.load(save_1)
        self.dbg(f'get_assignment_expression return comp.NoObject()')
        return comp.NoObject()


    @go_deep
    def get_unary_expression(self):
        # postfix-expression
        # ++ unary-expression
        # -- unary-expression
        # unary-operator cast-expression
        # sizeof unary-expression
        # sizeof ( type-name )

        self.dbg(f'get_unary_expression')
        save_1 = self.save()

        pe = self.get_postfix_expression()
        if pe:
            new_ue = comp.UnaryExpression(self, pe = pe)
            self.dbg(f'get_unary_expression return {new_ue}')
            return new_ue

        self.load(save_1)

        if self.get_a_string('++'):
            ue = self.get_unary_expression()
            if ue:
                new_ue = comp.UnaryExpression(self, pp = '++', ue = ue)
                self.dbg(f'get_unary_expression return {new_ue}')
                return new_ue

        self.load(save_1)

        if self.get_a_string('--'):
            ue = self.get_unary_expression()
            if ue:
                new_ue = comp.UnaryExpression(self, pp = '--', ue = ue)
                self.dbg(f'get_unary_expression return {new_ue}')
                return new_ue

        self.load(save_1)

        # cast
        uo = self.get_unary_operator()
        if uo:
            cast = self.get_cast_expression()
            if cast:
                new_ue = comp.UnaryExpression(self, uo = uo, cast = cast)
                self.dbg(f'get_unary_expression return {new_ue}')
                return new_ue

        self.load(save_1)

        idf = self.get_identifier()
        if idf == 'sizeof':
            ue = self.get_unary_expression()
            if ue:
                new_ue = comp.UnaryExpression(self, ue = ue, sizeof = 'sizeof')
                self.dbg(f'get_unary_expression return {new_ue}')
                return new_ue

            if self.get_a_string('('):
                tn = self.get_type_name()
                if tn:
                    if self.get_a_string(')'):
                        new_ue = comp.UnaryExpression(self, sizeof = 'sizeof', tn = tn)
                        self.dbg(f'get_unary_expression return {new_ue}')
                        return new_ue

        self.load(save_1)
        self.dbg(f'get_unary_expression return comp.NoObject()')
        return comp.NoObject()


    @go_deep
    def get_assignment_operator(self):
        # = *= /= %= += -= <<= >>= &= ^= |=

        self.dbg(f'get_assignment_operator')
        save_1 = self.save()

        ops = ['=', '*=', '/=', '%=', '+=', '-=', '<<=', '>>=', '&=', '^=', '|=']

        for op in ops:
            save_2 = self.save()
            if self.get_a_string(op):
                if op == '=':
                    save_3 = self.save()
                    # avoid ==
                    if self.getc() == '=':
                        self.load(save_2)
                        continue

                    self.load(save_3)

                self.dbg(f'get_assignment_operator return {op}')
                return op
            else:
                self.load(save_1)

        # fail
        self.dbg(f'get_assignment_operator return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_cast_expression(self):
        # unary-expression
        # ( type-name ) cast-expression

        self.dbg(f'get_cast_expression')
        save_1 = self.save()

        casts = []

        while True:
            save_2 = self.save()

            if self.get_a_string('('):
                tn = self.get_type_name()
                if tn:
                    if self.get_a_string(')'):
                        casts.append(tn)
                        continue

            self.load(save_2)
            ue = self.get_unary_expression()
            if ue:
                cast = comp.CastExpression(self, casts, ue)
                self.dbg(f'get_cast_expression return {cast}')
                return cast

            # fail
            break

        self.dbg(f'get_cast_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_type_name(self):
        # specifier-qualifier-list abstract-declarator?

        self.dbg(f'get_type_name')
        save_1 = self.save()

        sql = self.get_specifier_qualifier_list()
        if sql:
            ad = self.get_abstract_declarator()
            self.dbg(f'get_type_name return {(sql, ad)}')
            return sql, ad

        self.dbg(f'get_type_name return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_abstract_declarator(self):
        # pointer
        # pointer? direct-abstract-declarator
        self.dbg(f'get_abstract_declarator')
        save_1 = self.save()

        ptr = self.get_pointer()
        if ptr:
            dad = self.get_direct_abstract_declarator()
            return ptr, dad
        else:
            dad = self.get_direct_abstract_declarator()
            if dad:
                return comp.NoObject(), dad

        self.dbg(f'get_abstract_declarator return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_direct_abstract_declarator(self):
        # ( abstract-declarator )
        #  direct-abstract-declarator? [ constant-expression? ]
        #  direct-abstract-declarator? ( parameter-type-list? )

        self.dbg(f'get_direct_abstract_declarator')
        save_1 = self.save()

        ad = comp.NoObject()

        if self.get_a_string('('):
            ad = self.get_abstract_declarator()
            if ad:
                if self.get_a_string(')'):
                    pass
                else:
                    ad = comp.NoObject()
                    self.load(save_1)

        data = []

        while True:
            save_2 = self.save()

            if self.get_a_string('['):
                ce = self.get_constant_expression()

                if self.get_a_string(']'):
                    data.append(('ce', ce))
                    continue

            self.load(save_2)

            if self.get_a_string('('):
                ptl = self.get_parameter_type_list()

                if self.get_a_string(')'):
                    data.append(('ptl', ptl))
                    continue

            self.load(save_2)
            break

        if len(data) != 0:
            self.dbg(f'get_direct_abstract_declarator return {(ad, data)}')
            return ad, data

        self.dbg(f'get_direct_abstract_declarator return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_unary_operator(self):

        self.skip_white()

        c = self.getc()
        if c in ['&', '*', '+', '-', '~', '!']:
            return c

        self.source_file_index -= 1
        return comp.NoObject()

    @go_deep
    def get_postfix_expression(self):
        # primary-expression
        # postfix-expression [ expression ]
        # postfix-expression ( argument-expression-list? )
        # postfix-expression . identifier
        # postfix-expression -> identifier
        # postfix-expression ++
        # postfix-expression --

        self.dbg(f'get_postfix_expression')
        save_1 = self.save()

        primary = self.get_primary_expression()
        if primary:
            data = []

            while True:
                save_2 = self.save()

                if self.get_a_string('['):
                    exp = self.get_expression()
                    if exp:
                        if self.get_a_string(']'):
                            data.append(('array index', exp))
                            continue

                self.load(save_2)

                if self.get_a_string('('):
                    aes = self.get_argument_expression_list()
                    if self.get_a_string(')'):
                        data.append(('function call', aes))
                        continue

                self.load(save_2)

                if self.get_a_string('.'):
                    idf = self.get_identifier()
                    if idf:
                        data.append(('.', idf))
                        continue

                self.load(save_2)

                if self.get_a_string('->'):
                    idf = self.get_identifier()
                    if idf:
                        data.append(('->', idf))
                        continue

                self.load(save_2)

                if self.get_a_string('++'):
                    data.append('++')
                    continue

                self.load(save_2)

                if self.get_a_string('--'):
                    data.append('--')
                    continue

                self.load(save_2)
                break

            self.dbg(f'get_postfix_expression return {(primary, data)}')
            return comp.PostfixExpression(self, primary, data)

        self.load(save_1)
        self.dbg(f'get_postfix_expression return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_argument_expression_list(self):
        # assignment-expression
        # argument-expression-list , assignment-expression

        self.dbg(f'get_argument_expression_list')
        save_1 = self.save()

        ae = self.get_assignment_expression()
        if ae:
            aes = [ae]

            while True:
                save_2 = self.save()

                if self.get_a_string(','):
                    ae = self.get_assignment_expression()
                    if ae:
                        aes.append(ae)
                        continue

                self.load(save_2)
                break

            self.dbg(f'get_argument_expression_list return {aes}')
            return aes

        self.dbg(f'get_argument_expression_list return comp.NoObject()')
        self.load(save_1)
        # return comp.NoObject()
        return []

    @go_deep
    def get_primary_expression(self):
        # identifier
        # constant
        # string-literal
        # ( expression )

        self.dbg(f'get_primary_expression')

        save_1 = self.save()

        idf = self.get_identifier()
        if idf and idf.name not in self.keywords:
            self.dbg(f'get_primary_expression return {idf}')
            return comp.PrimaryExpression(self, idf = idf)

        self.load(save_1)

        const = self.get_constant()
        if const:
            self.dbg(f'get_primary_expression return {const}')
            return comp.PrimaryExpression(self, const = const)

        self.load(save_1)

        string = self.get_string_literal()
        if string:
            self.dbg(f'get_primary_expression return {string}')
            return comp.PrimaryExpression(self, string = string)

        self.load(save_1)

        if self.get_a_string('('):
            exp = self.get_expression()
            if exp:
                if self.get_a_string(')'):
                    self.dbg(f'get_primary_expression return {exp}')
                    return comp.PrimaryExpression(self, exp = exp)

        self.dbg(f'get_primary_expression return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_string_literal(self):
        # encoding-prefix? " s-char-sequence? "
        self.dbg(f'get_string_literal')
        save_1 = self.save()

        if self.get_a_string('"'):
            string = ''
            while True:
                c = self.getc()
                if c is None:
                    return comp.NoObject()
                elif c == '\\': # todo
                    # pass
                    string += c
                elif c == '"':
                    return string
                else:
                    string += c

        self.dbg(f'get_string_literal return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_constant(self):
        # integer-constant
        # character-constant
        # floating-constant
        # enumeration-constant

        self.dbg(f'get_constant')
        save_1 = self.save()

        ic = self.get_integer_constant()
        if ic:
            self.dbg(f'get_integer_constant {ic}')
            return ic

        self.dbg(f'get_constant return comp.NoObject()')
        self.load(save_1)
        return comp.NoObject()

    @go_deep
    def get_integer_constant(self):
        # decimal-constant integer-suffix?
        # octal-constant integer-suffix?
        # hexadecimal-constant integer-suffix?

        self.dbg(f'get_integer_constant')
        save_1 = self.save()

        dc = self.get_decimal_constant()
        if dc:
            self.dbg(f'get_integer_constant {dc}')
            return comp.Constant(self, 'int', int(dc, 10))

        # 0x first
        hc = self.get_hexadecimal_constant()
        if hc:
            self.dbg(f'get_integer_constant {hc}')
            return comp.Constant(self, 'int', int(hc, 16))

        oc = self.get_octal_constant()
        if oc:
            self.dbg(f'get_integer_constant {oc}')
            return comp.Constant(self, 'int', int(oc, 8))

        self.load(save_1)
        self.dbg(f'get_integer_constant return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_hexadecimal_constant(self):
        # hexadecimal-prefix hexadecimal-digit
        # hexadecimal-constant hexadecimal-digit

        self.dbg(f'get_hexadecimal_constant')
        save_1 = self.save()

        if not self.get_a_string('0x') and not self.get_a_string('0X'):
            self.load(save_1)
            self.dbg(f'get_hexadecimal_constant return comp.NoObject()')
            return comp.NoObject()

        string = '0x'

        while True:
            c = self.getc()
            if c.isdigit() and c in '0123456789abcdefABCDEF':
                string += c
                continue
            # elif c.isspace():
            #     return int(string)
            # elif c.isalpha() or c == '':
            #     return int(string)
            else:
                self.source_file_index -= 1
                self.dbg(f'get_hexadecimal_constant return {int(string, 16)}')
                # return int(string, 8)
                return string

        self.load(save_1)
        self.dbg(f'get_hexadecimal_constant return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_octal_constant(self):
        # 0
        # octal-constant octal-digit

        self.dbg(f'get_octal_constant')
        save_1 = self.save()

        c = self.getc_skip_white()
        if c == '0':
            string = c

            while True:
                c = self.getc()
                if c in '01234567':
                    string += c
                    continue
                # elif c.isspace():
                #     return int(string)
                # elif c.isalpha() or c == '':
                #     return int(string)
                else:
                    self.source_file_index -= 1
                    self.dbg(f'get_octal_constant return {int(string, 8)}')
                    # return int(string, 8)
                    return string

        self.load(save_1)
        self.dbg(f'get_octal_constant return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_decimal_constant(self):
        # nonzero-digit
        # decimal-constant digit

        self.dbg(f'get_decimal_constant')
        save_1 = self.save()

        c = self.getc_skip_white()
        if c.isdigit() and c != '0':
            string = c

            while True:
                c = self.getc()
                if c.isdigit():
                    string += c
                    continue
                # elif c.isspace():
                #     return int(string)
                # elif c.isalpha() or c == '':
                #     return int(string)
                else:
                    self.source_file_index -= 1
                    # return int(string)
                    self.dbg(f'get_decimal_constant return {string}')
                    return string

        self.load(save_1)
        self.dbg(f'get_decimal_constant return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_typedef_name(self):
        idf = self.get_identifier()

        return idf

    @go_deep
    def get_type_qualifier(self):
        # const
        # volatile

        self.dbg(f'get_type_qualifier')
        save_1 = self.save()

        idf = self.get_identifier()
        if idf in ['const', 'volatile']:
            self.dbg(f'get_type_qualifier return {idf}')
            return idf.name

        self.load(save_1)
        self.dbg(f'get_type_qualifier return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_type_qualifier_list(self):
        # type-qualifier
        # type-qualifier-list type-qualifier

        self.dbg(f'get_type_qualifier_list')
        save_1 = self.save()

        tq = self.get_type_qualifier()
        if tq:
            data = [tq]

            while True:
                tq = self.get_type_qualifier()
                if tq:
                    data.append(tq)
                else:
                    self.dbg(f'get_type_qualifier_list return {data}')
                    return data

        self.load(save_1)
        self.dbg(f'get_type_qualifier_list return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_struct_or_union_specifier(self, head):
        # struct-or-union identifier? { struct-declaration-list }
        # struct-or-union identifier

        # struct          S1          { int a, b; ... }
        # struct                      { int a, b; ... }
        # struct          S2

        # 1. define a full struct. with name that can be used later.
        # 2. disposable struct. use once.
        # 3. S2 must exist

        self.dbg(f'get_struct_or_union_specifier')
        save_1 = self.save()

        idf = self.get_identifier()

        save_2 = self.save()

        if self.get_a_string('{'):
            sdl = self.get_struct_declaration_list()
            if sdl:
                if self.get_a_string('}'):
                    # ok
                    self.dbg(f'get_struct_or_union_specifier return {(head, idf.name, sdl)}')
                    return comp.StructUnion(self, head, idf.name, sdl)

        self.load(save_2)
        if idf:
            self.dbg(f'get_struct_or_union_specifier return {(head, idf.name, comp.NoObject())}')
            return comp.StructUnion(self, head, idf.name, comp.NoObject())

        # failed
        self.load(save_1)
        self.dbg(f'get_struct_or_union_specifier return comp.NoObject()')
        return comp.NoObject()


    @go_deep
    def get_struct_declaration_list(self):
        # struct-declaration
        # struct-declaration-list struct-declaration

        self.dbg(f'get_struct_declaration_list')
        save_1 = self.save()

        sd = self.get_struct_declaration()
        if sd:
            sds = [sd]

            while True:
                sd = self.get_struct_declaration()
                if sd:
                    sds.append(sd)
                    continue

                self.dbg(f'get_struct_declaration_list return {sds}')
                return sds

        self.load(save_1)
        self.dbg(f'get_struct_declaration_list return comp.NoObject()')
        return comp.NoObject()


    @go_deep
    def get_struct_declaration(self):
        # specifier-qualifier-list struct-declarator-list ;

        self.dbg(f'get_struct_declaration')
        save_1 = self.save()

        sql = self.get_specifier_qualifier_list() # const int ...
        if sql:
            sdl = self.get_struct_declarator_list()
            if sdl:
                if self.get_a_string(';'):
                    self.dbg(f'get_struct_declaration return {(sql, sdl)}')
                    return sql, sdl

        self.load(save_1)
        self.dbg(f'get_struct_declaration return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_struct_declarator_list(self):
        # struct-declarator
        # struct-declarator-list , struct-declarator
        self.dbg(f'get_struct_declarator_list')
        save_1 = self.save()

        sd = self.get_struct_declarator()
        if sd:
            sds = [sd]

            while True:
                save_2 = self.save()

                if self.get_a_string(','):
                    sd = self.get_struct_declarator()
                    if sd:
                        sds.append(sd)
                        continue

                self.load(save_2)
                self.dbg(f'get_struct_declarator_list return {sds}')
                return sds

        self.load(save_1)
        self.dbg(f'get_struct_declarator_list return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_struct_declarator(self):
        # declarator
        # declarator? : constant-expression
        self.dbg(f'get_struct_declarator')
        save_1 = self.save()

        dect = self.get_declarator()

        save_2 = self.save()
        if self.get_a_string(':'):
            ce = self.get_constant_expression()
            if ce:
                self.dbg(f'get_struct_declarator return {(dect, ce)}')
                return dect, ce

        self.load(save_2)

        if dect:
            self.dbg(f'get_struct_declarator return {(dect, None)}')
            return dect, None

        self.load(save_1)
        self.dbg(f'get_struct_declarator return comp.NoObject()')
        return comp.NoObject()



    @go_deep
    def get_pointer(self):
        # * type-qualifier-list?
        # * type-qualifier-list? pointer

        # * *const *const * * * *
        # * = [[]]
        # * *const * = [[], ['const'], []]

        self.dbg(f'get_pointer')
        save_1 = self.save()

        ptrs = []

        while True:
            if self.get_a_string('*'):
                tql = self.get_type_qualifier_list()
                if not tql:
                    tql = []
                ptrs.append(tql)
                continue

            break

        if True: # len(ptrs) != 0:
            self.dbg(f'get_pointer return {ptrs}')
            return ptrs

        self.load(save_1)
        self.dbg(f'get_pointer return comp.NoObject()')
        return comp.NoObject()

        #####

        if not self.get_a_string('*'):
            self.load(save_1)
            self.dbg(f'get_pointer return comp.NoObject()')
            return comp.NoObject()

        tqs = []
        while True:
            tq = self.get_type_qualifier()
            if tq:
                tqs.append(tq)
            else:
                break

        save_1 = self.save()

        pointer = self.get_pointer()
        if pointer:
            self.dbg(f'get_pointer return True')
            return True
        else:
            self.load(save_1)
            self.dbg(f'get_pointer return comp.NoObject()')
            return comp.NoObject()

    @go_deep
    def get_specifier_qualifier_list(self):
        # type-specifier specifier-qualifier-list?
        # type-qualifier specifier-qualifier-list?

        # if no type-specifier, default int.

        self.dbg(f'get_specifier_qualifier_list')
        save_1 = self.save()

        data = []

        ts = None # allow only one ts

        while True:
            save_2 = self.save()
            new_ts = self.get_type_specifier()
            if new_ts:
                if ts:
                    raise CodeError(f'more than one type-specifier {new_ts}')
                data.append(new_ts)
                ts = new_ts
                continue

            tq = self.get_type_qualifier()
            if tq:
                data.append(tq)
                continue

            self.load(save_2)
            break

        if ts is None:
            data.append(comp.TypeSpecifier(self, 'int'))

        if len(data) != 0:
            self.dbg(f'get_specifier_qualifier_list return {data}')
            return data

        self.load(save_1)
        self.dbg(f'get_specifier_qualifier_list return comp.NoObject()')
        return comp.NoObject()

    @go_deep
    def get_identifier_nondigit(self):
        return self.get_nondigit()

    @go_deep
    def get_identifier(self):
        # identifier-nondigit
        #    identifier identifier-nondigit
        #    identifier digit

        # must start with an identifier-nondigit, followed by identifier-nondigit or digit.

        self.dbg(f'get_identifier')
        self.skip_white()

        # save_1 = self.save()

        c = self.get_identifier_nondigit() # get a nondigit

        if c is None:
            self.dbg(f'get_identifier return comp.NoObject()')
            # self.load(save_1)
            return comp.NoObject()
        else:
            idf = c

            while True:
                c = self.get_identifier_nondigit()  # get a nondigit
                if c:
                    idf += c
                    continue

                c = self.get_digit()  # get a digit
                if c:
                    idf += c
                    continue

                break

            self.skip_white()
            self.dbg(f'get_identifier return {idf}')
            # return idf
            return comp.Identifier(self, idf)

    def get_a_string(self, string:str, skip_white = True, tail_white = False):
        self.dbg(f'get_a_string {string}')
        save_1 = self.save()

        if skip_white:
            self.skip_white()

        for c in string:
            self.source_file_index += 1
            if self.source_file_index >= self.source_file_buffer_len:
                self.load(save_1)
                self.dbg(f'get_a_string {string} return False')
                return False

            if c != self.source_file_buffer[self.source_file_index]:
                self.load(save_1)
                self.dbg(f'get_a_string {string} return False')
                return False

        if tail_white:
            c = self.getc()
            if c.isspace():
                return True
            else:
                return False

        self.dbg(f'get_a_string {string} return True')
        return True

    def get_digit(self):
        c = self.getc()
        if c is None:
            return comp.NoObject()

        if c.isdigit():
            return c

        self.source_file_index -= 1
        return comp.NoObject()

    def get_nondigit(self):
        c = self.getc()
        if c is None:
            return None

        if c == '_' or c.isalpha():
            self.dbg(f'get_nondigit return {c}')
            return c

        if c == '\n':
            self.current_lineno -= 1

        self.source_file_index -= 1
        return None

    def simple_self_test(self):
        idf = comp.Identifier(self, 'wtf')
        assert 'wtf' == idf
        assert idf in ['666', 'wtf']

    def gen_asm(self, name, tu):
        self.dbg_yellow(f'gen_asm')
        try:
            self.asm_head.write(f'; {name}.asm\n; {datetime.datetime.now()}\n\n')
            # self.asm_head.write(f'include cranks_libc.asm\n')
            self.asm_data.write(f'    .data\n\n')

            helper_var = f'right_32f qword 0ffffffffh ; ffffffffh not work \n'
            self.asm_data.write(helper_var)

            tu.gen_asm()

            with open(f'./{name}.asm', 'w', encoding = 'utf8') as f:
                f.write(self.asm_head.getvalue() + self.asm_data.getvalue() + self.asm_code.getvalue())

            return True
        #except CompilerError as e:
        #    raise e
        except CodeError as e:
            raise e
        except:
            traceback.print_exc()

        return False

    def remove_comments(self, name):
        # remove simple comments
        # ugly
        # one pass, delete comments.
        # keep lines
        # output to /output/{name}_no_comment.c

        source_file_buffer_new = io.StringIO()

        index = 0

        # todo: complex comments
        # in_comment = False
        # in_string = False

        while True:
            if index >= self.source_file_buffer_len:
                break

            c = self.source_file_buffer[index]

            # if not in_comment:
            if c == '/':
                if (index + 1) >= self.source_file_buffer_len:
                    source_file_buffer_new.write(f'/')
                    break

                index += 1
                cc = self.source_file_buffer[index]
                if cc == '/':
                    # // comment
                    # delete to new line
                    # replace with ' '
                    index += 1
                    done = False
                    while True:
                        if index >= self.source_file_buffer_len:
                            done = True
                            break

                        c = self.source_file_buffer[index]
                        if c == '\n':
                            source_file_buffer_new.write(f'\n')
                            index += 1
                            break

                        # source_file_buffer_new.write(f' ')
                        index += 1

                    if done:
                        break

                    continue
                elif cc == '*':
                    # /* comment
                    index += 1
                    # close_comment = False
                    while True:
                        if index >= self.source_file_buffer_len:
                            raise CodeError("unterminated comment")
                            # done = True
                            # break

                        c = self.source_file_buffer[index]
                        if c == '*':
                            index += 1
                            if index >= self.source_file_buffer_len:
                                raise CodeError("unterminated comment")

                            cc = self.source_file_buffer[index]
                            if cc == '/': # */ close comment
                                index += 1
                                # close_comment = True
                                break
                            else:
                                index += 1
                                if cc == '\n':
                                    source_file_buffer_new.write(f'\n')
                                continue
                        elif c == '\n':
                            source_file_buffer_new.write(f'\n')
                        else:
                            pass

                        index += 1

                    # if close_comment:
                    #    continue

                    continue
                else:
                    source_file_buffer_new.write(f'{c}{cc}')
                    index += 1
                    continue
            else:
                source_file_buffer_new.write(f'{c}')
                index += 1
                continue

        with open(f'./{name}_no_comment.c', 'w', encoding = 'utf8') as f:
            f.write(source_file_buffer_new.getvalue())

        self.source_file_buffer = source_file_buffer_new.getvalue()
        self.source_file_buffer_len = len(self.source_file_buffer)


    def compile(self, source_file_name):
        try:
            self.init()

            self.dbg_ok(f'compile {source_file_name}')
            file_name = os.path.basename(source_file_name)
            self.dbg_ok(f'file_name = {file_name}')
            name = os.path.splitext(file_name)[0]
            self.dbg_ok(f'name = {name}')

            with open(f'../test_case/{source_file_name}', 'r', encoding = 'utf8') as f:
                self.source_file_buffer = f.read()
                self.source_file_buffer_len = len(self.source_file_buffer)

            self.remove_comments(name)

            self.print_depth = True
            tu = self.get_translation_unit()
            self.print_depth = False

            tu.print_me()

            result = self.gen_asm(name, tu)
            if result:
                result = self.build(name)
                if result:
                    result, output = self.run(name + '.exe')
                    if result:
                        return True, output

        except CompilerError as e:
            self.dbg_fail(e)
        except CodeError as e:
            traceback.print_exc()
            self.dbg_fail(e)

        return False, None

    def build(self, name):
        # now in output folder

        # self.dbg(f'sys.getfilesystemencoding() = {sys.getfilesystemencoding()}')
        # self.dbg(f'locale.getencoding() = {locale.getencoding()}')
        # self.dbg(f'locale.getlocale() = {locale.getlocale()}')

        lib_path = self.win_sdk_lib_path # f'C:/Program Files (x86)/Windows Kits/10/Lib/10.0.22621.0/um/x64/'
        lib_string = f'"{lib_path}kernel32.lib" "{lib_path}user32.lib"'
        # lib_string = ''
        libc_name = 'cranks_libc'

        # "c:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.37.32822\bin\Hostx64\x64\ml64.exe" ./test.asm /link /subsystem:console /entry:main
        # cmd_1 = '"c:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.37.32822\bin\Hostx64\x64\ml64.exe" ./test.asm /link /subsystem:console /entry:main'
        ml64_exe = self.ml64_path # '"c:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.37.32822/bin/Hostx64/x64/ml64.exe"'

        cmd_1 = f'{ml64_exe} /c ../compiler/{libc_name}.asm'

        cmd_2 = f'{ml64_exe} ./{name}.asm ./{libc_name}.obj {lib_string} /link /subsystem:console /entry:main '

        # default /stack:1048576,4096
        # https://learn.microsoft.com/en-us/cpp/build/reference/stacksize?view=msvc-170
        # without calling __chkstk, large stack array will cause memory violation
        # https://learn.microsoft.com/en-us/windows/win32/devnotes/-win32-__chkstk?source=recommendations
        # https://stackoverflow.com/questions/4123609/allocating-a-buffer-of-more-a-page-size-on-stack-will-corrupt-memory
        # https://www.metricpanda.com/rival-fortress-update-45-dealing-with-__chkstk-__chkstk_ms-when-cross-compiling-for-windows/
        # not using __chkstk for simplicity
        cmd_2 += '/stack:1048576,1048576'

        # todo: subprocess displays garbage on error with chinese system.

        try:
            self.dbg_yellow(f'run assembler {cmd_1}')
            result = subprocess.run(cmd_1, shell = True, encoding = 'utf-8')  # , encoding = 'utf8'
            # result = subprocess.run(cmd, shell = True, encoding = 'utf8') # , encoding = 'utf8'
            self.dbg_yellow(f'assembler result = {result}')
            if result.returncode == 0:
                self.dbg_ok(f'assembler ok')
            else:
                raise CompilerError(f'assembler failed 1')

            self.dbg_yellow(f'run assembler {cmd_2}')
            # check_output run
            result = subprocess.run(cmd_2, shell = True, encoding = 'utf-8') # , encoding = 'utf8'
            self.dbg_yellow(f'assembler result = {result}')
            if result.returncode == 0:
                self.dbg_ok(f'assembler ok')
            else:
                raise CompilerError(f'assembler failed 2')

            return True

        except subprocess.CalledProcessError as e:
            self.dbg_fail(f'assembler failed. error = {e}')

        return False

    def run(self, name):
        try:
            self.dbg_yellow(f'start run {name}')
            # check_output run
            result = subprocess.run(f'{name}', shell = True, encoding = 'utf-8', stdout = subprocess.PIPE)  # , encoding = 'utf8'
            self.dbg_yellow(f'run {name} result = {result}')
            if result.returncode == 0:
                self.dbg_ok(f'run ok')

                # print(dir(result))
                # print(type(result.stdout))
                print(result.stdout)
                return True, result.stdout
            else:
                self.dbg_fail(f'run failed')

        except subprocess.CalledProcessError as e:
            self.dbg_fail(f'run failed error = {e}')

        return False, None

    def run_tests(self):
        self.dbg_ok(f'os.getcwd() = {os.getcwd()}')
        os.chdir('./output')
        self.dbg_ok(f'os.getcwd() now = {os.getcwd()}')

        with open(f'../test_case/test.json') as test_json:
            test_info = json.load(test_json)
            print(test_info)

            test_start = test_info['test_start']
            test_end = test_info['test_end']

            for i in range(test_start, test_end + 1):
                ok, output = self.compile(f'test_{i}.c')
                if not ok:
                    raise CompilerError(f'test_{i}.c failed')

                output = io.StringIO(output)

                with open(f'../test_case/test_{i}.ans', 'r', encoding = 'utf8') as answer:
                    while True:
                        answer_line = answer.readline()
                        if not answer_line:
                            break

                        output_line = output.readline()
                        if answer_line != output_line:
                            raise CompilerError(f'test_{i}.c wrong answer\noutput_line =\n{output_line}\nanswer_line =\n{answer_line}\n')

            self.dbg_ok(f'run_tests ok')
