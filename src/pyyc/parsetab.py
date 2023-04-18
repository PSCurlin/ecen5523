
# parsetab.py
# This file is automatically generated. Do not edit.
# pylint: disable=W,C,R
_tabversion = '3.10'

_lr_method = 'LALR'

_lr_signature = 'nonassocPRINTleftPLUSCOMMENT EQUALS EVAL ID INPUT INT LPAR MINUS PLUS PRINT RPARstart : statementsstatements : statement statementstatement : statementsstatement : expressionstatement : PRINT LPAR expression RPARstatement : ID EQUALS expressionexpression : IDexpression : expression PLUS expressionstatement :expression : LPAR expression RPARexpression : INTexpression : MINUS expressionexpression : EVAL LPAR INPUT LPAR RPAR RPAR'
    
_lr_action_items = {'PRINT':([0,2,3,4,7,8,11,12,16,18,20,22,23,25,28,],[5,-3,5,-4,-7,-11,5,-3,-7,-12,-8,-10,-6,-5,-13,]),'ID':([0,2,3,4,6,7,8,9,11,12,13,14,16,17,18,20,22,23,25,28,],[7,-3,7,-4,16,-7,-11,16,7,-3,16,16,-7,16,-12,-8,-10,-6,-5,-13,]),'$end':([0,1,2,3,4,7,8,11,12,16,18,20,22,23,25,28,],[-9,0,-1,-9,-4,-7,-11,-2,-3,-7,-12,-8,-10,-6,-5,-13,]),'LPAR':([0,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,20,22,23,24,25,28,],[6,-3,6,-4,14,6,-7,-11,6,19,6,-3,6,6,-7,6,-12,-8,-10,-6,26,-5,-13,]),'INT':([0,2,3,4,6,7,8,9,11,12,13,14,16,17,18,20,22,23,25,28,],[8,-3,8,-4,8,-7,-11,8,8,-3,8,8,-7,8,-12,-8,-10,-6,-5,-13,]),'MINUS':([0,2,3,4,6,7,8,9,11,12,13,14,16,17,18,20,22,23,25,28,],[9,-3,9,-4,9,-7,-11,9,9,-3,9,9,-7,9,-12,-8,-10,-6,-5,-13,]),'EVAL':([0,2,3,4,6,7,8,9,11,12,13,14,16,17,18,20,22,23,25,28,],[10,-3,10,-4,10,-7,-11,10,10,-3,10,10,-7,10,-12,-8,-10,-6,-5,-13,]),'PLUS':([4,7,8,15,16,18,20,21,22,23,28,],[13,-7,-11,13,-7,13,-8,13,-10,13,-13,]),'EQUALS':([7,],[17,]),'RPAR':([8,15,16,18,20,21,22,26,27,28,],[-11,22,-7,-12,-8,25,-10,27,28,-13,]),'INPUT':([19,],[24,]),}

_lr_action = {}
for _k, _v in _lr_action_items.items():
   for _x,_y in zip(_v[0],_v[1]):
      if not _x in _lr_action:  _lr_action[_x] = {}
      _lr_action[_x][_k] = _y
del _lr_action_items

_lr_goto_items = {'start':([0,],[1,]),'statements':([0,3,11,],[2,12,12,]),'statement':([0,3,11,],[3,11,11,]),'expression':([0,3,6,9,11,13,14,17,],[4,4,15,18,4,20,21,23,]),}

_lr_goto = {}
for _k, _v in _lr_goto_items.items():
   for _x, _y in zip(_v[0], _v[1]):
       if not _x in _lr_goto: _lr_goto[_x] = {}
       _lr_goto[_x][_k] = _y
del _lr_goto_items
_lr_productions = [
  ("S' -> start","S'",1,None,None,None),
  ('start -> statements','start',1,'p_start','parser.py',66),
  ('statements -> statement statement','statements',2,'p_statements','parser.py',70),
  ('statement -> statements','statement',1,'p_statement_statements','parser.py',79),
  ('statement -> expression','statement',1,'p_statement_expression','parser.py',83),
  ('statement -> PRINT LPAR expression RPAR','statement',4,'p_print_statement','parser.py',87),
  ('statement -> ID EQUALS expression','statement',3,'p_assign_id','parser.py',91),
  ('expression -> ID','expression',1,'p_id_expression','parser.py',98),
  ('expression -> expression PLUS expression','expression',3,'p_plus_expression','parser.py',102),
  ('statement -> <empty>','statement',0,'p_comments','parser.py',106),
  ('expression -> LPAR expression RPAR','expression',3,'p_nested_expression','parser.py',110),
  ('expression -> INT','expression',1,'p_int_expression','parser.py',114),
  ('expression -> MINUS expression','expression',2,'p_unary_expression','parser.py',118),
  ('expression -> EVAL LPAR INPUT LPAR RPAR RPAR','expression',6,'p_eval_expression','parser.py',123),
]
