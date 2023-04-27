#include<stdio.h>


int sum;

int ret_sum(int a, int b){
	return a+b;
}

void print_sum(){
	printf("%d",sum);
	printf("\n");
}


int main(){
	sum= ret_sum(1,2);
	print_sum();
	printf("h\n");
	return 0;
}
