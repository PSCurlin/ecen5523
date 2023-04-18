def f(_f_x):
	_f_y = create_list(4)
	_f_y = inject_big(_f_y)
	temp0_ = set_subscript(_f_y, 0, 16)
	temp1_ = create_list(2)
	temp1_ = inject_big(temp1_)
	temp3_ = set_subscript(temp1_, 0, y)
	temp4_ = set_subscript(temp1_, 4, x)
	temp2_ = create_closure(lambda_0, temp1_)
	return temp2_
def lambda_0(temp1_, _lambda_1_z):
	tp_check_type_0 = is_int(_x)
	tp_check_type_2 = is_big(_x)
	tp_check_type_1 = is_bool(_x)
	if(tp_check_type_0):
		tp_check_type_3 = is_int(_y)
		tp_check_type_5 = is_bool(_y)
		if(tp_check_type_3):
			tp_proj_0 = project_int(_x)
			tp_proj_1 = project_int(_y)
			tp_proj_0 = tp_proj_0 + tp_proj_1
			temp5_ = inject_int(tp_proj_0)
		if(tp_check_type_5):
			tp_proj_0 = project_int(_x)
			tp_proj_1 = project_bool(_y)
			tp_proj_0 = tp_proj_0 + tp_proj_1
			temp5_ = inject_int(tp_proj_0)
	elif(tp_check_type_1):
		tp_check_type_3 = is_int(_y)
		tp_check_type_5 = is_bool(_y)
		if(tp_check_type_3):
			tp_proj_0 = project_bool(_x)
			tp_proj_1 = project_int(_y)
			tp_proj_0 = tp_proj_0 + tp_proj_1
			temp5_ = inject_int(tp_proj_0)
		if(tp_check_type_5):
			tp_proj_0 = project_bool(_x)
			tp_proj_1 = project_bool(_y)
			tp_proj_0 = tp_proj_0 + tp_proj_1
			temp5_ = inject_int(tp_proj_0)
	elif(tp_check_type_2):
		tp_check_type_4 = is_big(_y)
		if(tp_check_type_4):
			tp_proj_0 = project_big(_x)
			tp_proj_1 = project_big(_y)
			tp_proj_0 = add(tp_proj_0, tp_proj_1)
			temp5_ = inject_big(tp_proj_0)
	tp_check_type_6 = is_int(temp5_)
	tp_check_type_8 = is_big(temp5_)
	tp_check_type_7 = is_bool(temp5_)
	if(tp_check_type_6):
		tp_check_type_9 = is_int(_lambda_1_z)
		tp_check_type_11 = is_bool(_lambda_1_z)
		if(tp_check_type_9):
			tp_proj_2 = project_int(temp5_)
			tp_proj_3 = project_int(_lambda_1_z)
			tp_proj_2 = tp_proj_2 + tp_proj_3
			temp6_ = inject_int(tp_proj_2)
		if(tp_check_type_11):
			tp_proj_2 = project_int(temp5_)
			tp_proj_3 = project_bool(_lambda_1_z)
			tp_proj_2 = tp_proj_2 + tp_proj_3
			temp6_ = inject_int(tp_proj_2)
	elif(tp_check_type_7):
		tp_check_type_9 = is_int(_lambda_1_z)
		tp_check_type_11 = is_bool(_lambda_1_z)
		if(tp_check_type_9):
			tp_proj_2 = project_bool(temp5_)
			tp_proj_3 = project_int(_lambda_1_z)
			tp_proj_2 = tp_proj_2 + tp_proj_3
			temp6_ = inject_int(tp_proj_2)
		if(tp_check_type_11):
			tp_proj_2 = project_bool(temp5_)
			tp_proj_3 = project_bool(_lambda_1_z)
			tp_proj_2 = tp_proj_2 + tp_proj_3
			temp6_ = inject_int(tp_proj_2)
	elif(tp_check_type_8):
		tp_check_type_10 = is_big(_lambda_1_z)
		if(tp_check_type_10):
			tp_proj_2 = project_big(temp5_)
			tp_proj_3 = project_big(_lambda_1_z)
			tp_proj_2 = add(tp_proj_2, tp_proj_3)
			temp6_ = inject_big(tp_proj_2)
	return temp6_
temp7_ = create_list(0)
temp7_ = inject_big(temp7_)
temp8_ = create_closure(f, temp7_)
temp9_ = inject_big(temp8_)
inject_0 = 4
temp11_ = get_free_vars(temp9_)
temp10_ = get_fun_ptr(temp9_)
_f1 = function_return(temp10_, temp11_, inject_0)
inject_1 = 12
temp15_ = _f1
temp14_ = get_free_vars(temp15_)
temp13_ = get_fun_ptr(temp15_)
temp12_ = function_return(temp13_, temp14_, inject_1)
temp16_ = temp12_
print(temp16_)