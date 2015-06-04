""" Layout widgets
"""

from ..pyscript import js
from ..properties import Prop, Instance, Str, Tuple, Float, Int

from .widget import Widget


# todo: rename "zf-" prefix to "xx" or something


class Layout(Widget):
    """ Abstract class for all layout classes.
    """
    
    CSS = """
    
    html {
        /* set height, so body can have height, and the first layout too */
        height: 100%;  
    }
    
    body {
        /* Set height so the first layout can fill whole window */
        height: 100%;
        margin: 0px;
    }
    
    .zf-layout {
        width: 100%;
        height: 100%;
        margin: 0px;
        padding: 0px;
        border-spacing: 0px;
        border: 0px;
    }
    
    """
    
    @js
    def _js_applyBoxStyle(self, e, sty, value):
        for prefix in ['-webkit-', '-ms-', '-moz-', '']:
            e.style[prefix + sty] = value



class Box(Layout):
    """ Abstract class for HBox and VBox
    """
    
    CSS = """
    .zf-hbox, .zf-vbox {
        display: -webkit-flex;
        display: -ms-flexbox;  /* IE 10 */
        display: -ms-flex;     /* IE 11 */
        display: -moz-flex;
        display: flex;
        
        justify-content: stretch;  /* start, end, center, space-between, space-around */
        align-items: stretch;
        align-content: stretch;
    }
    
    */
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    .box-align-center { -webkit-align-items: center; -ms-align-items: center; -moz-align-items: center; align-items: center; }
    */
    
    .zf-hbox > .zf-hbox, .zf-hbox > .zf-vbox {
        width: auto;
    }
    .zf-vbox > .zf-hbox, .zf-vbox > .zf-vbox {
        height: auto;
    }
    """
    
    margin = Float()
    spacing = Float()
    
    @js
    def _js_create_node(self):
        this.node = document.createElement('div')
    
    @js
    def _js_add_child(self, widget):
        self._applyBoxStyle(widget.node, 'flex-grow', widget.flex)
        #if widget.flex > 0:  widget.applyBoxStyle(el, 'flex-basis', 0)
        self._spacing_changed('spacing', self.spacing, self.spacing)
        super()._add_child(widget)
    
    @js
    def _js_remove_child(self, widget):
        self._spacing_changed('spacing', self.spacing, self.spacing)
        super()._remove_child(widget)
    
    @js
    def _js_spacing_changed(self, name, old, spacing):
        if self.children.length:
            self.children[0].node.style['margin-left'] = '0px'
            for child in self.children[1:]:
                child.node.style['margin-left'] = spacing + 'px'
    
    @js
    def _js_margin_changed(self, name, old, margin):
        self.node.style['padding'] = margin + 'px'


class HBox(Box):
    """ Layout widget to align elements horizontally.
    """
    
    CSS = """
    .zf-hbox {
        -webkit-flex-flow: row;
        -ms-flex-flow: row;
        -moz-flex-flow: row;
        flex-flow: row;
        width: 100%;
        /*border: 1px dashed #44e;*/
    }
    """
    
    @js
    def _js_init(self):
        super()._init()
        # align-items: flex-start, flex-end, center, baseline, stretch
        self._applyBoxStyle(self.node, 'align-items', 'center')
        #justify-content: flex-start, flex-end, center, space-between, space-around
        self._applyBoxStyle(self.node, 'justify-content', 'space-around')


class VBox(Box):
    """ Layout widget to align elements vertically.
    """
    
    CSS = """
    .zf-vbox {
        -webkit-flex-flow: column;
        -ms-flex-flow: column;
        -moz-flex-flow: column;
        flex-flow: column;
        height: 100%;
        width: 100%;
        /*border: 1px dashed #e44;*/
    }
    """
    
    @js
    def _js_init(self):
        super()._init()
        self._applyBoxStyle(self.node, 'align-items', 'stretch')
        self._applyBoxStyle(self.node, 'justify-content', 'space-around')


