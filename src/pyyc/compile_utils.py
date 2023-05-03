PRINT_STR = "{push}\ncall print_any"
EVAL_INPUT = 'call {op}\nadd {value},x0,a0'
CREATE_DICT = 'call {op}\nadd {value},x0, a0'
ASSIGN_STACK = 'sd {var}, -{value}(sp)'
NOT_EQUALS_BIG = "{push_y}\n{push_x}\ncall not_equal\nadd {z},x0,a0"
EQUALS_BIG = "{push_y}\n{push_x}\ncall equal\nadd {z},x0, a0"

FUNCTION_CALL_3_args = "{push_z}\n{push_y}\n{push_x}\ncall {op}\nadd {z},x0, a0"
FUNCTION_CALL_2_args = "{push_y}\n{push_x}\ncall {op}\nadd {z},x0, a0"
FUNCTION_CALL_1_args = "{push_x}\ncall {op}\nadd {z},x0, a0"