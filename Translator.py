from Parser import MyParser
import itertools as it

class Translator:

    def __init__(self, formula):
        self.headerMona = "m2l-str;\n"
        self.alphabet = []
        self.formula_to_be_parsed = formula
        self.formulaType = self.search_mixed_formula()
        self.parsed_formula = ""
        self.translated_formula = ""

    def get_parsed_formula(self):
        return self.parsed_formula

    def get_translated_formula(self):
        return self.translated_formula

    def formula_parser(self):
        if self.formulaType in {1,2,3}:
            self.compute_alphabet()
            parser = MyParser()
            self.parsed_formula = parser(self.formula_to_be_parsed)
        else: raise ValueError('Ooops! You typed a formula with mixed past/future operators')

    def tuple_to_string(self):
        return '_'.join(str(self.formula_to_be_parsed))

    '''
    search_mixed_formula() possible outputs:
    0: formula is mixed
    1: formula is only future
    2: formula is only past
    3: formula is only present
    '''
    def search_mixed_formula(self):
        formula_to_check_str = self.tuple_to_string()
        separated_formula = formula_to_check_str.split('_')

        past_operators = []
        future_operators = []
        for character in separated_formula:
            if character.isupper():
                if character == 'T': continue
                elif character == 'F': continue
                elif character in {'X','E','G','U'}: future_operators.append(character)
                elif character in {'Y','O','H','S'}: past_operators.append(character)
                else: continue
            else: continue

        if not past_operators and future_operators:
            return 1
        elif past_operators and not future_operators:
            return 2
        elif not past_operators and not future_operators:
            return 3
        else: return 0

    def compute_alphabet(self):
        formula_to_check_str = self.tuple_to_string()
        separated_formula = formula_to_check_str.split('_')

        for character in separated_formula:
            if character.islower():
                self.alphabet.append(character.upper())
            else: continue

    def compute_declare_assumption(self):
        pairs = list(it.combinations(self.alphabet, 2))

        first_assumption = "~(ex1 y: 0<=y & y<=max($) & ~("
        for symbol in self.alphabet:
            if symbol == self.alphabet[-1]: first_assumption += 'y in '+ symbol +'))'
            else : first_assumption += 'y in '+ symbol +' | '

        if pairs:
            second_assumption = "~(ex1 y: 0<=y & y<=max($) & ~("
            for pair in pairs:
                if pair == pairs[-1]: second_assumption += '(y notin '+ pair[0]+' | y notin '+pair[1]+ ')));'
                else: second_assumption += '(y notin '+ pair[0]+' | y notin '+pair[1]+ ') & '

            return first_assumption +' & '+ second_assumption
        else:
            return first_assumption +';'

    def translate(self):
        self.translated_formula = translate_bis(self.parsed_formula, var='v_0')+";\n"

    def buildMonaProgram(self):
        if not self.alphabet and not self.translated_formula:
            raise ValueError
        else:
            return self.headerMona + 'var2 ' + ", ".join(self.alphabet) + ';\n' + self.translated_formula + self.compute_declare_assumption()

    def createMonafile(self):
        program = self.buildMonaProgram()
        try:
            with open('./automa.mona', 'w+') as file:
                file.write(program)
                file.close()
        except IOError:
            print('Problem with the opening of the file!')

