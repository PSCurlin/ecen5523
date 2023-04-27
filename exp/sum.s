	.file	"sum.c"
	.option pic
	.text
	.globl	sum
	.bss
	.align	2
	.type	sum, @object
	.size	sum, 4
sum:
	.zero	4
	.text
	.align	1
	.globl	ret_sum
	.type	ret_sum, @function
ret_sum:
	addi	sp,sp,-32
	sd	s0,24(sp)
	addi	s0,sp,32
	mv	a5,a0
	mv	a4,a1
	sw	a5,-20(s0)
	mv	a5,a4
	sw	a5,-24(s0)
	lw	a5,-20(s0)
	mv	a4,a5
	lw	a5,-24(s0)
	addw	a5,a4,a5
	sext.w	a5,a5
	mv	a0,a5
	ld	s0,24(sp)
	addi	sp,sp,32
	jr	ra
	.size	ret_sum, .-ret_sum
	.section	.rodata
	.align	3
.LC0:
	.string	"%d"
	.text
	.align	1
	.globl	print_sum
	.type	print_sum, @function
print_sum:
	addi	sp,sp,-16
	sd	ra,8(sp)
	sd	s0,0(sp)
	addi	s0,sp,16
	lla	a5,sum
	lw	a5,0(a5)
	mv	a1,a5
	lla	a0,.LC0
	call	printf@plt
	li	a0,10
	call	putchar@plt
	nop
	ld	ra,8(sp)
	ld	s0,0(sp)
	addi	sp,sp,16
	jr	ra
	.size	print_sum, .-print_sum
	.section	.rodata
	.align	3
.LC1:
	.string	"h"
	.text
	.align	1
	.globl	main
	.type	main, @function
main:
	addi	sp,sp,-16
	sd	ra,8(sp)
	sd	s0,0(sp)
	addi	s0,sp,16
	li	a1,2
	li	a0,1
	call	ret_sum
	mv	a5,a0
	mv	a4,a5
	lla	a5,sum
	sw	a4,0(a5)
	call	print_sum
	lla	a0,.LC1
	call	puts@plt
	li	a5,0
	mv	a0,a5
	ld	ra,8(sp)
	ld	s0,0(sp)
	addi	sp,sp,16
	jr	ra
	.size	main, .-main
	.ident	"GCC: (Ubuntu 11.3.0-1ubuntu1~22.04) 11.3.0"
	.section	.note.GNU-stack,"",@progbits
