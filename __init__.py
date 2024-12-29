#!/bin/python

#for language parsing
from .goblang.read_lang import LanguageMap
from .goblang.read_lang import GrammerNode
from .goblang.read_lang import hide_parenthasis
from .errors import ParseError
from DAKMatrix import Matrix

#for typing
from samgob.iterators.control_flow_iterator import ControlFlowIterator

#for random number generation
import random

import os

def get_prelude_path()->str:
    """
    returns the path that the prelude file is located at for python compilation
    """
    return os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            "prelude.py.txt")

class DiceSetParser:
    """
    representation of a dice parser object that parses out the dice language
    """

    """
    the sorting algorithm used by the dice parser,
    we use the built in python one cuz were laaaaaayZ
    """
    def sort_set(self,s : [float],*args) -> [float]:
        #even though we use in place sort, still return
        #for future iterations
        s.sort(*args)
        return s
    
    """
    turn constants into lists for the set functions to be happy
    """
    def setify(self,n)-> [float]:
        if type(n) is float or type(n) is int: return [i for i in range(1,int(n)+1)]
        if type(n) is list: return n

    def __init__(self,**kwargs):
        #if we are theoretical we only want the operator functions on the object,
        #since we are using this object purly for operator parsing
        if not kwargs["only_operations"] if "only_operations" in kwargs else True:

            #language file that contains the specs for the samgob language
            language_file = kwargs["language_file"] if "language_file" in kwargs else os.path.join(
                                                                                        os.path.dirname(
                                                                                            os.path.abspath(__file__)
                                                                                            ),
                                                                                        "dice_set.lang")
            
            #determines if we are going to print matricies using samgbos formating or
            #with numpy formating
            self.numpy_matrix_formating = kwargs["numpy_matrix_formating"] if "numpy_matrix_formating" in kwargs else False

            #generate the langauge structure
            lang,lexims,maps = LanguageMap.from_file(language_file,
                                                     entry_point = "statement")
            self.lang = lang
            self.lexims = lexims
            self.maps = maps

            self.print_delimiter = ' '

            self.variable_map = {}

            self.do_compile = False
            self.tab_order = 0

        #used when adding two numbers together
        self.arithmatic_operators = {
                "+": lambda x,y : x+y,
                "-": lambda x,y : x-y,
                "/": lambda x,y : x/y,
                "*": lambda x,y : x*y,
                ">=": lambda x,y : int(x>=y),
                "<=": lambda x,y : int(x<=y),
                ">": lambda x,y : int(x>y),
                "<": lambda x,y : int(x<y),
                "==": lambda x,y : int(x==y),
                }
        
        #used to compress sets down into a single number but take in a number as an option
        self.set_compressors = {
                'd': lambda n,s: sum([random.choice(self.setify(s)) for _ in range(int(n))])
                }
        
        #used to compress sets down to a single number
        self.unary_set_compressors = {
                's': lambda s: sum(self.setify(s))
                }
        
        #take in two sets and output a new set
        self.set_operators = {
                'D' : lambda n,s: [random.choice(self.setify(s)) for _ in range(int(n))],
                'T' : lambda n,s : self.sort_set(self.setify(s))[-int(n):],
                'B' : lambda n,s : self.sort_set(self.setify(s))[:int(n)]
                }
        
        #iterator that gives us the next statement to parse
        self.statement_stream : ControlFlowIterator = None

        #the buffer that we place output into
        self.out_buffer = ""

    def stream_out(self,*args,**kwargs)->None:
        """
        sends data to the output buffer used to get our dynamic end line working
        """
        data = ""
        if len(args) >0: data = args[0]
        self.out_buffer += str(data) + kwargs["end"] if "end" in kwargs else "\n"

    def parse_assignment(self,token : GrammerNode,parenth)->None:
        """
        parses assinging a value to a variable
        """
        var_name = token.sub_tokens[0].data
        if token.sub_tokens[2].token.name == "arithmatic":
            
            if self.do_compile:
                self.variable_map[var_name] = 1
                self.stream_out("\t"*self.tab_order+f"{var_name}=",end="")
                self.parse_arithmatic(token.sub_tokens[2],parenth)
            else:
                self.variable_map[var_name] = self.parse_arithmatic(token.sub_tokens[2],parenth)

        else:
            self.variable_map[var_name] = self.parse_set(token.sub_tokens[2],parenth)

    def parse_print_flow(self,token : GrammerNode,parenth = [])->None:
        """
        handles parsing the delimter changes in the language (the -100S+ syntax)
        """

        if not (token.sub_tokens[0].sub_tokens[0].token.name == "flow_end" 
               or
               self.statement_stream.while_flag):
            if len(token.sub_tokens) == 2:
                if self.do_compile:
                    self.stream_out("\t"*self.tab_order + "context.delimiters.append('\\n')")
                else:
                    self.print_delimiter = "\n"
            elif len(token.sub_tokens) == 1:
                if self.do_compile:
                    self.stream_out("\t"*self.tab_order + "context.delimiters.append(' ')")
                else:
                    self.print_delimiter = " "
            else:
                if self.do_compile:
                    self.stream_out("\t"*self.tab_order + "context.delimiters.append('",end="")
                    self.stream_out(token.sub_tokens[2].data,end="")
                    self.stream_out("')")
                else:
                    self.print_delimiter = token.sub_tokens[2].data
        

        self.parse_control_flow(token.sub_tokens[0])


    def parse_control_flow(self,token : GrammerNode,parenth = [])->None:
        """
        handles parsing of control flow operations
        """
        flow_token = token.sub_tokens[0]
        flow_type = flow_token.token.name
        match flow_type:
            case "for":
                if self.do_compile:
                    self.stream_out("\t" + "for i in range(",end="")
                    self.parse_arithmatic(flow_token.sub_tokens[1],parenth)
                    self.stream_out("):",end="")
                    self.tab_order += 1
                else:
                    n = self.parse_arithmatic(flow_token.sub_tokens[1],parenth)
                    
                    if n == 0:
                        self.statement_stream.add_if(False,self.print_delimiter)
                    elif n == 1:
                        self.statement_stream.add_if(True,self.print_delimiter)
                    else:
                        self.statement_stream.add_for(int(n),self.print_delimiter)
            case "flow_end":
                if self.do_compile:
                    self.tab_order -= 1
                    self.stream_out("\t"*self.tab_order + "clean_delimiters()")
                else:
                    self.statement_stream.pop_loop()
            case "else":
                if self.do_compile:
                    self.stream_out( "\t"*self.tab_order + "break")
                    self.stream_out("\t"*(self.tab_order-1) + "else:")
                else:
                    self.statement_stream.set_else(True,self.print_delimiter)
            case "while":
                if self.do_compile:
                    self.stream_out( "\t"*self.tab_order + "while ",end="")
                    self.tab_order += 1
                    self.parse_arithmatic(flow_token.sub_tokens[2],parenth)
                    self.stream_out(">0:",end="")
                else:
                    n = self.parse_arithmatic(flow_token.sub_tokens[2],parenth)
                    self.statement_stream.add_while(n>0,flow_token.data,self.print_delimiter)

    def parse_statement(self,statement : GrammerNode,parenth = []):
        """
        this is the entry point for parsing a single grammer node statement of the sam gob
        language

        since this is a fully fledged programming language the parsing can get a little hary (and my coding style :)),
        a good reference to help follow along with what these functions are doing is the dice_set.lang file that contains the
        spec of the language that is used to parse out tokens

        typically, each token will get a function dedicated to parsing out its grammer node, and these functions will be named

        parse_<tokenname>

        then the arragment of sub tokens on that particular grammer node determines the course of action for the langauage
        interpreter to take

        again, see dice_set.lang for the langauge specs on how the tokens are set up, it is VERY helpful for following along with
        the logic here
        """
        expr = statement.sub_tokens[0]
        expression_token = expr.sub_tokens[0]
        
        #control flow clauses
        if self.statement_stream.in_if(False) or self.statement_stream.in_else(True):
            if expression_token.token.name == "print_control_flow":
                expression_token = expression_token.sub_tokens[0]
                if expression_token.sub_tokens[0].token.name == "flow_end":
                    self.statement_stream.break_loop()
                elif expression_token.sub_tokens[0].token.name == "else":
                    self.statement_stream.set_else(False,self.print_delimiter)
                else:
                    """
                    we still care about control flow for the ordering of --
                    but we don't want to parse loops, so a neet hack is to add
                    a true if statement that does nothing, but gets poped when it finds
                    the flow end
                    """
                    self.statement_stream.add_if(True,self.print_delimiter) 
        else:
            match expression_token.token.name:
                case "arithmatic":
                    if self.do_compile:
                        self.stream_out("\t"*self.tab_order + 'print(')
                        n = self.parse_arithmatic(expression_token,parenth)
                        self.stream_out('\n,end=get_delimiter())')
                    else:
                        n = self.parse_arithmatic(expression_token,parenth)
                        
                        if isinstance(n, Matrix):
                            self.stream_out(
                                            str(n) if self.numpy_matrix_formating else n.samgob_string(),
                                            end=self.print_delimiter)
                        else:
                            self.stream_out("%g" % n, end=self.print_delimiter)

                case "set":
                    if self.do_compile:
                        self.stream_out("\t"*self.tab_order + "print(")
                        s = self.parse_set(expression_token,parenth),
                        self.stream_out("\n,end=get_delimiter())")
                        self.stream_out()
                    else:
                        s = self.parse_set(expression_token,parenth)
                        self.stream_out(s,end=self.print_delimiter)
                case "assignment":
                    self.parse_assignment(expression_token,parenth)
                case "print_control_flow":
                    self.parse_print_flow(expression_token,parenth)
            
            if self.do_compile:
                self.stream_out()

    def parse_matrix_row(self,matrix_row : GrammerNode,parenth = [])->[float]:
        ret_val = []
        walker = matrix_row
        
        ret_val.append(self.parse_arithmatic(walker.sub_tokens[0],parenth))

        #see the language specs (dice_set.lang) for how were walking through this
        #basically matricies will allways have an arithmatic node as their second node,
        #but with a matrix row that row might be another matrix attached to the current
        #matrix row, we walk along these rows and parse out the values, until we reach the end
        #of the matrix rows
        while walker.sub_tokens[2].sub_tokens[0].token.name == "matrix":
            walker = walker.sub_tokens[2].sub_tokens[0].sub_tokens[0]
            ret_val.append(self.parse_arithmatic(walker.sub_tokens[0],parenth))

        ret_val.append(self.parse_arithmatic(walker.sub_tokens[2],parenth))
        
        return ret_val
    

    def walk_matrix(self,matrix_node : GrammerNode,matrix = [],parenth = []):
        """
        this function walks along a matrix, and parses out the rows of that matrix
        as float arrays, storing them in the matrix buffer passed to it from above
        """
        #print(matrix_node.token.name)
        #print(matrix_node.data)
        if matrix_node.token.name == "matrix_row": #only a matrix row
            matrix.append(
                self.parse_matrix_row(matrix_node,parenth)
            )
        elif matrix_node.token.name == "matrix":
            if len(matrix_node.sub_tokens) == 3:
                self.walk_matrix(matrix_node.sub_tokens[0],matrix,parenth)
                self.walk_matrix(matrix_node.sub_tokens[2],matrix,parenth)
            elif len(matrix_node.sub_tokens) == 1: #leaf node
                self.walk_matrix(matrix_node.sub_tokens[0],matrix,parenth)

    def parse_matrix(self, matrix_node : GrammerNode,parenth = [])->Matrix:
        """
        wrapper function that holds a buffer for the recursive matrix walk, that 
        way when the walk finishes we can create a matrix class object and pass it out of the system
        without adding extra complexity to the recursion
        """
        matrix_buffer = []
        self.walk_matrix(matrix_node,matrix_buffer,parenth)
        return Matrix(matrix_buffer)
    

    def parse_set(self,set_node : GrammerNode,parenth = []):#->float | [float]:
        inner_token : GrammerNode = set_node.sub_tokens[0]
        if inner_token.token.name == "range":
            if len(inner_token.sub_tokens) == 1:
                number = int(inner_token.sub_tokens[0].data)
                a = [i for i in range(1,number+1)]
                if self.do_compile:
                    self.stream_out(a,end="")
                else:
                    return a
            else:
                a = [i for i in range(int(inner_token.sub_tokens[1].data),int(inner_token.sub_tokens[3].data)+1)]
                if self.do_compile:
                    self.stream_out(a,end="")
                else:
                    return a
        elif inner_token.token.name == 'arithmatic':
            return self.parse_arithmatic(inner_token,parenth)
        elif set_node.sub_tokens[1].token.name == "set_operator":
            if self.do_compile:
                self.stream_out(f"context.set_operators['{set_node.sub_tokens[1].data}'](",end="")
                self.parse_set(set_node.sub_tokens[0],parenth)
                self.stream_out(",",end="")
                self.parse_set(set_node.sub_tokens[2],parenth)
                self.stream_out(")",end="")
            else:
                #ensure that we parse out the correct set from incoming data
                return self.set_operators[set_node.sub_tokens[1].data](
                         self.parse_set(set_node.sub_tokens[0],parenth),
                         self.parse_set(set_node.sub_tokens[2],parenth)
                         )


    #handles parsing out arithmatic statements
    def parse_arithmatic(self,arithmatic : GrammerNode,parenth = [])->float | Matrix:
        if len(arithmatic.sub_tokens) == 3:
            if arithmatic.sub_tokens[1].token.name == "arithmatic_operator":
                if self.do_compile:

                    self.parse_arithmatic(arithmatic.sub_tokens[0],parenth)
                    self.stream_out(arithmatic.sub_tokens[1].data,end="")
                    self.parse_arithmatic(arithmatic.sub_tokens[2],parenth)
                else:
                    return self.arithmatic_operators[arithmatic.sub_tokens[1].data](
                                self.parse_arithmatic(arithmatic.sub_tokens[0],parenth),
                                self.parse_arithmatic(arithmatic.sub_tokens[2],parenth)
                            )

            elif arithmatic.sub_tokens[1].token.name == "set_compressor":
                if self.do_compile:
                    self.stream_out(f"context.set_compressors['{arithmatic.sub_tokens[1].data}'](",
                            end="")
                    self.parse_arithmatic(arithmatic.sub_tokens[0],parenth)
                    self.stream_out(",",end="")
                    self.parse_set(arithmatic.sub_tokens[2],parenth)
                    self.stream_out(")",end="")
                else:
                    return self.set_compressors[arithmatic.sub_tokens[1].data](
                                self.parse_arithmatic(arithmatic.sub_tokens[0],parenth),
                                self.parse_set(arithmatic.sub_tokens[2],parenth)
                            )
            elif arithmatic.sub_tokens[1].token.name == "matrix_function_operator":
                m = None
                
                if arithmatic.sub_tokens[0].token.name == "variable": #check to see if we are storing a variable
                    m = self.variable_map[arithmatic.sub_tokens[0].data]
                else:
                    m = self.parse_matrix(arithmatic.sub_tokens[0])

                try:
                    return getattr(m,arithmatic.sub_tokens[2].data)()
                except:
                    raise ParseError("invalid matrix operation")
        elif len(arithmatic.sub_tokens) == 2:
            if self.do_compile:
                self.stream_out(f"context.unary_set_compressors['{arithmatic.sub_tokens[0].data}'](",
                      end="")
                self.parse_set(arithmatic.sub_tokens[1],parenth)
                self.stream_out(f")",end="")
            else:
                return self.unary_set_compressors[arithmatic.sub_tokens[0].data](
                        self.parse_set(arithmatic.sub_tokens[1],parenth)
                    )
        elif arithmatic.sub_tokens[0].token.name == "number":
            if self.do_compile:
                self.stream_out(arithmatic.data,end="")
            else:
                return float(arithmatic.data)
        elif arithmatic.sub_tokens[0].token.name == "variable":
            if not (arithmatic.data in self.variable_map):
                self.stream_out(f"\nerror reading unset variable :: {arithmatic.data}")
                raise ParseError()
            if self.do_compile:
                self.stream_out(arithmatic.data,end="")
            else:
                if not (arithmatic.data in self.variable_map):
                    self.stream_out(f"\nerror reading unset variable :: {arithmatic.data}")
                    raise ParseError()
                return self.variable_map[arithmatic.data]
        elif arithmatic.sub_tokens[0].token.name == "matrix":
            return self.parse_matrix(arithmatic.sub_tokens[0],parenth)
        else:
            
            inner_parenth = parenth[int(arithmatic.data.split("_")[2][1:])]
            inner_parenth,iner_para =  hide_parenthasis(inner_parenth)
            if self.do_compile:
                self.stream_out("(",end="")
                self.parse_arithmatic(
                                          self.maps["arithmatic"].match(inner_parenth),
                                          iner_para
                                      )
                self.stream_out(")",end="")
            else:
                return self.parse_arithmatic(
                                          self.maps["arithmatic"].match(inner_parenth),
                                          iner_para
                                      )

    def break_delimiter_print(self,just_broke_delimiter : str)->None:
        if len(self.statement_stream.flow_stack) < 1:
            return
        previous_delimiter = self.statement_stream.flow_stack[-1][-2][0]
        if previous_delimiter != just_broke_delimiter:
            self.stream_out(end=previous_delimiter)

    def compile_statement(self,idx,statement,entry_map):
        statement, parenth = hide_parenthasis(statement)
        #print("reading " + statement)
        g = entry_map.match(statement.strip() + ";")
        if g == None:
            self.stream_out(f"error on statement {idx} :: {statement}")
            raise ParseError()
        else:
            #print(g.get_summary())
            self.parse_statement(g,parenth)

    def compile_langauge(self,statement_stream : ControlFlowIterator,**kwargs)->str:

        self.out_buffer = ""

        if self.do_compile:
            with open(get_prelude_path(),'r') as f:
                for line in f:
                    self.stream_out(line)


        self.statement_stream = statement_stream
        self.statement_stream.break_callback = self.break_delimiter_print

        entry_map = self.maps[self.lang.entry_node.name]

        for idx,statement in enumerate(statement_stream):
            self.compile_statement(idx, statement,entry_map)

        #ensure we handle eof as closing each of our while loops properly
        while self.do_compile and self.tab_order > 0:
            self.compile_statement(0, "--", entry_map)
        
        return self.out_buffer