def translate_bis(formula_tree, var):
    if type(formula_tree) == tuple:
        #enable this print to see the tree pruning
        # print(self.parsed_formula)
        # print(var)
        if formula_tree[0] == '&':
            # print('computed tree: '+ str(self.parsed_formula))
            if var == 'v_0':
                a = translate_bis(formula_tree[1], '0')
                # a = translate_bis(self.parsed_formula[1], '0')
                b = translate_bis(formula_tree[2], '0')
            else:
                a = translate_bis(formula_tree[1], var)
                b = translate_bis(formula_tree[2], var)
            if a == 'False' or b == 'False':
                return 'False'
            elif a == 'True':
                if b == 'True': return 'True'
            elif b == 'True': return a
            else: return '('+a+' & '+b+')'
        elif formula_tree[0] == '|':
            # print('computed tree: '+ str(self.parsed_formula))
            if var == 'v_0':
                a = translate_bis(formula_tree[1], '0')
                b = translate_bis(formula_tree[2], '0')
            else:
                a = translate_bis(formula_tree[1], var)
                b = translate_bis(formula_tree[2], var)
            if a == 'True' or b == 'True':
                return 'True'
            elif a == 'False':
                if b == 'True': return 'True'
                elif b == 'False': return 'False'
                else: return b
            elif b == 'False': return a
            else: return '('+a+' | '+b+')'
        elif formula_tree[0] == '~':
            # print('computed tree: '+ str(self.parsed_formula))
            if var == 'v_0': a = translate_bis(formula_tree[1], '0')
            else: a = translate_bis(formula_tree[1], var)
            if a == 'True': return 'False'
            elif a == 'False': return 'True'
            else: return '~('+ a +')'
        elif formula_tree[0] == 'X':
            # print('computed tree: '+ str(self.parsed_formula))
            new_var = _next(var)
            a = translate_bis(formula_tree[1],new_var)
            if var == 'v_0':
                return '('+ 'ex1 '+new_var+': '+ new_var +' = 1 '+ '& '+ a +')'
            else:
                return '('+ 'ex1 '+new_var+': '+ new_var +' = '+ var + ' + 1 '+ '& '+ a +')'
        elif formula_tree[0] == 'U':
            # print('computed tree: '+ str(self.parsed_formula))
            new_var = _next(var)
            new_new_var = _next(new_var)
            a = translate_bis(formula_tree[2],new_var)
            b = translate_bis(formula_tree[1],new_new_var)

            if var == 'v_0':
                if b == 'True': return '( '+ 'ex1 '+new_var+': 0 <= '+new_var+' & '+new_var+' <= max($) & '+ a +' )'
                elif a ==  'True': return '( '+ 'ex1 '+new_var+': 0 <= '+new_var+' & '+new_var+' <= max($) & forall1 '+new_new_var+': '+var+' <= '+new_new_var+' & '+new_new_var+' < '+new_var+' => '+b+' )'
                elif a == 'False': return 'False'
                else: return '( '+ 'ex1 '+new_var+': 0 <= '+new_var+' & '+new_var+' <= max($) & '+ a +' & forall1 '+new_new_var+': '+var+' <= '+new_new_var+' & '+new_new_var+' < '+new_var+' => '+b+' )'
            else:
                if b == 'True': return '( '+ 'ex1 '+new_var+': '+var+' <= '+new_var+' & '+new_var+' <= max($) & '+ a +' )'
                elif a ==  'True': return '( '+ 'ex1 '+new_var+': '+var+' <= '+new_var+' & '+new_var+' <= max($) & forall1 '+new_new_var+': '+var+' <= '+new_new_var+' & '+new_new_var+' < '+new_var+' => '+b+' )'
                elif a == 'False': return 'False'
                else: return '( '+ 'ex1 '+new_var+': '+var+' <= '+new_var+' & '+new_var+' <= max($) & '+ a +' & forall1 '+new_new_var+': '+var+' <= '+new_new_var+' & '+new_new_var+' < '+new_var+' => '+b+' )'
        elif formula_tree[0] == 'Y':
            # print('computed tree: '+ str(self.parsed_formula))
            new_var = _next(var)
            a = translate_bis(formula_tree[1],new_var)
            if var == 'v_0':
                return '('+ 'ex1 '+new_var+': '+ new_var +' = max($) - 1 '+ '& '+new_var+' > 0 & '+ a +')'
            else:
                return '('+ 'ex1 '+new_var+': '+ new_var +' = '+ var + ' - 1 '+ '& '+new_var+' > 0 & '+ a +')'
        elif formula_tree[0] == 'S':
            # print('computed tree: '+ str(self.parsed_formula))
            new_var = _next(var)
            new_new_var = _next(new_var)
            a = translate_bis(formula_tree[2],new_var)
            b = translate_bis(formula_tree[1],new_new_var)

            if var == 'v_0':
                if b == 'True': return '( '+ 'ex1 '+new_var+': 0 <= '+new_var+' & '+new_var+' <= max($) & '+ a +' )'
                elif a ==  'True': return '( '+ 'ex1 '+new_var+': 0 <= '+new_var+' & '+new_var+' <= max($) & forall1 '+new_new_var+': '+new_var+' < '+new_new_var+' & '+new_new_var+' <= max($) => '+b+' )'
                elif a == 'False': return 'False'
                else: return '( '+ 'ex1 '+new_var+': 0 <= '+new_var+' & '+new_var+' <= max($) & '+ a +' & forall1 '+new_new_var+': '+new_var+' < '+new_new_var+' & '+new_new_var+' <= max($) => '+b+' )'
            else:
                if b == 'True': return '( '+ 'ex1 '+new_var+': 0 <= '+new_var+' & '+new_var+' <= max($) & '+ a +' )'
                elif a ==  'True': return '( '+ 'ex1 '+new_var+': 0 <= '+new_var+' & '+new_var+' <= '+var+' & forall1 '+new_new_var+': '+new_var+' < '+new_new_var+' & '+new_new_var+' <= '+var+' => '+b+' )'
                elif a == 'False': return 'False'
                else: return '( '+ 'ex1 '+new_var+': 0 <= '+new_var+' & '+new_var+' <= '+var+' & '+ a +' & forall1 '+new_new_var+': '+new_var+' < '+new_new_var+' & '+new_new_var+' <= '+var+' => '+b+' )'
    else:
        # handling non-tuple cases
        if formula_tree[0] == 'T': return 'True'
        elif formula_tree[0] == 'F': return 'False'

        # enable if you want to see recursion
        # print('computed tree: '+ str(self.parsed_formula))

        # BASE CASE OF RECURSION
        else:
            if formula_tree.isalpha():
                return var + ' in ' + formula_tree.upper()
            else:
                return var + ' in ' + formula_tree

def _next(var):
    if var == '0': return 'v_1'
    else:
        s = var.split('_')
        s[1] = str(int(s[1])+1)
        return '_'.join(s)