class BaseTableLayout(Layout):
    """ Abstract base class for layouts that use an HTML table.
    """
    
    CSS = """
    
    /* Behave well inside hbox/vbox, 
       we assume no layouts to be nested inside a table layout */
    .zf-hbox > .zf-basetablelayout {
        width: auto;
    }
    .zf-vbox > .zf-basetablelayout {
        height: auto;
    }

    /* In flexed cells, occupy the full space */
    td.vflex > .zf-widget {
        height: 100%;
    }
    td.hflex > .zf-widget {
        width: 100%;
    }
    """
    
    @js
    def _js_apply_table_layout(self):
        table = self.node
        AUTOFLEX = 729  # magic number unlikely to occur in practice
        
        # Get table dimensions
        nrows = len(table.children)
        ncols = 0
        for i in range(len(table.children)):
            row = table.children[i]
            ncols = max(ncols, len(row.children))
        if ncols == 0 and nrows == 0:
            return
        
        # Collect flexes
        vflexes = []
        hflexes = []
        for i in range(nrows):
            row = table.children[i]
            for j in range(ncols):
                col = row.children[j]
                if (col is undefined) or (len(col.children) == 0):
                    continue
                vflexes[i] = max(vflexes[i] or 0, col.children[0].vflex or 0)
                hflexes[j] = max(hflexes[j] or 0, col.children[0].hflex or 0)
        
        # What is the cumulative "flex-value"?
        cum_vflex = vflexes.reduce(lambda pv, cv: pv + cv, 0)
        cum_hflex = hflexes.reduce(lambda pv, cv: pv + cv, 0)
        
        # If no flexes are given; assign each equal
        if (cum_vflex == 0):
            for i in range(len(vflexes)):
                vflexes[i] = AUTOFLEX
            cum_vflex = len(vflexes) * AUTOFLEX
        if (cum_hflex == 0):
            for i in range(len(hflexes)):
                hflexes[i] = AUTOFLEX
            cum_hflex = len(hflexes) * AUTOFLEX
        
        # Assign css class and height/weight to cells
        for i in range(nrows):
            row = table.children[i]
            row.vflex = vflexes[i] or 0  # Store for use during resizing
            for j in range(ncols):
                col = row.children[j];
                if (col is undefined) or (col.children.length is 0):
                    continue
                self._apply_cell_layout(row, col, vflexes[i], hflexes[j], cum_vflex, cum_hflex)
    
    @js
    def _js_apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
        raise NotImplementedError()



class Form(BaseTableLayout):
    """ A form layout organizes pairs of widgets vertically.
    """
    
    CSS = """
    .zf-form > tr > td > .zf-label {
        text-align: right;
    }
    """
    
    @js
    def _js_create_node(self):
        this.node = document.createElement('table')
        this.node.appendChild(document.createElement('tr'))
        # todo: we need to keep track of vertical resizing ...
    
    @js
    def _js_add_child(self, widget):
        # Get row, create if necessary
        row = this.node.children[-1]
        itemsInRow = row.children.length
        if itemsInRow >= 2:
            row = document.createElement('tr')
            self.node.appendChild(row)
        # Create td and add widget to it
        td = document.createElement("td")
        row.appendChild(td)
        td.appendChild(widget.node)
        #
        self._update_layout()
        self._apply_table_layout()
        # do not call super!
    
    @js
    def _js_update_layout(self):
        """ Set hflex and vflex on node.
        """
        i = 0
        for widget in self.children:
            i += 1
            widget.node.hflex = 0 if (i % 2) else 1
            widget.node.vflex = widget.flex
        self._apply_table_layout()
    
    @js
    def _js_remove_child(self, widget):
        pass
        # do not call super!
    
    @js
    def _js_apply_cell_layout(self, row, col, vflex, hflex, cum_vflex, cum_hflex):
        AUTOFLEX = 729
        className = ''
        if (vflex == AUTOFLEX) or (vflex == 0):
            row.style.height = 'auto'
            className += ''
        else:
            row.style.height = vflex * 100 / cum_vflex + '%'
            className += 'vflex'
        className += ' '
        if (hflex == 0):
            col.style.width = 'auto'
            className += ''
        else:
            col.style.width = '100%'
            className += 'hflex'
        col.className = className


class GridLayout(BaseTableLayout):
    """ Not implemented.
    
    Do we even need it? If we do implement it, we need a way to specify
    the vertical flex value.
    """
