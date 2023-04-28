HEADER_ASSEMBLY = [
    '\t.file   "hello.c"',
	'\t.option pic',
	'\t.text'
]



MAIN_STARTER_ASSEMBLY = [
    "",
    "\t.align  1",
	"\t.globl  main",
	"\t.type   main, @function",
    "main:",
    "\taddi    sp,sp,-{var_space}",
	"\tsd      ra,24(sp)",
	"\tsd      s0,16(sp)",
	"\taddi    s0,sp,{var_space}",
    ""]

FUNC_STARTER_ASSEMBLY = [ 
    "{func}:",
    "\tpushl %ebp # save caller’s base pointer", 
    "\tmovl %esp, %ebp # set our base pointer", 
    "\tsubl ${var_space}, %esp # allocate for local vars",
    "\tpushl %ebx # save callee saved registers",
    "\tpushl %esi",
    "\tpushl %edi",
    ""]

FUNC_END_OF_ASSEMBLY_FILE = [
    "",
    # "\tmovl {return_value}, %eax # set return value",
    "\tpopl %edi # restore callee saved registers",
    "\tpopl %esi",
    "\tpopl %ebx",
    "\tmovl %ebp, %esp # restore esp",
    "\tpopl %ebp # restore ebp (alt. “leave”)",
    "\tret # jump execution to call site",
    ""]


MAIN_END_OF_ASSEMBLY_FILE = [
    "",
    "\tli      a5,0",
	"\tmv      a0,a5",
	"\tld      ra,24(sp)",
	"\tld      s0,16(sp)",
	"\taddi    sp,sp,{var_space}",
	"\tjr      ra",
    ""]


EMPTY_FILE = [
    ".globl main",
    "main:",
	"pushl %ebp", # save caller’s base pointer
	"movl %esp, %ebp", # set our base pointer
	"subl $4, %esp", # allocate for local vars
	"pushl %ebx", # save callee saved registers
	"pushl %esi",
	"pushl %edi",

	"popl %edi", # restore callee saved registers
	"popl %esi",
	"popl %ebx",
	"movl $0, %eax", # set return value
	"movl %ebp, %esp", # restore esp
	"popl %ebp", # restore ebp (alt. “leave”)
	"ret", # jump execution to call site
]