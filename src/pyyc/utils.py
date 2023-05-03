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
    "",
    "\t.align  1",
	"\t.globl  {func}",
	"\t.type   {func}, @function",
    "{func}:",
    "\taddi    sp,sp,-{var_space}",
	"\tsd      ra,24(sp)",
	"\tsd      s0,16(sp)",
	"\taddi    s0,sp,{var_space}",
    ""
]

FUNC_END_OF_ASSEMBLY_FILE = [
    "",
    "\tli      a5,0",
	"\tmv      a0,a5",
	"\tld      ra,24(sp)",
	"\tld      s0,16(sp)",
	"\taddi    sp,sp,{var_space}",
	"\tjr      ra",
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
    '\t.file   "hello.c"',
	'\t.option pic',
	'\t.text',

    "",
    "\t.align  1",
	"\t.globl  main",
	"\t.type   main, @function",
    "main:",
    "\taddi    sp,sp,0",
	"\tsd      ra,24(sp)",
	"\tsd      s0,16(sp)",
	"\taddi    s0,sp,0",

	"",
    "\tli      a5,0",
	"\tmv      a0,a5",
	"\tld      ra,24(sp)",
	"\tld      s0,16(sp)",
	"\taddi    sp,sp,0",
	"\tjr      ra",
    ""
]