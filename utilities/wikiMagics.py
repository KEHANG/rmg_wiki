from IPython import display
from IPython.core.magic import Magics, magics_class, cell_magic
import jinja2

@magics_class
class JinjaMagics(Magics):
    '''Magics class containing the jinja2 magic and state'''
    
    def __init__(self, shell):
        super(JinjaMagics, self).__init__(shell)
        
        # create a jinja2 environment to use for rendering
        # this can be modified for desired effects (ie: using different variable syntax)        

        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader('.'))
        
        # possible output types
        self.display_functions = dict(html=display.HTML, 
                                      latex=display.Latex,
                                      json=display.JSON,
                                      pretty=display.Pretty,
                                      display=display.display)

    
    @cell_magic
    def jinja(self, line, cell):
        '''
        jinja2 cell magic function.  Contents of cell are rendered by jinja2, and 
        the line can be used to specify output type.

        ie: "%%jinja html" will return the rendered cell wrapped in an HTML object.
        '''
        f = self.display_functions.get(line.lower().strip(), display.display)

        tmp = self.env.get_template(cell)
        rend = tmp.render(dict((k,v) for (k,v) in self.shell.user_ns.items() 
                                        if not k.startswith('_') and k not in self.shell.user_ns_hidden))
        
        return f(rend)
