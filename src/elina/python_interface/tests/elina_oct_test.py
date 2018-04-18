import sys
sys.path.insert(0, '../../../')

from elina.python_interface.elina_auxiliary_imports import *
from elina.python_interface.opt_oct import *
from elina.python_interface.test_imports import *
from elina.python_interface.elina_scalar import *
from elina.python_interface.elina_lincons0 import *
from elina.python_interface.elina_lincons0_h import *
from elina.python_interface.elina_manager import *
from elina.python_interface.elina_abstract0 import *
from elina.python_interface.elina_linexpr0 import *
from elina.python_interface.elina_linexpr0_h import *
from elina.python_interface.elina_dimension_h import *
import  random

import gc

def generate_random_linexpr0(dim,nbcons,is_lincons):
        if(is_lincons):
        	size = random.randint(0,2)
        else:
                size = random.randint(1,2)        
        linexpr0 = elina_linexpr0_alloc(ElinaLinexprDiscr.ELINA_LINEXPR_SPARSE, size)
        d = random.randint(0, 10)
        cst = pointer(linexpr0.contents.cst) #the constant of the expression
        elina_scalar_set_int(cst.contents.val.scalar, d)
        if(size):
        	v1 = random.randint(0, dim-1)
        	v2 = v1
        	while(v2==v1):
            		v2 = random.randint(0, dim-1)
        	linterm = pointer(linexpr0.contents.p.linterm[0])
        	linterm.contents.dim = ElinaDim(v1)
        	coeff = pointer(linterm.contents.coeff)
        	d = c_double(random.randint(0, 1))
        	if d:
            		elina_scalar_set_double(coeff.contents.val.scalar, 1)
        	else:
            		elina_scalar_set_double(coeff.contents.val.scalar, -1)
        if(size==2):
        	linterm = pointer(linexpr0.contents.p.linterm[1])
        	linterm.contents.dim = ElinaDim(v2)
        	coeff = pointer(linterm.contents.coeff)
        	d = c_double(random.randint(0, 1))
        	if d:
            		elina_scalar_set_double(coeff.contents.val.scalar, 1)
        	else:
            		elina_scalar_set_double(coeff.contents.val.scalar, -1)
        return linexpr0

def generate_linexpr0(size, var, sign, c):
	if size > 2: 
		print ("Size shouldn't be greater than 2")
		return None 
	linexpr0 = elina_linexpr0_alloc(ElinaLinexprDiscr.ELINA_LINEXPR_SPARSE, size)
	cst = pointer(linexpr0.contents.cst)
	#set the constant of the expression to c 
	elina_scalar_set_int(cst.contents.val.scalar, c)
	#let the variables and coefficients (signs) of the linear expression
	for i in range(size):
		linterm = pointer(linexpr0.contents.p.linterm[i])
		linterm.contents.dim = ElinaDim(var[i])
		coeff = pointer(linterm.contents.coeff)
		elina_scalar_set_double(coeff.contents.val.scalar, sign[i])

	return linexpr0





def generate_random_lincons0_array(dim, nbcons):

    lincons0_array = elina_lincons0_array_make(nbcons)
    # elina_lincons0_array_fprint(cstdout, lincons0_array, None)

    for i in range(0, nbcons):
        option = random.randint(0, 1)
        if option:
            lincons0_array.p[i].constyp = c_uint(ElinaConstyp.ELINA_CONS_SUPEQ)
        else:
            lincons0_array.p[i].constyp = c_uint(ElinaConstyp.ELINA_CONS_EQ)
        lincons0_array.p[i].linexpr0 = generate_random_linexpr0(dim,nbcons,False)

    return lincons0_array


def test_meet_lincons(man,dim,nbcons):
	arr = generate_random_lincons0_array(dim,nbcons) #generate random array of linear constraints
	top = elina_abstract0_top(man,dim,0) #create top element
	print("Meet lincons input constraints")
	elina_lincons0_array_print(arr,None) #prints array of linear constraints
	sys.stdout.flush() 
	o1 = elina_abstract0_meet_lincons_array(man,False,top,arr) #o1 = top (intersects) arr
	arr2 = elina_abstract0_to_lincons_array(man,o1) #arr2 = concrete()
	print("OutPut Octagon")
	elina_lincons0_array_print(arr2,None)
	elina_lincons0_array_clear(arr)
	elina_lincons0_array_clear(arr2)
	elina_abstract0_free(man,top)
	elina_abstract0_free(man,o1)

