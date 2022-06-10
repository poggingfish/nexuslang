#!/usr/bin/env python

#Nexuslang > C codegen
#Created by: poggingfish
#First created: 05/15/2022

linenum = 0
import sys # for args
import subprocess # for calling gcc
import os
import colorama
import time
import sys
import random
builtins_location = "/opt/nexus/builtins.nexus"
main_file = sys.argv[1]
quiet = False
line = ""
current_file = ""
main_defed = False
funcs = []
def error(message):
    global line
    global linenum
    print(colorama.Fore.RED + "Error: " + colorama.Fore.RESET + message + " at line " + str(linenum))
    print("error at: " + " ".join(line))
    os.remove(current_file.replace(".nexus", ".c"))
    sys.exit()
def warning(message):
    global line
    global linenum
    print(colorama.Fore.YELLOW + "Warning: " + colorama.Fore.RESET + message + " at line " + str(linenum))
    print("warning at: " + " ".join(line))
def compile(file_name, keep_file=False, debug_info=False):
    global linenum
    global line
    global funcs
    global current_file
    global main_defed
    global quiet
    c_code = False
    numloops_ended = 0
    numloops = 0
    ifs = 0
    with open(file_name, 'r') as f:
        lines = f.readlines()
    out = open(file_name.replace(".nexus", ".c").split("/")[-1], 'w')
    if file_name == main_file:
        compile("/opt/nexus/builtins.nexus", True)
        code_gen_start = time.perf_counter()
        out.write("#include <unistd.h>\n")
        out.write("#include <stdio.h> //Codegen\n")
        out.write("#include <stdlib.h> //Codegen\n")
        out.write("#include <string.h> //Codegen\n")
        out.write("#include <math.h> //Codegen\n")
        out.write("int stack[1024];\n")
        out.write("int stack_ptr = 0;\n")
        out.write("// START OF BUILTINS\n")
        out.write(open("builtins.c", 'r').read())
        os.remove("builtins.c")
        out.write("// END OF BUILTINS\n")
    else:
        code_gen_start = time.perf_counter()
    current_file = file_name
    for line in lines:
        if file_name == main_file:
            linenum += 1
        if c_code:
            if line.strip() == "end_c_code":
                c_code = False
                continue
            out.write(line.replace("\n", ""))
            if line.startswith("//"):
                out.write("\n")
            else:
                out.write(" // C Code\n")
            continue
        line = line.replace("\n", "")
        line = line.replace("  ", " ")
        line = line.split(" ")
        if line[0] in funcs:
            out.write(line[0] + "(" + ",".join(line[1:]) + "); // Call\n")
        elif line[0] in (x.replace("__","") for x in funcs):
            out.write("__"+line[0] + "__(" + ",".join(line[1:]) + "); // Call\n")
        if line[0] == "func":
            if len(line) < 2:
                error("func takes exactly 1 argument")
            if debug_info:
                print("Function: " + line[2])
            if line[2] == "main":
                main_defed = True
            funcs.append(line[2])
            if line[1] == "int":
                out.write("int ")
            elif line[1] == "char_array":
                out.write("char* ")
            elif line[1] == "char":
                out.write("char ")
            if len(line) >= 3:
                out.write(line[2] + "(" + " ".join(line[3:]) + ") { //func\n")
            else:
                out.write(line[2] + "() { //func\n")
        if line[0] == "end":
            out.write("} //end\n")
            if ifs > 0:
                ifs -= 1
        if line[0] == "set":
            if line[1] == "int":
                if len(line) < 3:
                    error("set int takes at least 2 arguments")
                elif len(line) == 4:
                    out.write("int " + line[2] + " = " + line[3] + "; //set\n")
                    if debug_info:
                        print("Set int: " + line[2] + " = " + line[3])
                else:
                    out.write("int " + line[2] + "; //set\n")
                    if debug_info:
                        print("Set int: " + line[2])
            elif line[1] == "char_array":
                if len(line) < 3:
                    error("set char_array takes at least 2 arguments")
                elif len(line) == 4:
                    out.write("char " + line[2] + "[" + line[3] + "]; //set\n")
                    if debug_info:
                        print("Set char_array: " + line[2] + " = " + line[3])
                else:
                    out.write("char " + line[2] + "[]; //set\n")
                    if debug_info:
                        print("Set char_array: " + line[2])
            elif line[1] == "char":
                if len(line) < 3:
                    error("set char takes at least 2 arguments")
                elif len(line) == 4:
                    out.write("char " + line[2] + " = " + line[3] + "; //set\n")
                    if debug_info:
                        print("Set char: " + line[2] + " = " + line[3])
                else:
                    out.write("char " + line[2] + "; //set\n")
                    if debug_info:
                        print("Set char: " + line[2])
            else:
                if len(line) < 2:
                    error("set takes at least 2 arguments")
                if len(line) == 2:
                    out.write(line[1] + " " + line[2] + " = " + line[3] + "; //set\n")
                    if debug_info:
                        print("Reassigned: " + line[1] + " = " + line[3])
                else:
                    out.write(line[1] + " = " + line[2] + "; //set\n")
                    if debug_info:
                        print("Set: " + line[1] + " = " + line[2])
        if line[0] == "print":
            if len(line) != 3:
                error("print takes exactly 2 arguments")
            if line[1] == "int":
                out.write("printf(\"%d\\n\", " + line[2] + "); //print \n")
                if debug_info:
                    print("Print int: " + line[2])
            elif line[1] == "char_array":
                out.write("printf(" + line[2] + "); //print \n")
                if debug_info:
                    print("Print char_array: " + line[2])
            else:
                error("Type not specified")
        if line[0] == "add":
            if line[1] == "int":
                out.write(line[2] + " = " + line[2] + " + " + line[3] + "; //add\n")
                if debug_info:
                    print("Add int: " + line[2] + " + " + line[3])
            else:
                error("Type not specified")
        if line[0] == "sub":
            if line[1] == "int":
                out.write(line[2] + " = " + line[2] + " - " + line[3] + "; //sub\n")
                if debug_info:
                    print("Sub int: " + line[2] + " - " + line[3])
            else:
                error("Type not specified")
        if line[0] == "mul":
            if line[1] == "int":
                out.write(line[2] + " = " + line[2] + " * " + line[3] + "; //mul\n")
                if debug_info:
                    print("Mul int: " + line[2] + " * " + line[3])
            else:
                error("Type not specified")
        if line[0] == "div":
            if line[1] == "int":
                out.write(line[2] + " = " + line[2] + " / " + line[3] + "; //div\n")
                if debug_info:
                    print("Div int: " + line[2] + " / " + line[3])
            else:
                error("Type not specified")
        if line[0] == "fori":
            if len(line) < 3:
                error("fori takes at least 2 arguments")
            #Iterate for the amount of times in the 1st argument
            out.write(f"for(int {line[2]} = 0; {line[2]} < {line[1]}; {line[2]}++){{\n")
            if debug_info:
                print("Fori: " + line[2] + " < " + line[1])
        if line[0] == "call":
            if len(line) < 2:
                error("call takes 1 or more arguments")
            if line[1] == "set":
                if line[3] not in funcs:
                    error("Function " + line[3] + " not found")
                out.write(line[2] + " = " + line[3] + "("+ " ".join(line[4:]) + ")" +"; //call\n")
            else:
                if line[1] not in funcs:
                    error("Function " + line[1] + " not found")
                out.write(line[1] + "("+ " ".join(line[2:]) + "); //call\n")
            if debug_info:
                print("Call: " + line[1] + "(" + " ".join(line[2:]) + ")")
        if line[0] == "return":
            if len(line) != 2:
                error("return takes exactly 1 argument")
            out.write("return " + line[1] + "; //return\n")
            if debug_info:
                print("Return: " + line[1])
        if line[0] == "if":
            if len(line) < 3:
                error("if takes at least 2 arguments")
            if line[1] == "eq":
                out.write("if(" + line[2] + " == " + line[3] + ") {\n")
                if debug_info:
                    print("If eq: " + line[2] + " == " + line[3])
            elif line[1] == "ne":
                out.write("if(" + line[2] + " != " + line[3] + ") {\n")
                if debug_info:
                    print("If ne: " + line[2] + " != " + line[3])
            elif line[1] == "lt":
                out.write("if(" + line[2] + " < " + line[3] + ") {\n")
                if debug_info:
                    print("If lt: " + line[2] + " < " + line[3])
            elif line[1] == "le":
                out.write("if(" + line[2] + " <= " + line[3] + ") {\n")
                if debug_info:
                    print("If le: " + line[2] + " <= " + line[3])
            elif line[1] == "gt":
                out.write("if(" + line[2] + " > " + line[3] + ") {\n")
                if debug_info:
                    print("If gt: " + line[2] + " > " + line[3])
            elif line[1] == "ge":
                out.write("if(" + line[2] + " >= " + line[3] + ") {\n")
                if debug_info:
                    print("If ge: " + line[2] + " >= " + line[3])
            ifs += 1
        if line[0] == "c_code":
            c_code = True
        if line[0] == "loop_until_break":
            out.write("while (1) {\n")
            if debug_info:
                print("Loop until break")
            numloops_ended += 1
            numloops +1
        if line[0] == "break":
            if numloops_ended < 0:
                error("Break outside of loop")
            if numloops_ended == 0 and ifs == 0:
                warning("Possibly useless break")
            out.write("break;\n")
            if debug_info:
                print("Break")
            numloops_ended -= 1
        if line[0] == "sleep":
            if len(line) != 2:
                error("sleep takes exactly 1 argument")
            #Convert us to ms
            out.write("usleep(" + line[1] + " * 1000);\n")
        if line[0] == "push":
            if len(line) != 2:
                error("push takes exactly 1 argument")
            out.write("stack[stack_ptr++] = " + line[1] + "; //push \n")
        if line[0] == "pop":
            if len(line) != 2:
                error("pop takes exactly 1 argument")
            out.write(line[1] + " = stack[--stack_ptr]; //pop \n")
    if numloops_ended > 0 and ifs == 0:
        error("Possible infinite loop")
    code_gen_end = time.perf_counter()
    code_gen = code_gen_end - code_gen_start
    # Covert to us
    if not quiet:
        print("Code generation time: " + str(round(code_gen * 1000000,3)) + "μs")
    if file_name == main_file:
        if main_defed == False:
            out.write("int main() {\n")
            out.write("\treturn 0;\n")
            out.write("}\n")
        out.close()
        subprocess.call(["gcc", file_name.replace(".nexus", ".c"), "-o",  file_name.replace(".nexus", "")])
        if not keep_file:
            os.remove(file_name.replace(".nexus", ".c"))
if os.path.isfile("builtins.nexus"):
    with open("builtins.nexus") as f:
        builtins = f.read()
    with open(builtins_location, "w") as f:
        f.write(builtins)
else:
    if not os.path.isfile(builtins_location):
        error("Builtins file not found")
if sys.argv[1] == "--install":
    #Check if user is root
    if os.geteuid() != 0:
        print("You must be root to install")
        sys.exit(1)
    print("Installing nexus to /usr/bin/nexus")
    os.system("cp ./nexus.py /usr/bin/nexus")
    os.chmod("/usr/bin/nexus", 0o755)
    print("Done!")
    sys.exit(0)
try:
    sys.argv[2]
    if sys.argv[2] == "--quiet":
        quiet = True
except IndexError:
    pass
compile_time_start = time.perf_counter()
compile(sys.argv[1], True, False)
compile_time_end = time.perf_counter()
compile_time = compile_time_end - compile_time_start
if not quiet:
    print("Compile time: " + str(round(compile_time*1000,1)) + "ms")