PRINT_STR = "{push}\ncall print_any"
EVAL_INPUT = 'call {op}\nmovl a1, {value}'
CREATE_DICT = 'call {op}\nmovl a1, {value}'
ASSIGN_STACK = 'movl {value}, {var}'
NOT_EQUALS_BIG = "{push_y}\n{push_x}\ncall not_equal\nmovl a1, {z}"
EQUALS_BIG = "{push_y}\n{push_x}\ncall equal\nmovl a1, {z}"

FUNCTION_CALL_3_args = "{push_z}\n{push_y}\n{push_x}\ncall {op}\nmovl a1, {z}"
FUNCTION_CALL_2_args = "{push_y}\n{push_x}\ncall {op}\nmovl a1, {z}"
FUNCTION_CALL_1_args = "{push_x}\ncall {op}\nmovl a1, {z}"