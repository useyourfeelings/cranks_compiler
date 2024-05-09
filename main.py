import argparse
import traceback
import compiler.compiler as compiler

if __name__ == '__main__':
    try:
        default_ml64_path = '"c:/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/14.37.32822/bin/Hostx64/x64/ml64.exe"'
        default_win_sdk_lib_path = 'C:/Program Files (x86)/Windows Kits/10/Lib/10.0.22621.0/um/x64/'

        parser = argparse.ArgumentParser()
        parser.add_argument('source_file_name', help = 'default = test.c', nargs = '?', default = 'test.c')
        parser.add_argument('--ml64_path', help = f'where is ml64.exe?\ndefault = {default_ml64_path} need quotes', default = default_ml64_path)
        parser.add_argument('--win_sdk_lib_path', help = f'where are windows sdk libs such as kernel32.lib?\ndefault = {default_win_sdk_lib_path}', default = default_win_sdk_lib_path)

        args = parser.parse_args()
        print(args)

        c = compiler.Compiler(args.ml64_path, args.win_sdk_lib_path)
        c.simple_self_test()
        c.compile(args.source_file_name)
    except:
        traceback.print_exc()