def test_assign(man,dim,nbcons):
	arr = generate_random_lincons0_array(dim,nbcons)
	o1 = elina_abstract0_top(man,dim,0) 
	o1 = elina_abstract0_meet_lincons_array(man,True,o1,arr) 
	print("Assign input octagon")
	arr2 = elina_abstract0_to_lincons_array(man,o1)
	elina_lincons0_array_print(arr2,None)
	elina_lincons0_array_clear(arr)
	elina_lincons0_array_clear(arr2)
	var = random.randint(0,dim-1) #int representing a variable I suppose
	tdim= ElinaDim(var) #casting to c_uint
	linexpr0 = generate_random_linexpr0(dim,nbcons,True) 
	print("Statement x",int(var))
	elina_linexpr0_print(linexpr0,None)
	sys.stdout.flush()
	o2 = elina_abstract0_assign_linexpr_array(man,False,o1,tdim,linexpr0,1,None)
	arr3 = elina_abstract0_to_lincons_array(man,o2)
	print("Assign output Octagon")
	elina_lincons0_array_print(arr3,None)
	elina_lincons0_array_clear(arr3)
	elina_linexpr0_free(linexpr0)
	elina_abstract0_free(man,o1)
	elina_abstract0_free(man,o2)

def test_substitute(man,dim,nbcons):
	arr = generate_random_lincons0_array(dim,nbcons)
	o1 = elina_abstract0_top(man,dim,0)
	o1 = elina_abstract0_meet_lincons_array(man,True,o1,arr)
	print("Substitute input octagon")
	arr2 = elina_abstract0_to_lincons_array(man,o1)
	elina_lincons0_array_print(arr2,None)
	elina_lincons0_array_clear(arr)
	elina_lincons0_array_clear(arr2)
	var = random.randint(0,dim-1)
	tdim= ElinaDim(var)
	linexpr0 = generate_random_linexpr0(dim,nbcons,True)
	print("Statement x",int(var))
	elina_linexpr0_print(linexpr0,None)
	sys.stdout.flush()
	o2 = elina_abstract0_substitute_linexpr_array(man,False,o1,tdim,linexpr0,1,None)
	arr3 = elina_abstract0_to_lincons_array(man,o2)
	print("Substitute output Octagon")
	elina_lincons0_array_print(arr3,None)
	elina_lincons0_array_clear(arr3)
	elina_linexpr0_free(linexpr0)
	elina_abstract0_free(man,o1)
	elina_abstract0_free(man,o2)
	
def test_join(man,dim,nbcons):
	arr1 = generate_random_lincons0_array(dim,nbcons)
	o1 = elina_abstract0_top(man,dim,0)
	o1 = elina_abstract0_meet_lincons_array(man,True,o1,arr1)
	arr2 = generate_random_lincons0_array(dim,nbcons)
	o2 = elina_abstract0_top(man,dim,0)
	o2 = elina_abstract0_meet_lincons_array(man,True,o2,arr2)
	arr3 = elina_abstract0_to_lincons_array(man,o1)
	arr4 = elina_abstract0_to_lincons_array(man,o2)
	print("Join input Octagons")
	elina_lincons0_array_print(arr3,None)
	elina_lincons0_array_print(arr4,None)
	elina_lincons0_array_clear(arr1)
	elina_lincons0_array_clear(arr2)
	elina_lincons0_array_clear(arr3)
	elina_lincons0_array_clear(arr4)
	o3 = elina_abstract0_join(man,False,o1,o2)
	arr5 = elina_abstract0_to_lincons_array(man,o3)
	print("Join output Octagon")
	elina_lincons0_array_print(arr5,None)
	elina_lincons0_array_clear(arr5)
	elina_abstract0_free(man,o1)
	elina_abstract0_free(man,o2)
	elina_abstract0_free(man,o3)



dim = int(sys.argv[1])
nbcons = int(sys.argv[2])
man = opt_oct_manager_alloc()
# test_meet_lincons(man,dim,nbcons)
# test_assign(man,dim,nbcons)
# test_substitute(man,dim,nbcons)
# test_join(man,dim,nbcons)
linexpr = generate_linexpr0(2, [0, 1], [1, -1], 4)
elina_linexpr0_print(linexpr, None)
print()
elina_manager_free(man)
gc.collect()

