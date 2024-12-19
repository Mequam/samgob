#this is an iterator with controls on it that will get the next word/section based
#on some control flow triggers that can be called on it
class ControlFlowIterator:
    def __init__(self,iter_wrapper):
        #the wraper that we are "flowing" around
        self.incoming_stream = iter_wrapper

        #the stack of loops that we are currently in
        self.flow_stack = []
        #we only store statements in memory that we need
        #all other statments are discarded
        self.statement_memory = []
        #the current statement that we are working with
        self.statement_idx = -1
        #determines if we are currently in a while loop
        self.while_flag = False
        #flag indicating we finish a loop
        self.eos_loop_end = "--"

        #function called when we break out of a loop or if statment, this is set elsewhere so for now
        #we default it to doing nothing
        self.break_callback = lambda x : x

    #adds a for loop to the flow stack
    def add_for(self,amount : int,*data)->None:
        self.flow_stack.append(['f',amount,data,self.statement_idx])
    
    def add_if(self,is_true : bool,*args)->None:
        self.flow_stack.append(['i',args,is_true])
    
    def add_while(self,is_true : bool,stmt : str,*args)->None:
        if self.while_flag:
            #we might need to pop the while loop
            if is_true:
                self.while_flag = False
                return

            self.break_loop()
            if len(self.statement_memory) !=0:
                self.add_if(False,"i") #we ignore while loops that are false
                self.while_flag = False
        else:
            #add a while loop like normal
            if not is_true:
                self.add_if(False,"i")
            else:
                if not self.in_loop():
                #    n = next(self)
                    self.statement_memory.append(stmt)
                    self.statement_idx += 1
                #    self.statement_memory.append(n)
                self.flow_stack.append(['w',args,self.statement_idx])
    def set_else(self, if_is_true : bool,*args)->None:
        if self.flow_stack[-1][0] == 'i':
            self.flow_stack.pop()
            self.flow_stack.append(['e',args,if_is_true])

    def __iter__(self):
        return self
    
    def in_loop(self)->bool:
        for entry in self.flow_stack:
            if entry[0] in ['f','w']:
                return True
        return False

    def in_if(self,state : bool)->bool:
        for entry in self.flow_stack:
            if entry[0] in ['i']:
                return entry[-1] == state
        return False

    def in_else(self,state : bool)->bool:
        for entry in self.flow_stack:
            if entry[0] in ['e']:
                return entry[-1] == state
        return False
    def loop_loop(self)->None:
        flow = self.flow_stack[-1]
        self.statement_idx = flow[-1]-1

    def pop(self)->None:
        p = self.flow_stack.pop()
        self.break_callback(*p[-2])

    def break_loop(self)->None:
        self.pop()
        if not self.in_loop():
            self.statement_idx = -1
            self.statement_memory = []

    def pop_loop(self)->str:
        flow = self.flow_stack[-1]
        if flow[0] == 'f': #for loop
            flow[1] -= 1
            if flow[1] <= 0:
                self.break_loop()
                #return next(self)
            else:
                self.loop_loop()
                self.statement_idx += 1
                return self.statement_memory[self.statement_idx]
        if flow[0] == 'i' or flow[0] == 'e':
            self.pop()
            return
        if flow[0] == 'w':
            self.while_flag = True
            self.loop_loop()



    def __next__(self):
        if not self.in_loop(): return next(self.incoming_stream)
        
        if self.statement_idx >= len(self.statement_memory)-1:
            try:
                w = next(self.incoming_stream)
                self.statement_idx += 1
                self.statement_memory.append(w)
                return w
            except StopIteration:
                if self.in_loop():
                    return self.eos_loop_end
                else:
                    raise StopIteration
        
        self.statement_idx += 1
        return self.statement_memory[self.statement_idx]

"""
very simple control flow iterator that ignores all control flow and passes
the next token into the stream, for compiling instead of interpreting
"""
class IgnoreControlIterator(ControlFlowIterator):
    def add_for(self, amount,*args):
        pass
    def add_if(self, is_true,*args):
        pass
    def add_while(self, is_true, stmt,*args):
        pass
    def __next__(self):
        return next(self.incoming_stream)
